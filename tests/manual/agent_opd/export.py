"""Verify a completed native update-20 HF export before benchmark consumption.

Only safetensors headers and explicitly limited CPU slices are read. A changed
value witnesses learning; it does not characterize every exported weight. GLM
shared MTP aliases are checked in full using limited slices, never whole-tensor
loads. Reload/generation and numerical qualification remain separate gates.
"""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path

from tests.manual.agent_opd.benchmark import model_inventory, write_json
from tests.manual.agent_opd.runtime_probe import cloud_path


def read_json(path):
    raw = cloud_path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def training_identity(receipt_path, config, original):
    receipt, receipt_hash = read_json(receipt_path)
    if not (
        receipt["native_fit_returned"] is True
        and receipt["requested_updates"] == receipt["completed_updates"] == receipt["actor_update_call_count"] == 20
        and receipt["native_megatron_optimizer_success_contract"]["one_optimizer_step_per_call"] is True
        and len(receipt["update_outcomes"]) == 20
        and [outcome["training_step"] for outcome in receipt["update_outcomes"]] == list(range(1, 21))
        and all(
            outcome["native_update_returned"] is True and outcome["optimizer_steps_verified"] == 1
            and outcome["finite_grad_loss"] is True and outcome["positive_grad_norm"] is True
            and outcome["status"] == "verified"
            for outcome in receipt["update_outcomes"]
        )
    ):
        raise ValueError("The native training receipt does not verify twenty successful optimizer updates")
    if config.trainer.total_training_steps != 20:
        raise ValueError("The native recipe did not request exactly twenty updates")
    if cloud_path(config.actor_rollout_ref.model.path).resolve() != original.resolve():
        raise ValueError("The native recipe does not identify the pinned original student")
    if config.trainer.resume_mode != "disable":
        raise ValueError("This comparison requires the run to start from the original weights without resume")
    export = receipt["final_export"]
    if export is None or export["completed_updates"] != 20:
        raise ValueError("The native fit has not published its final update-20 HF export")
    model = cloud_path(export["model_path"]).resolve()
    save_root = cloud_path(config.trainer.default_local_dir).resolve()
    if model == original.resolve() or not model.is_relative_to(save_root):
        raise ValueError("The final HF export is not a distinct model within this run's checkpoint directory")
    manifest_path = cloud_path(export["native_manifest_path"]).resolve()
    if manifest_path.name != "ckpt_contents.json" or not manifest_path.is_relative_to(save_root):
        raise ValueError("The final native manifest is outside this run's checkpoints")
    manifest, manifest_hash = read_json(manifest_path)
    if not (
        manifest_hash == export["native_manifest_sha256"]
        and manifest["global_step"] == 20 == export["native_manifest_global_step"]
        == export["training_step"] == receipt["last_native_checkpoint_step"]
    ):
        raise ValueError("The completed native checkpoint manifest differs from the training receipt")
    if not (
        manifest["framework"] == "megatron" and manifest["role"] == "actor"
        and manifest["save_contents"] == ["hf_model"]
        and manifest["backend"]["has_bridge"] is True
        and manifest["backend"]["use_dist_checkpointing"] is False
        and manifest["backend"]["peft"] is False
        and manifest["saved_any_dist_ckpt"] is False
    ):
        raise ValueError("The native manifest is not this task's complete actor HF-only Bridge export")
    saved = manifest["contents"]["hf_model"]
    relative = Path(saved["path"])
    if relative.is_absolute() or ".." in relative.parts or saved["format"] != "huggingface":
        raise ValueError("The native manifest does not declare a confined HF model path")
    if cloud_path(manifest_path.parent / relative).resolve() != model:
        raise ValueError("The native manifest and training receipt identify different HF exports")
    return model, export, {
        "training_receipt_path": str(receipt_path), "training_receipt_sha256": receipt_hash,
        "native_manifest_path": str(manifest_path), "native_manifest_sha256": manifest_hash,
        "native_manifest_global_step": manifest["global_step"], "completed_updates": 20,
    }


def tensor_inventory(path):
    """Extend the benchmark's actual index/shard checks with shape and dtype."""
    from safetensors import safe_open

    path = cloud_path(path).resolve()
    result = model_inventory(path)
    names = {shard["name"] for shard in result["shards"]}
    if {shard.name for shard in path.glob("*.safetensors")} != names:
        raise ValueError("The HF directory contains safetensors shards outside the complete published inventory")
    tensors = {}
    for name in sorted(names):
        shard = cloud_path(path / name)
        with safe_open(shard, framework="pt", device="cpu") as source:
            for key in source.keys():
                value = source.get_slice(key)
                tensors[key] = {"shape": value.get_shape(), "dtype": value.get_dtype(), "shard": name}
    result["tensors"] = tensors
    return result


def glm_decoder_scope(before, after, hf_config, config):
    """Apply only the decoder/MTP contract of pinned GLM47FlashBridge 0.6.2.

    glm47_flash_bridge.py:99 builds MTP from num_nextn_predict_layers unless
    overridden. Lines134-147 clone only the shared embedding/head aliases on
    export. Untrained MTP parameters are excluded only with an explicit zero
    provider override and disabled model MTP in the actual native recipe.
    """
    actor = config.actor_rollout_ref
    if actor.model.mtp.enable is not False or actor.actor.megatron.override_transformer_config.mtp_num_layers != 0:
        raise ValueError("The GLM decoder comparison requires explicit disabled MTP and mtp_num_layers=0")
    if importlib.metadata.version("megatron-bridge") != "0.6.2":
        raise ValueError("The GLM export scope was verified only against pinned Megatron-Bridge 0.6.2")
    prefixes = tuple(
        f"model.layers.{layer}."
        for layer in range(
            hf_config["num_hidden_layers"],
            hf_config["num_hidden_layers"] + hf_config.get("num_nextn_predict_layers", 0),
        )
    )
    decoder = {name: value for name, value in before.items() if not name.startswith(prefixes)}
    aliases = {
        prefix + suffix: canonical
        for prefix in prefixes
        for suffix, canonical in (
            ("embed_tokens.weight", "model.embed_tokens.weight"),
            ("shared_head.head.weight", "lm_head.weight"),
        )
    }
    if any(alias not in after or canonical not in after for alias, canonical in aliases.items()):
        raise ValueError("The GLM export is missing a required shared MTP alias or its canonical decoder source")
    return decoder, aliases


EXPORT_SCOPES = {"glm4_moe_lite": glm_decoder_scope}


def tensor_selections(shape, max_elements):
    """Cover a tensor with disjoint slices containing at most max_elements."""
    if not shape:
        yield ()
        return
    if any(size == 0 for size in shape):
        return
    axis = 0
    while math.prod(shape[axis + 1:]) > max_elements:
        axis += 1
    width = max_elements // math.prod(shape[axis + 1:])
    for prefix in itertools.product(*(range(size) for size in shape[:axis])):
        for start in range(0, shape[axis], width):
            yield prefix + (slice(start, min(start + width, shape[axis])),) + (slice(None),) * (len(shape) - axis - 1)


def verify_aliases(model, tensors, aliases, chunk_elements):
    from safetensors import safe_open

    verified = {}
    for alias, canonical in aliases.items():
        left, right = tensors[alias], tensors[canonical]
        if (left["shape"], left["dtype"]) != (right["shape"], right["dtype"]):
            raise ValueError(f"Shared MTP alias metadata differs from its decoder source: {alias}")
        with (
            safe_open(cloud_path(model / left["shard"]), framework="pt", device="cpu") as left_file,
            safe_open(cloud_path(model / right["shard"]), framework="pt", device="cpu") as right_file,
        ):
            for selection in tensor_selections(left["shape"], chunk_elements):
                if not left_file.get_slice(alias)[selection].equal(right_file.get_slice(canonical)[selection]):
                    raise ValueError(f"Shared MTP alias values differ from the complete decoder source: {alias}")
        verified[alias] = {"source": canonical, "all_values_equal": True, "elements": math.prod(left["shape"])}
    return verified


def changed_witness(original, model, before, after, sample_elements):
    from safetensors import safe_open

    examined = 0
    for name in sorted(before):
        left, right = before[name], after[name]
        selection = next(tensor_selections(left["shape"], sample_elements), None)
        if selection is None:
            continue
        with (
            safe_open(cloud_path(original / left["shard"]), framework="pt", device="cpu") as left_file,
            safe_open(cloud_path(model / right["shard"]), framework="pt", device="cpu") as right_file,
        ):
            left_value = left_file.get_slice(name)[selection]
            right_value = right_file.get_slice(name)[selection]
        examined += 1
        if not (left_value.isfinite().all() and right_value.isfinite().all()):
            raise ValueError(f"The inspected weight slice contains non-finite values: {name}")
        if left_value.equal(right_value):
            continue
        coordinate = (left_value != right_value).nonzero()[0].tolist()
        position, dimension = [], 0
        for part in selection:
            if isinstance(part, int):
                position.append(part)
            else:
                position.append((part.start or 0) + coordinate[dimension])
                dimension += 1
        local = tuple(coordinate)
        return {
            "tensor": name, "shape": left["shape"], "dtype": left["dtype"], "coordinates": position,
            "original_value": left_value[local].item(), "exported_value": right_value[local].item(),
            "sampled_elements_in_tensor": left_value.numel(), "sampled_tensor_count": examined,
            "scope": "First bounded slice of each sorted decoder tensor, stopped at the first unequal value",
            "unsampled_values_verified": False,
        }
    raise ValueError(
        "No changed value was observed in the inspected slices; optimizer updates do not prove weight change"
    )


def inspect_export(args):
    from omegaconf import OmegaConf

    original = cloud_path(json.loads(args.pairs.read_text())[args.pair]["student"]).resolve()
    config_path = cloud_path(args.config)
    config = OmegaConf.load(config_path)
    model, native_export, identity = training_identity(cloud_path(args.training_receipt), config, original)
    before, after = tensor_inventory(original), tensor_inventory(model)
    before_config, _ = read_json(original / "config.json")
    after_config, _ = read_json(model / "config.json")
    if any(before_config.get(key) != after_config.get(key) for key in ("model_type", "architectures")):
        raise ValueError("The exported HF model architecture differs from the pinned student")
    weights = {item["name"]: item["bytes"] for item in after["shards"]}
    if weights != {item["name"]: item["bytes"] for item in native_export["weight_files"]}:
        raise ValueError("The complete exported weight files differ from the native fit receipt")
    if sum(weights.values()) != native_export["weight_total_bytes"]:
        raise ValueError("The exported weight byte count differs from the native fit receipt")
    policy = EXPORT_SCOPES.get(before_config["model_type"])
    decoder, aliases = policy(before["tensors"], after["tensors"], before_config, config) if policy else (
        before["tensors"], {}
    )
    expected = {name: (value["shape"], value["dtype"]) for name, value in decoder.items()}
    actual = {name: (value["shape"], value["dtype"]) for name, value in after["tensors"].items() if name not in aliases}
    if not expected or expected != actual:
        missing, extra = sorted(expected.keys() - actual.keys()), sorted(actual.keys() - expected.keys())
        changed = sorted(name for name in expected.keys() & actual.keys() if expected[name] != actual[name])
        raise ValueError(
            f"Exported tensor metadata differs: missing={missing}, extra={extra}, shape_or_dtype={changed}"
        )
    shared = verify_aliases(model, after["tensors"], aliases, args.value_chunk_elements)
    witness = changed_witness(original, model, decoder, after["tensors"], args.sample_elements)
    inventory = {"original": before, "exported": after, "verified_shared_mtp_aliases": shared}
    receipt = {
        "status": "verified", "pair": args.pair, "original_model_path": str(original), "model_path": str(model),
        **identity,
        "native_recipe_path": str(config_path),
        "native_recipe_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "tensor_inventory": {
            "status": "verified", "original_tensor_count": before["tensor_count"],
            "exported_tensor_count": after["tensor_count"], "decoder_tensor_count": len(decoder),
            "excluded_untrained_mtp_tensor_count": len(before["tensors"]) - len(decoder),
            "verified_shared_mtp_aliases": shared,
            "scope": "All tensor names, shapes, dtypes and actual index/shard locations; no Qwen/VL name exclusions",
        },
        "weight_change_verified": True, "changed_witness": witness,
        "sample_elements": args.sample_elements, "value_chunk_elements": args.value_chunk_elements,
        "new_process_reload_verified": False, "numerical_agreement_verified": False,
    }
    return receipt, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--pair", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--training-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-elements", type=int, required=True)
    parser.add_argument("--value-chunk-elements", type=int, required=True)
    args = parser.parse_args()
    if min(args.sample_elements, args.value_chunk_elements) <= 0:
        raise ValueError("Weight slice element limits must be positive")
    output = cloud_path(args.output)
    inventory_path = cloud_path(output.with_name(output.stem + ".tensors.json"))
    if output.exists() or inventory_path.exists():
        raise FileExistsError("Export verification writes new receipts only; use a new output name")
    try:
        receipt, inventory = inspect_export(args)
    except Exception as error:
        failed_path = cloud_path(output.with_name(output.stem + ".unverified.json"))
        if failed_path.exists():
            raise FileExistsError(f"The failure receipt already exists: {failed_path}") from error
        write_json(failed_path, {
            "status": "unverified", "pair": args.pair, "error": f"{type(error).__name__}: {error}",
        })
        print("VERL_EXPORT_UNVERIFIED " + str(failed_path), flush=True)
        return 2
    inventory_bytes = (json.dumps(inventory, indent=2) + "\n").encode()
    receipt["tensor_inventory"].update(
        path=str(inventory_path), sha256=hashlib.sha256(inventory_bytes).hexdigest(),
    )
    write_json(inventory_path, inventory)
    write_json(output, receipt)
    print("VERL_EXPORT_VERIFIED " + str(output), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
