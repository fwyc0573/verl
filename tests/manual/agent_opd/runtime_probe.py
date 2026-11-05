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
"""Inspect the native OPD runtime and exact local HF assets without loading weights.

Run with the intended worker interpreter, for example:
    python -B tests/manual/agent_opd/runtime_probe.py \
        --pairs tests/manual/agent_opd/pairs.json --output /data/ycfeng/tmp/runtime.json

The JSON is a CPU preflight receipt. It does not qualify CUDA execution,
training/inference agreement, weight conversion, HF export, or SWE evaluation.
"""

import argparse
import contextlib
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CLOUD_ROOT = Path("/mnt/codesign-exp/ycfeng")
COMMON_PACKAGES = ("torch", "transformers", "ray", "tensordict", "TransferQueue")
BACKEND_PACKAGES = {
    "megatron": ("megatron-core", "megatron-bridge", "transformer-engine", "flash-attn", "flash-linear-attention"),
    "fsdp": ("liger-kernel", "flash-attn", "flash-linear-attention"),
    "sglang": ("sglang", "sglang-kernel"),
    "vllm": ("vllm",),
}
IMPORT_MARKER = "VERL_RUNTIME_IMPORT="


def error_record(error):
    return {"type": type(error).__name__, "message": str(error)[-2000:]}


def cloud_path(value):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(CLOUD_ROOT):
        raise ValueError(f"Model asset path must be under {CLOUD_ROOT}")
    # Check lexical confinement before resolving a symlink, then check its target.
    resolved = path.resolve()
    if not resolved.is_relative_to(CLOUD_ROOT.resolve()):
        raise ValueError(f"Model asset symlink leaves {CLOUD_ROOT}")
    return path


def git_output(repository, *arguments):
    result = subprocess.run(
        ["git", "-c", f"safe.directory={repository}", "-C", str(repository), *arguments],
        check=True, capture_output=True, text=True, timeout=15,
    )
    return result.stdout.strip()


def package_versions(repository, required):
    import tomllib

    lock = tomllib.loads((repository / "uv.lock").read_text())
    normalize = lambda name: name.lower().replace("_", "-")
    names = set(COMMON_PACKAGES)
    names.update(name for packages in BACKEND_PACKAGES.values() for name in packages)
    records = {}
    for name in sorted(names):
        candidates = [p for p in lock["package"] if normalize(p["name"]) == normalize(name)]
        if name == "torch":
            candidates = [p for p in candidates if p.get("source", {}).get("registry", "").endswith("/cu130")]
        expected = sorted({p["version"] for p in candidates})
        entry = {"required": name in required, "locked_versions": expected}
        try:
            distribution = importlib.metadata.distribution(name)
            observed = distribution.version
            # CUDA local-version suffixes identify the wheel build, not a different release.
            matches = observed in expected or observed.split("+", 1)[0] in expected
            entry.update(
                version=observed, location=str(distribution.locate_file("")),
                status="PASS" if matches else "VERSION_MISMATCH",
            )
        except importlib.metadata.PackageNotFoundError:
            entry["status"] = "NOT_INSTALLED"
        records[name] = entry
    return records


def import_one(module):
    """Run each import in a child so native-library crashes leave a receipt."""
    source = (
        "import importlib,json\n"
        "try:\n"
        f" m=importlib.import_module({module!r})\n"
        " r={'status':'PASS','file':getattr(m,'__file__',None)}\n"
        "except Exception as e:\n"
        " r={'status':'IMPORT_FAILED','type':type(e).__name__,'message':str(e)[-2000:]}\n"
        f"print({IMPORT_MARKER!r}+json.dumps(r))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-c", source], capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"status": "IMPORT_TIMEOUT", "timeout_seconds": 60}
    payloads = [line[len(IMPORT_MARKER):] for line in result.stdout.splitlines() if line.startswith(IMPORT_MARKER)]
    if not payloads:
        return {"status": "IMPORT_CRASH", "returncode": result.returncode, "stderr": result.stderr[-2000:]}
    record = json.loads(payloads[-1])
    if record["status"] != "PASS":
        message = record.get("message", "").lower()
        gpu_reasons = (
            "libcuda.so", "libcudart.so", "libnvrtc.so", "libnvjitlink.so", "cuda_home",
            "no nvidia driver", "no cuda gpus", "cuda driver", "failed to initialize nvml",
        )
        if any(reason in message for reason in gpu_reasons):
            record["status"] = "GPU_VALIDATION_REQUIRED"
        elif record.get("type") == "ModuleNotFoundError":
            record["status"] = "MISSING_RUNTIME_DEPENDENCY"
    return record


def weight_inventory(model_path):
    """Read only index JSON and file metadata, never safetensors/pickle bytes."""
    for filename in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        index_path = model_path / filename
        if not index_path.is_file():
            continue
        index = json.loads(cloud_path(index_path).read_text())
        weight_map = index.get("weight_map", {})
        if not weight_map:
            return {"status": "FAIL", "index": filename, "reason": "Empty or absent weight_map"}
        shards = sorted(set(weight_map.values()))
        missing = []
        empty = []
        for shard in shards:
            shard_path = cloud_path(model_path / shard)
            if not shard_path.is_file():
                missing.append(shard)
            elif shard_path.stat().st_size == 0:
                empty.append(shard)
        return {
            "status": "PASS" if not missing and not empty else "FAIL", "index": filename,
            "tensor_names_count": len(weight_map), "shards_count": len(shards),
            "missing_shards": missing, "empty_shards": empty,
            "verification_limit": "Index and file metadata only; tensor headers and values were not read.",
        }
    for filename in ("model.safetensors", "pytorch_model.bin"):
        candidate = cloud_path(model_path / filename)
        if candidate.is_file() and candidate.stat().st_size:
            return {"status": "PASS", "index": None, "single_weight_file": filename, "shards_count": 1}
    return {"status": "FAIL", "reason": "No HF weight index or supported single weight file"}


def inspect_model(model_path, transformers, auto_bridge, require_bridge):
    record = {"path": str(model_path)}
    tokenizer = None
    try:
        model_path = cloud_path(model_path)
    except Exception as error:
        record["weights"] = {"status": "FAIL", **error_record(error)}
        return record, tokenizer
    try:
        record["weights"] = weight_inventory(model_path)
    except Exception as error:
        record["weights"] = {"status": "FAIL", **error_record(error)}
    if transformers is None:
        record["config"] = {"status": "UNVERIFIED", "reason": "Transformers import unavailable"}
        record["tokenizer"] = {"status": "UNVERIFIED", "reason": "Transformers import unavailable"}
        return record, tokenizer
    try:
        cloud_path(model_path / "config.json")
        config = transformers.AutoConfig.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=False,
        )
        text_config = getattr(config, "text_config", config)
        record["config"] = {
            "status": "PASS", "class": type(config).__name__, "model_type": config.model_type,
            "architectures": getattr(config, "architectures", None),
            "text_model_type": text_config.model_type, "vocab_size": getattr(text_config, "vocab_size", None),
            "parallel_shape": {
                key: getattr(text_config, key, None)
                for key in (
                    "hidden_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads",
                    "n_routed_experts", "num_experts", "linear_num_key_heads", "linear_num_value_heads",
                )
            },
        }
        record["bridge"] = {"required_for_training": require_bridge}
        if auto_bridge is None:
            record["bridge"].update(status="UNVERIFIED", reason="Native megatron.bridge import unavailable")
        else:
            supported = auto_bridge.list_supported_models()
            bridge = auto_bridge.from_hf_config(config)
            record["bridge"].update(
                status="PASS", registered_architectures=[a for a in config.architectures if a in supported],
                implementation=type(bridge._model_bridge).__module__ + "." + type(bridge._model_bridge).__name__,
                verification_limit="Config-only Bridge dispatch; model construction and tensor conversion unverified.",
            )
    except Exception as error:
        key = "bridge" if record.get("config", {}).get("status") == "PASS" else "config"
        record[key] = {"status": "FAIL", "required_for_training": require_bridge, **error_record(error)}
    try:
        # Inspect only the exact directory. No Hub requests or custom modeling code.
        for candidate in model_path.iterdir():
            if candidate.suffix in (".json", ".model", ".txt", ".tiktoken", ".jinja"):
                cloud_path(candidate)
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=False,
        )
        record["tokenizer"] = {
            "status": "PASS", "class": type(tokenizer).__name__, "length": len(tokenizer),
            "vocab_size": tokenizer.vocab_size, "has_chat_template": bool(tokenizer.chat_template),
        }
    except Exception as error:
        record["tokenizer"] = {"status": "FAIL", **error_record(error)}
    return record, tokenizer


def tokenizer_compatibility(student, teacher):
    if student is None or teacher is None:
        return {"status": "UNVERIFIED", "reason": "At least one tokenizer failed to load"}
    student_vocab, teacher_vocab = student.get_vocab(), teacher.get_vocab()
    mismatches = sum(
        student_vocab.get(token) != teacher_vocab.get(token)
        for token in student_vocab.keys() | teacher_vocab.keys()
    )
    special_tokens_match = student.special_tokens_map == teacher.special_tokens_map
    special_ids_match = student.all_special_ids == teacher.all_special_ids
    return {
        "status": "PASS" if mismatches == 0 and special_tokens_match and special_ids_match else "FAIL",
        "vocabulary_id_mismatches": mismatches, "special_tokens_match": special_tokens_match,
        "special_token_ids_match": special_ids_match,
        "chat_templates_match": student.chat_template == teacher.chat_template,
        "verification_limit": (
            "Vocabulary and special-token identity only; rendered training prompts and teacher scores unverified."
        ),
    }


def run_probe(args):
    repository = Path(__file__).resolve().parents[3]
    required = set(COMMON_PACKAGES + BACKEND_PACKAGES[args.training_backend] + BACKEND_PACKAGES[args.rollout_backend])
    report = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "interpreter": {"executable": sys.executable, "python": platform.python_version()},
        "selected_backends": {"training": args.training_backend, "rollout": args.rollout_backend},
        "scope": "CPU runtime and local HF asset preflight; no GPU allocation or tensor loading.",
        "unverified_gates": [
            "CUDA kernels", "weight conversion", "sameweight log-probability agreement",
            "20 optimizer updates", "HF save/reload", "original/updated SWE evaluation",
        ],
    }
    try:
        report["source"] = {
            "repository": str(repository), "revision": git_output(repository, "rev-parse", "HEAD"),
            "status": git_output(repository, "status", "--short"),
            "uv_lock_sha256": hashlib.sha256((repository / "uv.lock").read_bytes()).hexdigest(),
        }
        report["packages"] = package_versions(repository, required)
    except Exception as error:
        report["environment_error"] = error_record(error)
        return report
    modules = ["verl", "torch", "transformers", "ray", args.rollout_backend]
    if args.training_backend == "megatron":
        modules.append("megatron.bridge")
    report["imports"] = {module: import_one(module) for module in modules}
    verl_import = report["imports"]["verl"]
    if verl_import["status"] == "PASS":
        actual = Path(verl_import["file"]).resolve()
        verl_import["source_matches_repository"] = actual.is_relative_to(repository / "verl")
    transformers = None
    auto_bridge = None
    if report["imports"]["transformers"]["status"] == "PASS":
        transformers = importlib.import_module("transformers")
    if report["imports"].get("megatron.bridge", {}).get("status") == "PASS":
        auto_bridge = importlib.import_module("megatron.bridge").AutoBridge
    if report["imports"]["torch"]["status"] == "PASS":
        torch = importlib.import_module("torch")
        report["cuda"] = {"available": torch.cuda.is_available(), "torch_build_cuda": torch.version.cuda}
    pairs = json.loads(args.pairs.read_text())
    if set(pairs) != {"glm", "qwen"}:
        raise ValueError("--pairs must define exactly the glm and qwen model pairs")
    report["pairs"] = {}
    for name, pair in pairs.items():
        models, tokenizers = {}, {}
        for role in ("student", "teacher"):
            value = pair[role]
            path = value["path"] if isinstance(value, dict) else value
            models[role], tokenizers[role] = inspect_model(
                Path(path), transformers, auto_bridge,
                require_bridge=role == "student" and args.training_backend == "megatron",
            )
        report["pairs"][name] = {
            "models": models,
            "tokenizer_compatibility": tokenizer_compatibility(tokenizers["student"], tokenizers["teacher"]),
        }
    return report


def classify(report):
    failures, incomplete = [], []
    if "environment_error" in report or "probe_error" in report:
        failures.append("probe setup failed")
    for name, package in report.get("packages", {}).items():
        if package["required"] and package["status"] != "PASS":
            failures.append(f"package {name}: {package['status']}")
    for name, module in report.get("imports", {}).items():
        if module["status"] == "GPU_VALIDATION_REQUIRED":
            incomplete.append(f"import {name}: GPU_VALIDATION_REQUIRED")
        elif module["status"] != "PASS":
            failures.append(f"import {name}: {module['status']}")
        if module.get("source_matches_repository") is False:
            failures.append("verl import resolves outside the recorded repository")
    for name, pair in report.get("pairs", {}).items():
        for role, model in pair["models"].items():
            for check in ("weights", "config", "tokenizer", "bridge"):
                result = model.get(check, {"status": "UNVERIFIED"})
                if check == "bridge" and not result.get("required_for_training"):
                    continue
                if result["status"] == "FAIL":
                    failures.append(f"{name}/{role}/{check}: FAIL")
                elif result["status"] != "PASS":
                    incomplete.append(f"{name}/{role}/{check}: {result['status']}")
        result = pair["tokenizer_compatibility"]
        if result["status"] == "FAIL":
            failures.append(f"{name}/tokenizer_compatibility: FAIL")
        elif result["status"] != "PASS":
            incomplete.append(f"{name}/tokenizer_compatibility: {result['status']}")
    status = (
        "FAIL_RUNTIME_PREFLIGHT" if failures else "INCOMPLETE_CPU_PREFLIGHT" if incomplete else "PASS_CPU_PREFLIGHT"
    )
    return {"status": status, "failures": failures, "incomplete": incomplete, "workflow_accepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--training-backend", choices=("megatron", "fsdp"), default="megatron")
    parser.add_argument("--rollout-backend", choices=("sglang", "vllm"), default="sglang")
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        # Libraries may print model-specific diagnostics; keep stdout a compact JSON summary.
        with contextlib.redirect_stdout(io.StringIO()):
            report = run_probe(args)
    except Exception as error:
        report = {"probe_error": error_record(error)}
    report["result"] = classify(report)
    if args.output.resolve().is_relative_to(Path("/mnt/codesign-exp")):
        raise ValueError("--output must point to the mounted local workspace or local temporary storage")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)
        output.write("\n")
    print(json.dumps({"output": str(args.output), **report["result"]}, ensure_ascii=False))
    return 1 if report["result"]["status"] == "FAIL_RUNTIME_PREFLIGHT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
