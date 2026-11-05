"""Run the frozen Miles SWE benchmark through its native agent and grader.

Only the endpoint configuration and scheduling belong to this adapter. Miles
owns question preparation, native outcome/seed receipts and paired scoring.
Run this entrypoint on the authorized worker, with its native SWE environment.
"""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event


PRESERVED_STATUSES = frozenset(("reserved", "running", "interrupted_pending_audit"))


def cloud_path(value):
    path = Path(value).resolve()
    path.relative_to("/mnt/codesign-exp/ycfeng")
    return path


def load_miles(root, name):
    path = Path(root).resolve() / "tests/manual/agent_opd" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"miles_opd_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=path.name + ".", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(json.dumps(value, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def freeze_identity(path, identity):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            if json.loads(path.read_text()) != identity:
                raise ValueError("A resumed benchmark cannot change its model, population or inference contract")
        else:
            write_json(path, identity)


def membership(path, expected_sha256):
    raw = cloud_path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("The benchmark membership differs from the independently frozen digest")
    record = json.loads(raw)
    if len(record["task_ids"]) != 20 or len(set(record["task_ids"])) != 20:
        raise ValueError("The frozen benchmark must contain twenty distinct questions")
    if record["seeds"] != [1729, 1730, 1731, 1732]:
        raise ValueError("The frozen benchmark seeds differ from the source contract")
    if (record["sampling"]["temperature"], record["sampling"]["top_p"]) != (1.0, 0.95):
        raise ValueError("The frozen benchmark sampling differs from the source contract")
    dataset = cloud_path(record["dataset"])
    dataset_raw = dataset.read_bytes()
    if hashlib.sha256(dataset_raw).hexdigest() != record["dataset_sha256"]:
        raise ValueError("The frozen benchmark dataset changed")
    if [row["instance_id"] for row in json.loads(dataset_raw)] != record["task_ids"]:
        raise ValueError("The frozen benchmark ordered question identities changed")
    return record, digest


def credentials():
    present = {
        key: bool(os.environ.get(key))
        for key in ("AK_BASEMIND", "SK_BASEMIND", "SR_USER_TOKEN", "SESSION_ROUTER_USER_TOKEN")
    }
    return {
        "present": present,
        "ready": present["AK_BASEMIND"]
        and present["SK_BASEMIND"]
        and (present["SR_USER_TOKEN"] or present["SESSION_ROUTER_USER_TOKEN"]),
    }


def pair_config(args):
    pair = json.loads(args.pairs.read_text())[args.pair]
    benchmark = pair["benchmark"]
    if benchmark["context_tokens"] < 1 or not isinstance(benchmark["chat_template_kwargs"], dict):
        raise ValueError("Invalid benchmark context or template configuration")
    if not all(isinstance(value, str) for value in benchmark["server_args"]):
        raise ValueError("Benchmark server_args must be a list of strings")
    return pair


def model_inventory(path):
    """Validate the complete HF tensor inventory without loading large tensors."""
    from safetensors import safe_open

    path = cloud_path(path)
    config_raw = cloud_path(path / "config.json").read_bytes()
    index = cloud_path(path / "model.safetensors.index.json")
    mapping = json.loads(index.read_text())["weight_map"] if index.exists() else None
    files = sorted(set(mapping.values())) if mapping is not None else ["model.safetensors"]
    actual = {}
    inventory = []
    for name in files:
        shard = cloud_path(path / name)
        if shard.parent != path:
            raise ValueError("HF tensor shards must be directly inside the model directory")
        with safe_open(shard, framework="np") as tensors:
            for key in tensors.keys():
                if key in actual:
                    raise ValueError("Duplicate HF tensor inventory")
                actual[key] = name
        stat = shard.stat()
        inventory.append({"name": name, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    if not actual or (mapping is not None and actual != mapping):
        raise ValueError("HF safetensors inventory differs from the published index")
    return {
        "model_path": str(path),
        "model_type": json.loads(config_raw)["model_type"],
        "config_sha256": hashlib.sha256(config_raw).hexdigest(),
        "tensor_count": len(actual),
        "shards": inventory,
    }


def model_identity(args, pair):
    path = cloud_path(args.model_path)
    original = cloud_path(pair["student"])
    if args.version == 0 and path != original:
        raise ValueError("The original benchmark must load the pinned student path")
    receipt_identity = None
    if args.version == 20:
        if path == original or args.export_receipt is None:
            raise ValueError("The updated benchmark requires its HF export and successful-update receipt")
        receipt_path = cloud_path(args.export_receipt)
        receipt_raw = receipt_path.read_bytes()
        receipt = json.loads(receipt_raw)
        if receipt["completed_updates"] != 20 or cloud_path(receipt["model_path"]) != path:
            raise ValueError("The export receipt does not identify this successful update-20 model")
        receipt_identity = {
            "path": str(receipt_path), "sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "completed_updates": 20, "model_path": str(path),
        }
    result = model_inventory(path)
    original_type = json.loads(cloud_path(original / "config.json").read_text())["model_type"]
    if result["model_type"] != original_type:
        raise ValueError("The exported HF architecture differs from the pinned student")
    result["export_receipt"] = receipt_identity
    return result


def served_model(args):
    return f"verl-agent-opd-{args.pair}-step{args.version}"


def server_argv(args):
    pair = pair_config(args)
    bank, _ = membership(args.membership, args.membership_sha256)
    model_identity(args, pair)
    if not credentials()["ready"]:
        raise RuntimeError("Native sandbox credentials are incomplete; use credentials for presence-only status")
    from transformers import AutoTokenizer

    student = cloud_path(pair["student"])
    for asset in student.rglob("*"):
        cloud_path(asset)
        if asset.is_symlink() and asset.is_dir():
            raise ValueError("Tokenizers require ordinary asset directories, without directory symlinks")
    tokenizer = AutoTokenizer.from_pretrained(student, local_files_only=True)
    template = tokenizer.get_chat_template()
    kwargs = pair["benchmark"]["chat_template_kwargs"]
    if any(key not in template for key in kwargs):
        raise ValueError("The pinned student chat template does not support its benchmark kwargs")
    tokenizer.apply_chat_template(
        [{"role": "user", "content": "Check the native benchmark template."}],
        tokenize=True,
        add_generation_prompt=True,
        **kwargs,
    )
    command = [
        sys.executable, "-m", "sglang.launch_server",
        "--model-path", str(cloud_path(args.model_path)),
        "--tokenizer-path", str(cloud_path(pair["student"])),
        "--served-model-name", served_model(args),
        "--weight-version", str(args.version),
        "--host", "127.0.0.1", "--port", str(args.port),
        "--tp-size", str(args.tp_size), "--dtype", "bfloat16", "--load-format", "safetensors",
        "--context-length", str(pair["benchmark"]["context_tokens"]),
        "--mem-fraction-static", str(args.memory_fraction),
        "--chunked-prefill-size", str(args.prefill_tokens), "--max-running-requests", str(len(bank["seeds"])),
        "--disable-cuda-graph", "--enable-deterministic-inference",
        "--reasoning-parser", pair["reasoning_parser"], "--tool-call-parser", pair["tool_parser"],
        "--log-requests", "--log-requests-level", "1", "--log-requests-format", "json",
        *pair["benchmark"]["server_args"],
    ]
    sys.stdout.buffer.write(b"\0".join(value.encode() for value in command) + b"\0")


def wait_server(args):
    deadline = time.monotonic() + args.server_timeout
    while time.monotonic() < deadline:
        os.kill(args.server_pid, 0)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/model_info", timeout=5) as response:
                info = json.load(response)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2)
            continue
        if cloud_path(info["model_path"]) != cloud_path(args.model_path):
            raise ValueError("The reloaded endpoint model path differs from the benchmark identity")
        if str(info["weight_version"]) != str(args.version):
            raise ValueError("The reloaded endpoint weight version differs from the benchmark identity")
        return {"model_path": info["model_path"], "weight_version": info["weight_version"]}
    raise TimeoutError("The native SGLang benchmark endpoint did not become ready")


def native(args):
    """Keep the source native adapter unchanged; replace only endpoint config."""
    import toml

    membership(args.membership, args.membership_sha256)
    source = load_miles(args.miles_root, "native_benchmark")
    benchmark = pair_config(args)["benchmark"]
    base = source.RunCheckPipeline

    class PairPipeline(base):
        def __init__(self, eval_config_path, work_dir):
            config = toml.loads(eval_config_path.read_text())
            config["model"]["max_context_tokens"] = benchmark["context_tokens"]
            config["model"]["inference_args"]["chat_template_kwargs"] = benchmark["chat_template_kwargs"]
            eval_config_path.write_text(toml.dumps(config))
            super().__init__(eval_config_path=eval_config_path, work_dir=work_dir)

    source.RunCheckPipeline = PairPipeline
    sys.argv = [
        str(Path(source.__file__)), "--membership", str(args.membership),
        "--url", f"http://127.0.0.1:{args.port}", "--model", served_model(args),
        "--version", str(args.version), "--seed", str(args.seed), "--task-index", str(args.task_index),
        "--sandbox-backend", args.sandbox_backend, "--output", str(args.output),
        "--server-log", str(args.server_log),
    ]
    source.main()


def attempt_roots(output, version):
    return sorted((output / f"step{version}" / "attempts").glob("*/attempt-*"))


def execute_native(command, environment, log, timeout, on_start, stop):
    process = subprocess.Popen(
        command, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
    )
    try:
        on_start(process.pid)
        deadline = time.monotonic() + timeout
        while True:
            if stop.is_set():
                raise InterruptedError("The benchmark owner interrupted the native attempt")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"status": "timeout"}
            try:
                return {"status": "returned", "returncode": process.wait(timeout=min(1, remaining))}
            except subprocess.TimeoutExpired:
                continue
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run(args):
    pair = pair_config(args)
    bank, digest = membership(args.membership, args.membership_sha256)
    output = cloud_path(args.output)
    version_root = output / f"step{args.version}"
    identity = {
        "pair": args.pair, "completed_updates": args.version, "membership_sha256": digest,
        "model": model_identity(args, pair), "benchmark": pair["benchmark"],
        "reasoning_parser": pair["reasoning_parser"], "tool_parser": pair["tool_parser"],
        "sandbox_backend": args.sandbox_backend,
    }
    shared_identity = {key: value for key, value in identity.items() if key not in ("model", "completed_updates")}
    shared_identity["student"] = str(cloud_path(pair["student"]))
    freeze_identity(output / "identity.json", shared_identity)
    freeze_identity(version_root / "identity.json", identity)
    if not credentials()["ready"]:
        raise RuntimeError("Native sandbox credentials are incomplete")
    endpoint = wait_server(args)
    source_summary = load_miles(args.miles_root, "summarize_benchmark")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    stop = Event()

    def run_attempt(index, seed):
        if stop.is_set():
            return 0
        task = bank["task_ids"][index]
        group = version_root / "attempts" / f"question-{index:02d}-seed-{seed}"
        group.mkdir(parents=True, exist_ok=True)
        with (group / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            roots = sorted(group.glob("attempt-*"))
            result = source_summary._read_model(roots, {"task_ids": [task], "seeds": [seed]}, args.version)
            if result["valid_attempts"]:
                return 1
            states = [json.loads((root / "state.json").read_text()) for root in roots]
            if any(state["status"] in PRESERVED_STATUSES for state in states):
                print("VERL_BENCHMARK_RUNNING_PRESERVED", args.version, index, seed, flush=True)
                return 0
            attempt = group / f"attempt-{uuid.uuid4().hex}"
            reservation = group / (".reserved-" + attempt.name)
            reservation.mkdir()
            state = {
                "status": "reserved", "task_id": task, "seed": seed, "started": time.time(),
                "owner": {"host": socket.gethostname(), "pid": os.getpid(),
                          "job_name": os.environ.get("RJOB_NAME") or os.environ.get("EXP_ID"),
                          "job_uid": os.environ.get("RJOB_UID")},
            }
            write_json(reservation / "state.json", state)
            reservation.rename(attempt)
        with tempfile.TemporaryDirectory(prefix="native-swe-", dir=args.work_dir) as temporary:
            directory = Path(temporary)
            server_log = directory / "server.log"
            server_log.symlink_to(args.server_log.resolve())
            native_output = attempt / f"step{args.version}" / f"seed-{seed}"
            command = [
                str(args.native_python), "-B", str(Path(__file__).resolve()), "native",
                "--miles-root", str(args.miles_root), "--pairs", str(args.pairs.resolve()),
                "--pair", args.pair, "--membership", str(args.membership),
                "--membership-sha256", args.membership_sha256,
                "--version", str(args.version), "--port", str(args.port),
                "--seed", str(seed), "--task-index", str(index),
                "--sandbox-backend", args.sandbox_backend, "--output", str(native_output),
                "--server-log", str(server_log),
            ]
            environment = dict(os.environ, PYTHONPATH=args.native_pythonpath, PYTHONDONTWRITEBYTECODE="1")

            def started(pid):
                state.update(status="running", child_pid=pid)
                write_json(attempt / "state.json", state)

            try:
                with (directory / "native.log").open("w") as log:
                    state.update(execute_native(command, environment, log, args.attempt_timeout, started, stop))
            except BaseException as error:
                state.update(
                    status="interrupted" if "child_pid" in state else "interrupted_pending_audit",
                    error_type=type(error).__name__,
                )
                raise
            finally:
                # All native writers have exited before archival and temporary cleanup.
                shutil.copy2(directory / "native.log", attempt / "native.log")
                native_work = directory / f"step{args.version}"
                if native_work.exists():
                    shutil.copytree(native_work, attempt / "native")
                state["finished"] = time.time()
                write_json(attempt / "state.json", state)
        result = source_summary._read_model([attempt], {"task_ids": [task], "seeds": [seed]}, args.version)
        print("VERL_BENCHMARK_ATTEMPT_FINISHED", args.version, index, seed, result["valid_attempts"], flush=True)
        return result["valid_attempts"]

    def remaining_questions(seed):
        for index in range(1, len(bank["task_ids"])):
            if stop.is_set():
                return
            run_attempt(index, seed)

    pool = ThreadPoolExecutor(max_workers=len(bank["seeds"]))
    try:
        gate = list(pool.map(lambda seed: run_attempt(0, seed), bank["seeds"]))
        if sum(gate) == len(bank["seeds"]):
            list(pool.map(remaining_questions, bank["seeds"]))
    finally:
        stop.set()
        pool.shutdown(wait=True, cancel_futures=True)
    with (version_root / "report.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = source_summary._read_model(attempt_roots(output, args.version), bank, args.version)
        first = source_summary._read_model(
            attempt_roots(output, args.version),
            {"task_ids": bank["task_ids"][:1], "seeds": bank["seeds"]}, args.version
        )
        result.update(
            status="complete" if result["valid_attempts"] == 80 else "incomplete",
            first_question_four_seed_gate="passed" if first["valid_attempts"] == 4 else "incomplete",
            native_endpoint_reload=endpoint, credentials=credentials(),
            preserved_attempts=[
                {"path": str(root), **json.loads((root / "state.json").read_text())}
                for root in attempt_roots(output, args.version)
                if json.loads((root / "state.json").read_text())["status"] in PRESERVED_STATUSES
            ],
        )
        report = version_root / "report.json"
        if (report.exists() and json.loads(report.read_text())["status"] == "complete"
                and result["status"] != "complete"):
            raise ValueError("Previously complete native outcomes are missing; preserve the completed report for audit")
        write_json(report, result)
    print("VERL_BENCHMARK_VERSION", args.pair, args.version, result["status"], result["valid_attempts"], flush=True)
    return 0 if result["status"] == "complete" else 2


def archive(args):
    target = cloud_path(args.output) / f"step{args.version}" / "engine-logs" / args.server_log.parent.name
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.server_log, target / "server.log")
    args.server_log.unlink()
    (args.work_dir / "server-argv").unlink()
    args.work_dir.rmdir()
    print("VERL_BENCHMARK_ENGINE_LOG_ARCHIVED", str(target), flush=True)


def summarize(args):
    bank, _ = membership(args.membership, args.membership_sha256)
    output = cloud_path(args.output)
    pair = pair_config(args)
    shared = json.loads((output / "identity.json").read_text())
    expected = {
        "pair": args.pair, "membership_sha256": args.membership_sha256, "benchmark": pair["benchmark"],
        "reasoning_parser": pair["reasoning_parser"], "tool_parser": pair["tool_parser"],
        "sandbox_backend": shared["sandbox_backend"], "student": str(cloud_path(pair["student"])),
    }
    if shared != expected:
        raise ValueError("The benchmark comparison identity differs from its model pair contract")
    identities = [json.loads((output / f"step{version}" / "identity.json").read_text()) for version in (0, 20)]
    for identity, version in zip(identities, (0, 20), strict=True):
        if identity["completed_updates"] != version or any(
            identity[key] != shared[key] for key in shared if key != "student"
        ):
            raise ValueError("Original and updated benchmark contracts differ")
    before, after = (identity["model"] for identity in identities)
    receipt = after["export_receipt"]
    if (before["model_path"] != expected["student"] or after["model_path"] == expected["student"]
            or before["model_type"] != after["model_type"] or receipt["completed_updates"] != 20
            or receipt["model_path"] != after["model_path"]):
        raise ValueError("The comparison does not identify this student's original and successful update-20 HF export")
    source = load_miles(args.miles_root, "summarize_benchmark")
    result = source.summarize(
        attempt_roots(output, 0), attempt_roots(output, 20), bank,
        bootstrap_samples=args.bootstrap_samples, bootstrap_seed=args.bootstrap_seed,
    )
    write_json(cloud_path(args.report), result)
    print("VERL_BENCHMARK_COMPARISON", result["status"], flush=True)
    return 0 if result["status"] == "complete" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("credentials")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--miles-root", type=Path, required=True)
    prepare.add_argument("--parent", type=Path, required=True)
    prepare.add_argument("--output-root", type=Path, required=True)
    for name in ("server-argv", "run", "native", "archive"):
        command = commands.add_parser(name)
        command.add_argument("--miles-root", type=Path, required=True)
        command.add_argument("--pairs", type=Path, required=True)
        command.add_argument("--pair", required=True)
        command.add_argument("--membership", type=Path, required=True)
        command.add_argument("--membership-sha256", required=True)
        command.add_argument("--version", type=int, choices=(0, 20), required=True)
        command.add_argument("--port", type=int, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--sandbox-backend", choices=("acs", "basemind"), default="basemind")
        if name == "native":
            command.add_argument("--server-log", type=Path, required=True)
            command.add_argument("--seed", type=int, required=True)
            command.add_argument("--task-index", type=int, required=True)
            continue
        command.add_argument("--model-path", type=Path, required=True)
        command.add_argument("--export-receipt", type=Path)
        command.add_argument("--native-python", type=Path, required=True)
        command.add_argument("--native-pythonpath", required=True)
        command.add_argument("--work-dir", type=Path, required=True)
        command.add_argument("--tp-size", type=int, required=True)
        command.add_argument("--prefill-tokens", type=int, required=True)
        command.add_argument("--memory-fraction", type=float, required=True)
        command.add_argument("--server-timeout", type=int, required=True)
        command.add_argument("--attempt-timeout", type=int, required=True)
        if name in ("run", "archive"):
            command.add_argument("--server-log", type=Path, required=True)
        if name == "run":
            command.add_argument("--server-pid", type=int, required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--miles-root", type=Path, required=True)
    summary.add_argument("--pairs", type=Path, required=True)
    summary.add_argument("--pair", required=True)
    summary.add_argument("--membership", type=Path, required=True)
    summary.add_argument("--membership-sha256", required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--report", type=Path, required=True)
    summary.add_argument("--bootstrap-samples", type=int, default=10000)
    summary.add_argument("--bootstrap-seed", type=int, default=20261105)
    args = parser.parse_args()
    if args.command == "credentials":
        print(json.dumps(credentials()), flush=True)
    elif args.command == "prepare":
        preparer = args.miles_root.resolve() / "tests/manual/agent_opd/prepare_benchmark.py"
        subprocess.run([
            sys.executable, "-B", str(preparer), "--parent", str(args.parent),
            "--output-root", str(cloud_path(args.output_root)),
        ], check=True)
        path = args.output_root / "membership.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        membership(path, digest)
        print("VERL_BENCHMARK_MEMBERSHIP_SHA256", digest, flush=True)
    elif args.command == "server-argv":
        server_argv(args)
    elif args.command == "native":
        native(args)
    elif args.command == "run":
        return run(args)
    elif args.command == "archive":
        archive(args)
    else:
        return summarize(args)
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    sys.exit(main())
