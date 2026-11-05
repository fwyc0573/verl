# Copyright 2026 Individual Contributor.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Join the allocated RJob replicas and run one native verl OPD stage.

This entrypoint uses the existing interpreter, mounted inputs and native Ray.
It neither installs dependencies nor submits/stops RJobs. Platform NCCL values
are preserved. Auxiliary receipts do not interrupt healthy native training.
"""

import argparse
import csv
import ipaddress
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from threading import Thread

from tests.manual.agent_opd.runtime_probe import cloud_path, weight_inventory


def write_json(path, value):
    """Publish complete rendezvous records across the mounted local NFS."""
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + "-", suffix=".pending", dir=path.parent)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def failed_peer(directory, nodes):
    for rank in range(nodes):
        path = directory / f"rank-{rank}-result.json"
        if path.is_file():
            result = json.loads(path.read_text())
            if result["status"] == "failed":
                return result
    return None


def wait_json(path, deadline, directory, nodes):
    while time.monotonic() < deadline:
        failure = failed_peer(directory, nodes)
        if failure:
            raise RuntimeError(f"Replica {failure['rank']} failed: {failure.get('error', 'unknown reason')}")
        if path.is_file():
            return json.loads(path.read_text())
        time.sleep(1)
    raise TimeoutError(f"RJob rendezvous timed out waiting for {path.name}")


def worker_environment(local, seed):
    for key, name in {
        "TMPDIR": "tmp", "TORCH_EXTENSIONS_DIR": "torch-extensions",
        "TORCHINDUCTOR_CACHE_DIR": "inductor", "TRITON_CACHE_DIR": "triton",
        "FLASHINFER_WORKSPACE_BASE": "flashinfer", "XDG_CACHE_HOME": "cache",
        "CUDA_CACHE_PATH": "cuda", "HF_HOME": "huggingface",
    }.items():
        path = local / name
        path.mkdir()
        os.environ[key] = str(path)
    os.environ["RAY_TMPDIR"] = str(local / "ray")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["CUDA_DEVICE_MAX_CONNECTIONS"] = "1"
    os.environ["NVTE_ALLOW_NONDETERMINISTIC_ALGO"] = "0"
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(key, None)
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = "*"


def gpu_inventory(args):
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,uuid,memory.total,driver_version", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=args.startup_timeout,
    )
    rows = [dict(zip(("index", "name", "uuid", "memory_mib", "driver"), map(str.strip, row)))
            for row in csv.reader(result.stdout.splitlines()) if row]
    if len(rows) != args.gpus_per_node or any(args.gpu_type not in row["name"] for row in rows):
        raise ValueError(f"Allocated GPU inventory differs from requested {args.gpus_per_node} {args.gpu_type}")
    return rows


def start_ray(rank, ip, directory, local, args):
    command = [
        sys.executable, "-m", "ray.scripts.scripts", "start", "--node-ip-address", ip,
        "--num-gpus", str(args.gpus_per_node), "--disable-usage-stats",
        # Bind worker ports at allocation time; do not probe and reuse an
        # unreserved port that can become an outgoing connection in the gap.
        "--min-worker-port", "0", "--max-worker-port", "0",
    ]
    if rank == 0:
        head = {"ip": ip, "port": int(os.environ["PORT_AUTO0"]), "dashboard_port": int(os.environ["PORT_AUTO1"])}
        command += [
            "--head", "--port", str(head["port"]), "--dashboard-host", "0.0.0.0",
            "--dashboard-port", str(head["dashboard_port"]), "--temp-dir", str(local / "ray"),
        ]
    else:
        head = wait_json(directory / "head.json", time.monotonic() + args.startup_timeout, directory, args.nodes)
        command += ["--address", f"{head['ip']}:{head['port']}"]
    with (local / "ray-start.log").open("x") as stream:
        subprocess.run(command, check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=args.startup_timeout)
    if rank == 0:
        write_json(directory / "head.json", head)
    return head


def check_cluster(head, directory, args):
    import ray

    ray.init(address=f"{head['ip']}:{head['port']}", log_to_driver=False)
    try:
        deadline = time.monotonic() + args.startup_timeout
        while time.monotonic() < deadline:
            failure = failed_peer(directory, args.nodes)
            if failure:
                raise RuntimeError(f"Replica {failure['rank']} failed before cluster registration")
            nodes = [node for node in ray.nodes() if node["Alive"]]
            if len(nodes) > args.nodes:
                raise ValueError("The Ray cluster contains more nodes than this RJob allocated")
            if len(nodes) == args.nodes and all(
                node["Resources"].get("GPU", 0) == args.gpus_per_node for node in nodes
            ):
                registered = {node["NodeManagerAddress"] for node in nodes}
                expected = {
                    json.loads((directory / f"rank-{rank}-runtime.json").read_text())["ip"]
                    for rank in range(args.nodes)
                }
                if len(registered) != args.nodes or registered != expected:
                    raise ValueError("Registered Ray node addresses do not match this RJob's replica receipts")
                record = {"nodes": [
                    {
                        "ip": node["NodeManagerAddress"], "gpus": node["Resources"].get("GPU", 0),
                        "node_id": node["NodeID"],
                    }
                    for node in nodes
                ]}
                write_json(directory / "cluster.json", record)
                return record
            time.sleep(1)
        raise TimeoutError("Ray did not register the exact requested node and GPU allocation")
    finally:
        ray.shutdown()


def prepare_recipe(args, pair, settings, directory, cloud, head, job):
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf, open_dict

    from tests.manual.agent_opd.configure import recipe_overrides, validate_assets

    settings = dict(
        settings, save_directory=str(cloud / "checkpoints"), experiment_name=f"{args.pair}-{args.steps}-{job}",
    )
    settings_file, agent_file, recipe_file = (
        directory / name for name in ("settings.json", "agent.yaml", "recipe.yaml")
    )
    write_json(settings_file, settings)
    agent = [{
        "name": "prepared_turn_agent", "_target_": "tests.manual.agent_opd.agent_loop.PreparedTurnAgentLoop",
        "reasoning_parser": pair["reasoning_parser"], "tool_parser": pair["loop_tool_parser"],
        "ratio_bounds": settings["importance_ratio_bounds"], "numerical_limits": settings.get("numerical_limits"),
    }]
    with agent_file.open("x") as stream:
        stream.write(OmegaConf.to_yaml(OmegaConf.create(agent)))
    validate_assets(argparse.Namespace(dataset=args.dataset, agent_config=agent_file, steps=args.steps), pair, settings)
    repository = Path(__file__).resolve().parents[3]
    overrides = recipe_overrides(
        pair, settings, dataset=args.dataset, agent_config=agent_file, steps=args.steps, repository=repository,
    )
    with initialize_config_dir(version_base=None, config_dir=str(repository / "verl/trainer/config")):
        config = compose(config_name="ppo_trainer", overrides=overrides)
    with open_dict(config.ray_kwargs.ray_init):
        config.ray_kwargs.ray_init.address = f"{head['ip']}:{head['port']}"
    with recipe_file.open("x") as stream:
        stream.write(OmegaConf.to_yaml(config, resolve=False))
    for file in (settings_file, agent_file, recipe_file):
        shutil.copy2(file, cloud / file.name)
    return recipe_file


def stop_training(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=30)


def run_training(recipe, cloud, directory, local, args):
    command = [
        sys.executable, "-B", "-m", "tests.manual.agent_opd.train", "--config", str(recipe),
        "--observations", str(cloud / "observations"),
    ]
    child = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True,
    )

    def record_output():
        try:
            stream = (local / "training.log").open("x")
        except OSError as error:
            print(f"VERL_STAGE_LOG_UNVERIFIED {type(error).__name__}", flush=True)
            stream = None
        try:
            for line in child.stdout:
                print(line, end="", flush=True)
                if stream is not None:
                    try:
                        stream.write(line)
                        stream.flush()
                    except OSError as error:
                        print(f"VERL_STAGE_LOG_UNVERIFIED {type(error).__name__}", flush=True)
                        stream.close()
                        stream = None
        finally:
            if stream is not None:
                stream.close()

    observer = Thread(target=record_output, daemon=True)
    observer.start()
    try:
        deadline = time.monotonic() + args.training_timeout
        while child.poll() is None:
            failure = failed_peer(directory, args.nodes)
            if failure:
                raise RuntimeError(f"Native peer replica {failure['rank']} failed")
            if time.monotonic() >= deadline:
                raise TimeoutError("The native training subprocess exceeded the requested training timeout")
            time.sleep(1)
        if child.returncode:
            raise subprocess.CalledProcessError(child.returncode, command)
    finally:
        stop_training(child)
        observer.join(timeout=30)
        child.stdout.close()


def training_receipt(cloud, steps):
    """Inspect completed native evidence without deriving updates from directory names."""
    receipt_path = cloud / "observations/training.json"
    try:
        receipt = json.loads(receipt_path.read_text())
        updates = receipt["completed_updates"]
        export = receipt["final_export"]
        outcomes = receipt["update_outcomes"]
        verified = (
            receipt["native_fit_returned"] is True and receipt["requested_updates"] == steps and updates == steps
            and receipt["actor_update_call_count"] == steps
            and receipt["native_megatron_optimizer_success_contract"]["one_optimizer_step_per_call"] is True
            and len(outcomes) == steps and all(
                item["native_update_returned"] is True and item["optimizer_steps_verified"] == 1
                and item["finite_grad_loss"] is True and item["positive_grad_norm"] is True
                for item in outcomes
            )
            and export is not None and export["completed_updates"] == steps
        )
        result = {
            "status": "PASS_NATIVE_UPDATES_AND_EXPORT" if verified else "UNVERIFIED",
            "training_receipt": str(receipt_path), "completed_updates": updates, "final_export": export,
            "new_process_reload_verified": False, "numerical_agreement_verified": False,
        }
        if verified:
            model_path = cloud_path(export["model_path"])
            if not model_path.resolve().is_relative_to(cloud.resolve()):
                raise ValueError("Final HF export is outside this job's output directory")
            result["hf_inventory"] = weight_inventory(model_path)
            if result["hf_inventory"]["status"] != "PASS":
                result["status"] = "UNVERIFIED"
        return result
    except Exception as error:
        return {
            "status": "UNVERIFIED", "training_receipt": str(receipt_path),
            "error": f"{type(error).__name__}: {error}",
        }


def archive_logs(local, cloud, rank):
    """Archive selected completed logs; cache and active logs stay worker-local."""
    destination = cloud / "logs" / f"rank-{rank}"
    destination.mkdir(parents=True, exist_ok=True)
    files = [local / "ray-start.log", local / "training.log", local / "ray-stop.log"]
    files.extend(local / "ray/session_latest/logs" / name for name in ("raylet.err", "raylet.out", "gcs_server.err"))
    for file in files:
        if file.is_file():
            shutil.copy2(file, destination / file.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", required=True)
    parser.add_argument("--steps", choices=(2, 20), type=int, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--shared-dir", type=Path, required=True)
    parser.add_argument("--local-root", type=Path, default=Path("/var/tmp"))
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--gpus-per-node", type=int, required=True)
    parser.add_argument("--gpu-type", required=True)
    parser.add_argument("--startup-timeout", type=int, required=True)
    parser.add_argument("--training-timeout", type=int, required=True)
    args = parser.parse_args()
    if min(args.nodes, args.gpus_per_node, args.startup_timeout, args.training_timeout) <= 0:
        raise ValueError("Resource counts and stage timeouts must be positive")
    if not args.local_root.is_absolute() or args.local_root.resolve().is_relative_to(Path("/mnt/codesign-exp")):
        raise ValueError("--local-root must be an absolute worker-local temporary directory")
    cloud_path(args.dataset)
    output_root = cloud_path(args.output_root)
    shared = args.shared_dir.resolve()
    if not shared.is_relative_to(Path("/data/ycfeng/tmp")):
        raise ValueError("--shared-dir must use the mounted local /data/ycfeng/tmp directory")
    rank, total = int(os.environ["KUBEBRAIN_REPLICA"]), int(os.environ["KUBEBRAIN_REPLICA_TOTAL"])
    job = os.environ["KUBEBRAIN_RJOB_NAME"]
    if Path(job).name != job or job in (".", ".."):
        raise ValueError("The platform RJob name cannot contain path components")
    pair = json.loads(args.pairs.read_text())[args.pair]
    settings = json.loads(args.settings.read_text())
    if total != args.nodes or not 0 <= rank < total:
        raise ValueError("The platform replica allocation differs from the requested stage")
    runtime = pair["runtime"]
    if args.nodes * args.gpus_per_node != runtime["actor_gpus"] + runtime["teacher_gpus"]:
        raise ValueError("The allocated GPU count differs from the selected native actor and teacher pools")
    directory, cloud = shared / job, output_root / job
    directory.mkdir(parents=True, exist_ok=True)
    # Ray's Unix socket paths include a long session suffix. Keep their
    # worker-local prefix short, independently of the platform job name.
    local = Path(tempfile.mkdtemp(prefix="vo-", dir=args.local_root))
    nccl = {key: value for key, value in os.environ.items() if key.startswith("NCCL_")}
    worker_environment(local, settings["seed"])
    if nccl != {key: value for key, value in os.environ.items() if key.startswith("NCCL_")}:
        raise RuntimeError("Worker setup changed platform NCCL environment values")
    result = {"status": "failed", "job": job, "rank": rank, "pair": args.pair, "requested_updates": args.steps}
    ray_started = False

    def interrupted(signum, frame):
        raise InterruptedError(f"Worker received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    try:
        import torch
        import verl

        ip = socket.gethostbyname(socket.gethostname())
        if ipaddress.ip_address(ip).is_loopback:
            raise ValueError("The native node hostname resolves to an unreachable loopback address")
        runtime_receipt = {
            "job": job, "rank": rank, "total": total, "hostname": socket.gethostname(), "ip": ip,
            "python": sys.executable, "python_version": sys.version,
            "torch": {"version": torch.__version__, "cuda": torch.version.cuda, "source": torch.__file__},
            "verl_source": verl.__file__, "gpus": gpu_inventory(args), "preserved_nccl_keys": sorted(nccl),
        }
        write_json(directory / f"rank-{rank}-runtime.json", runtime_receipt)
        print("VERL_STAGE_GPU_RECEIPT " + json.dumps(runtime_receipt), flush=True)
        head = start_ray(rank, ip, directory, local, args)
        ray_started = True
        if rank == 0:
            cloud.mkdir(parents=True, exist_ok=False)
            cluster = check_cluster(head, directory, args)
            write_json(cloud / "cluster.json", cluster)
            recipe = prepare_recipe(args, pair, settings, directory, cloud, head, job)
            run_training(recipe, cloud, directory, local, args)
            result.update(
                status="native_succeeded", evidence=training_receipt(cloud, args.steps), workflow_accepted=False,
            )
            write_json(directory / "finished.json", result)
        else:
            terminal = wait_json(
                directory / "finished.json", time.monotonic() + args.startup_timeout + args.training_timeout,
                directory, args.nodes,
            )
            if terminal["status"] != "native_succeeded":
                raise RuntimeError("The head replica failed the native stage")
            result.update(status="native_succeeded", workflow_accepted=False)
    except BaseException as error:
        result["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        try:
            write_json(directory / f"rank-{rank}-result.json", result)
            if result["status"] == "failed":
                write_json(directory / "finished.json", result)
        except Exception as error:
            print(f"VERL_STAGE_RENDEZVOUS_UNVERIFIED {type(error).__name__}: {error}", flush=True)
        ray_stopped = not ray_started
        if ray_started:
            try:
                with (local / "ray-stop.log").open("x") as stream:
                    stopped = subprocess.run(
                        [sys.executable, "-m", "ray.scripts.scripts", "stop", "--force"],
                        stdout=stream, stderr=subprocess.STDOUT, timeout=60, check=False,
                    )
                    ray_stopped = stopped.returncode == 0
            except Exception as error:
                print(f"VERL_STAGE_RAY_STOP_UNVERIFIED {type(error).__name__}", flush=True)
        try:
            cloud.mkdir(parents=True, exist_ok=True)
            write_json(cloud / f"rank-{rank}-result.json", result)
            archive_logs(local, cloud, rank)
            if ray_stopped:
                shutil.rmtree(local)
        except Exception as error:
            print(f"VERL_STAGE_ARCHIVE_UNVERIFIED {type(error).__name__}: {error}", flush=True)
        print("VERL_STAGE_RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
