"""Run native OPD and observe student logprobs before each actor update.

Usage: python -m tests.manual.agent_opd.train --config recipe.yaml
       --observations /mnt/codesign-exp/ycfeng/<task>/<run>/observations

Observations never replace tensors or determine whether native training runs.
Trainer weight versions describe the inspected synchronous trainer lifecycle;
they are not an independent checksum of every worker's live parameters.
"""

import argparse
import hashlib
import json
import logging
import math
from collections import Counter, defaultdict
from pathlib import Path

import ray
import torch
from omegaconf import OmegaConf

from tests.manual.agent_opd.agent_loop import _weight_version
from tests.manual.agent_opd.alignment import compare_logprobs
from tests.manual.agent_opd.prepare_turns import token_hash
from verl.trainer.main_ppo import run_ppo
from verl.trainer.main_ppo_v0 import BaseTaskRunner
from verl.trainer.ppo.ray_trainer import RayPPOTrainer
from verl.trainer.ppo.utils import create_rl_dataset, create_rl_sampler, need_critic, need_reference_policy
from verl.utils.config import omega_conf_to_dataclass, validate_config
from verl.utils.dataset.rl_dataset import collate_fn
from verl.workers.config import HFModelConfig

logger = logging.getLogger(__name__)
PAIRS = {
    "decode_vs_prefill": ("decode", "prefill"),
    "decode_vs_trainer": ("decode", "trainer"),
    "prefill_vs_trainer": ("prefill", "trainer"),
}
VERSION_SOURCE = (
    "RayPPOTrainer.fit publishes the initial loaded version before generation, then each completed step; "
    "_compute_old_log_prob runs before the current step update. No independent live parameter checksum."
)


def observation_directory(value):
    path = Path(value).resolve()
    path.relative_to("/mnt/codesign-exp/ycfeng")
    return path


def observer_settings(config):
    agent = config.actor_rollout_ref.rollout.agent
    entries = OmegaConf.load(agent.agent_loop_config_path)
    selected = [entry for entry in entries if entry.name == agent.default_agent_loop]
    if len(selected) != 1:
        raise ValueError("The default agent loop must have one explicit configuration entry")
    entry = selected[0]
    return {
        "ratio_bounds": OmegaConf.to_container(entry.ratio_bounds, resolve=True),
        "numerical_limits": OmegaConf.to_container(entry.numerical_limits, resolve=True)
        if entry.get("numerical_limits") is not None
        else None,
    }


def _unverified(error):
    return {"status": "unverified", "error_type": type(error).__name__, "reason": str(error)}


def _compare(record, reference, candidate, settings):
    if "prefill" in (reference, candidate) and not record["independent_prefill"]:
        raise ValueError("An independent student prefill was not verified")
    return compare_logprobs(
        record[f"{reference}_logprobs"],
        record[f"{candidate}_logprobs"],
        reference_token_ids=record[f"{reference}_token_ids"],
        candidate_token_ids=record[f"{candidate}_token_ids"],
        reference_weight_version=record["weight_versions"][reference],
        candidate_weight_version=record["weight_versions"][candidate],
        **settings,
    )


def _aggregate(records, settings):
    """Aggregate each training step without inventing a cross-step weight version."""
    result = {"turn_count": len(records), "comparisons": {}}
    for name, (reference, candidate) in PAIRS.items():
        valid = [
            record
            for record in records
            if name in record.get("comparisons", {})
            and record["comparisons"][name]["status"] != "unverified"
        ]
        entry = {"verified_turn_count": len(valid), "unverified_turn_count": len(records) - len(valid)}
        if valid:
            versions = {record["weight_versions"][reference] for record in valid}
            if len(versions) != 1:
                raise ValueError("An aggregate must cover one actual weight version")
            version = versions.pop()
            entry["metrics"] = compare_logprobs(
                [value for record in valid for value in record[f"{reference}_logprobs"]],
                [value for record in valid for value in record[f"{candidate}_logprobs"]],
                reference_token_ids=[value for record in valid for value in record[f"{reference}_token_ids"]],
                candidate_token_ids=[value for record in valid for value in record[f"{candidate}_token_ids"]],
                reference_weight_version=version,
                candidate_weight_version=version,
                **settings,
            )
        result["comparisons"][name] = entry
    return result


class ObservedPPOTrainer(RayPPOTrainer):
    """Keep native computation intact and save auxiliary observations separately."""

    def __init__(self, *args, observations, alignment_settings, **kwargs):
        super().__init__(*args, **kwargs)
        self.observations = observations
        self.alignment_settings = alignment_settings
        self.observed_turns = []
        self.training_receipt = {
            "requested_updates": int(self.total_training_steps),
            "actor_update_call_count": 0,
            "completed_updates": 0,
            "update_outcomes": [],
            "native_megatron_optimizer_success_contract": {
                "source": "verl/workers/engine/megatron/transformer_impl.py:MegatronEngine.optimizer_step",
                "success_condition": "Megatron optimizer.step update_successful=False raises before returning",
                "iteration_source": "verl/workers/engine_workers.py:TrainingWorker.train_mini_batch",
                "one_optimizer_step_per_call": True,
            },
            "native_fit_returned": False,
            "last_native_checkpoint_step": None,
            "final_export": None,
        }

    def _save_training_receipt(self):
        try:
            (self.observations / "training.json").write_text(
                json.dumps(self.training_receipt, indent=2, allow_nan=False) + "\n"
            )
        except Exception as error:
            logger.warning("AGENT_OPD_TRAINING_RECEIPT_UNVERIFIED %s: %s", type(error).__name__, error)

    def _update_actor(self, batch):
        self.training_receipt["actor_update_call_count"] += 1
        outcome = {"training_step": int(self.global_steps), "native_update_returned": False}
        try:
            result = super()._update_actor(batch)
        except Exception as error:
            outcome.update(_unverified(error))
            self.training_receipt["update_outcomes"].append(outcome)
            self._save_training_receipt()
            raise
        outcome["native_update_returned"] = True
        try:
            expected_size = (
                self.config.actor_rollout_ref.actor.ppo_mini_batch_size * self.config.actor_rollout_ref.rollout.n
            )
            if len(batch) != expected_size:
                raise ValueError("The actor call did not cover exactly one configured optimizer mini-batch")
            self.training_receipt["completed_updates"] += 1
            outcome["optimizer_steps_verified"] = 1
            metrics = result.meta_info["metrics"]
            loss = torch.as_tensor(metrics["actor/loss"], dtype=torch.float64).flatten().tolist()
            gradient = torch.as_tensor(metrics["actor/grad_norm"], dtype=torch.float64).flatten().tolist()
            finite = bool(loss and gradient) and all(math.isfinite(value) for value in loss + gradient)
            outcome["finite_grad_loss"] = finite
            outcome["positive_grad_norm"] = bool(gradient) and all(value > 0 for value in gradient)
            if not finite:
                raise ValueError("Native loss or gradient metrics are missing or non-finite")
            outcome.update(loss_values=loss, grad_norm_values=gradient)
            outcome["status"] = "verified" if outcome["positive_grad_norm"] else "unverified"
        except Exception as error:
            outcome.update(_unverified(error))
            logger.warning("AGENT_OPD_UPDATE_RECEIPT_UNVERIFIED %s: %s", type(error).__name__, error)
        self.training_receipt["update_outcomes"].append(outcome)
        self._save_training_receipt()
        return result

    def _save_checkpoint(self):
        result = super()._save_checkpoint()
        self.training_receipt["last_native_checkpoint_step"] = int(self.global_steps)
        return result

    def _observe_final_export(self):
        # Native fit has already finalized outstanding async checkpoint writes.
        try:
            receipt = self.training_receipt
            if receipt["completed_updates"] != receipt["requested_updates"]:
                raise ValueError("The checkpoint is not the requested final successful update")
            if any(outcome["status"] != "verified" for outcome in receipt["update_outcomes"]):
                raise ValueError("The final export has unverified update metrics")
            saved_step = receipt["last_native_checkpoint_step"]
            if saved_step is None:
                raise ValueError("No native checkpoint save returned during this run")
            checkpoint = observation_directory(self.config.trainer.default_local_dir)
            checkpoint = checkpoint / f"global_step_{saved_step}" / "actor"
            manifest_path = checkpoint / "ckpt_contents.json"
            manifest_bytes = manifest_path.read_bytes()
            manifest = json.loads(manifest_bytes)
            if manifest["global_step"] != saved_step:
                raise ValueError("The native checkpoint manifest does not identify the current saved step")
            model_path = (checkpoint / manifest["contents"]["hf_model"]["path"]).resolve()
            model_path.relative_to(checkpoint.resolve())
            files = sorted([*model_path.glob("*.safetensors"), *model_path.glob("*.bin")])
            inventory = [{"name": path.name, "bytes": path.stat().st_size} for path in files]
            if not (model_path / "config.json").is_file() or not inventory or any(
                entry["bytes"] == 0 for entry in inventory
            ):
                raise ValueError("The native HF export has no nonempty weight inventory")
            receipt["final_export"] = {
                "completed_updates": receipt["completed_updates"],
                "training_step": saved_step,
                "model_path": str(model_path),
                "native_manifest_path": str(manifest_path),
                "native_manifest_global_step": manifest["global_step"],
                "native_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "weight_files": inventory,
                "weight_total_bytes": sum(entry["bytes"] for entry in inventory),
                "new_process_reload_verified": False,
                "weight_change_verified": False,
            }
        except Exception as error:
            self.training_receipt["export_observation"] = _unverified(error)
            logger.warning("AGENT_OPD_EXPORT_RECEIPT_UNVERIFIED %s: %s", type(error).__name__, error)

    def fit(self):
        self._save_training_receipt()
        result = super().fit()
        self.training_receipt["native_fit_returned"] = True
        self._observe_final_export()
        self._save_training_receipt()
        return result

    def _observe_turn(self, batch, old_log_prob, index):
        rescoring = batch.non_tensor_batch["student_rescoring"][index]
        receipt = rescoring["prompt_receipt"]
        response_mask = batch.batch["response_mask"][index].detach().cpu()
        response_ids = batch.batch["responses"][index].detach().cpu()
        generated_ids = rescoring["response_token_ids"]
        expected_mask = [1] * len(generated_ids) + [0] * (len(response_ids) - len(generated_ids))
        if response_mask.tolist() != expected_mask:
            raise ValueError("The native single-turn response mask differs from the generated token span")
        selected = response_mask.bool()
        trainer_ids = response_ids[selected].tolist()
        if trainer_ids != generated_ids:
            raise ValueError("The trainer response token IDs differ from the sampled response")
        prompt_width = batch.batch["prompts"].shape[1]
        attention = batch.batch["attention_mask"][index].detach().cpu()
        if attention[prompt_width:].tolist() != expected_mask:
            raise ValueError("Response attention and generated-token masks differ")
        prompt_ids = batch.batch["prompts"][index].detach().cpu()[attention[:prompt_width].bool()].tolist()
        if len(prompt_ids) != receipt["token_count"] or token_hash(prompt_ids) != receipt["token_sha256"]:
            raise ValueError("The unpadded trainer prompt differs from the verified generation prompt")
        active = attention.bool()
        inputs = batch.batch["input_ids"][index].detach().cpu()[active].tolist()
        if inputs != prompt_ids + trainer_ids:
            raise ValueError("The actor input sequence differs from the generation sequence")
        positions = batch.batch["position_ids"][index].detach().cpu()[..., active]
        expected_positions = torch.arange(len(inputs), dtype=positions.dtype).expand_as(positions)
        if not torch.equal(positions, expected_positions):
            raise ValueError("The actor text positions differ from the unpadded generation sequence")
        decode_tensor = batch.batch["rollout_log_probs"][index].detach().cpu()
        decode = decode_tensor[selected].tolist()
        expected_decode = decode_tensor.new_tensor(rescoring["decode_logprobs"]).tolist()
        if decode != expected_decode:
            raise ValueError("The native rollout logprob tensor differs from the sampled logprobs")
        trainer = old_log_prob.batch["old_log_probs"][index].detach().cpu()[selected].tolist()
        if not all(math.isfinite(value) for value in decode + trainer):
            raise ValueError("Decode or trainer logprobs contain non-finite values")

        # This task uses the native synchronous fit loop and checkpoint manager.
        # A custom manager has no inspected version contract and stays unknown.
        native_manager = not self.config.actor_rollout_ref.rollout.get("checkpoint_manager_class")
        trainer_version = int(self.global_steps) - 1 if native_manager else None
        record = {
            "training_step": int(self.global_steps),
            "trainer_weight_version": trainer_version,
            "version_source": VERSION_SOURCE if native_manager else "Unverified custom checkpoint manager",
            "source_uid": receipt["source_uid"],
            "source_category": receipt["source_category"],
            "completion": batch.non_tensor_batch["completion"][index],
            "generated_category": batch.non_tensor_batch["completion"][index]["category"],
            "prompt_token_count": len(prompt_ids),
            "prompt_token_sha256": receipt["token_sha256"],
            "response_token_count": len(trainer_ids),
            "response_mask": response_mask.tolist(),
            "token_ids_match": True,
            "prompt_ids_match": True,
            "positions_match": True,
            "decode_token_ids": generated_ids,
            "trainer_token_ids": trainer_ids,
            "decode_logprobs": decode,
            "trainer_logprobs": trainer,
            "independent_prefill": rescoring["independent_prefill"],
            "weight_versions": {"trainer": trainer_version},
            "decode_weight_metadata": rescoring["decode_weight_metadata"],
            "prefill_weight_metadata": rescoring.get("prefill_weight_metadata"),
            "student_rescoring_status": rescoring["status"],
            "router_replay_mode": self.config.actor_rollout_ref.actor.megatron.router_replay.mode,
            "rollout_route_shape": list(batch.batch["routed_experts"][index].shape)
            if "routed_experts" in batch.batch else None,
            "route_observation": "Input route inventory only; no separate observation of replayed kernel routes",
        }
        if "prefill_logprobs" in rescoring and all(math.isfinite(value) for value in rescoring["prefill_logprobs"]):
            record["prefill_logprobs"] = rescoring["prefill_logprobs"]
            record["prefill_token_ids"] = rescoring["prefill_token_ids"]
        for name in ("decode", "prefill"):
            try:
                record["weight_versions"][name] = _weight_version(rescoring[f"{name}_weight_metadata"])
            except Exception as error:
                record["weight_versions"][name] = None
                record[f"{name}_version_error"] = _unverified(error)
        record["comparisons"] = {}
        for name, (reference, candidate) in PAIRS.items():
            try:
                record["comparisons"][name] = _compare(record, reference, candidate, self.alignment_settings)
            except Exception as error:
                record["comparisons"][name] = _unverified(error)
        statuses = {value["status"] for value in record["comparisons"].values()}
        record["status"] = (
            "unverified" if "unverified" in statuses else "fail" if "fail" in statuses else statuses.pop()
        )
        return record

    def _save_observations(self, records):
        with (self.observations / "turns.jsonl").open("a") as stream:
            for record in records:
                stream.write(json.dumps(record, allow_nan=False) + "\n")
        self.observed_turns.extend(records)
        by_step = defaultdict(list)
        for record in self.observed_turns:
            by_step[record["training_step"]].append(record)
        summary = {
            "turn_status_counts": dict(Counter(record["status"] for record in self.observed_turns)),
            "numerical_limits": self.alignment_settings["numerical_limits"],
            "version_source": VERSION_SOURCE,
            "aggregation_scope": "Each training step separately; versions are never combined",
            "by_training_step": {},
        }
        for step, turns in by_step.items():
            step_summary = {"all": _aggregate(turns, self.alignment_settings)}
            for field in ("source_category", "generated_category", "response_token_count"):
                groups = defaultdict(list)
                for turn in turns:
                    if field in turn:
                        groups[str(turn[field])].append(turn)
                step_summary[f"by_{field}"] = {
                    label: _aggregate(group, self.alignment_settings) for label, group in groups.items()
                }
            summary["by_training_step"][str(step)] = step_summary
        (self.observations / "aggregate.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")

    def _compute_old_log_prob(self, batch):
        result = super()._compute_old_log_prob(batch)
        try:
            records = []
            for index in range(len(batch)):
                try:
                    records.append(self._observe_turn(batch, result[0], index))
                except Exception as error:
                    records.append({
                        "training_step": int(self.global_steps), "batch_index": index, **_unverified(error)
                    })
                    logger.warning("AGENT_OPD_TRAINER_OBSERVATION_UNVERIFIED %s: %s", type(error).__name__, error)
            self._save_observations(records)
        except Exception as error:
            logger.warning("AGENT_OPD_OBSERVATION_WRITE_UNVERIFIED %s: %s", type(error).__name__, error)
        return result


def run_training(runner, config, observations, settings):
    """Use BaseTaskRunner's native worker setup and dataset construction."""
    OmegaConf.resolve(config)
    actor_rollout_cls, worker_group_cls = runner.add_actor_rollout_worker(config)
    runner.add_critic_worker(config)
    runner.add_reward_model_resource_pool(config)
    runner.add_teacher_model_resource_pool(config)
    runner.add_ref_policy_worker(config, actor_rollout_cls)
    validate_config(config, use_reference_policy=need_reference_policy(config), use_critic=need_critic(config))
    model: HFModelConfig = omega_conf_to_dataclass(config.actor_rollout_ref.model)
    train_dataset = create_rl_dataset(
        config.data.train_files, config.data, model.tokenizer, model.processor,
        is_train=True, max_samples=config.data.get("train_max_samples", -1),
    )
    val_dataset = create_rl_dataset(
        config.data.val_files, config.data, model.tokenizer, model.processor,
        is_train=False, max_samples=config.data.get("val_max_samples", -1),
    )
    trainer = ObservedPPOTrainer(
        config=config,
        tokenizer=model.tokenizer,
        processor=model.processor,
        role_worker_mapping=runner.role_worker_mapping,
        resource_pool_manager=runner.init_resource_pool_mgr(config),
        ray_worker_group_cls=worker_group_cls,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        collate_fn=collate_fn,
        train_sampler=create_rl_sampler(config.data, train_dataset),
        observations=observations,
        alignment_settings=settings,
    )
    trainer.init_workers()
    trainer.fit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--observations", type=observation_directory, required=True)
    args = parser.parse_args()
    config = OmegaConf.load(args.config)
    if config.trainer.use_v1 or config.algorithm.rollout_correction.bypass_mode:
        raise ValueError("This observer requires native v0 training with actor logprob recomputation")
    actor = config.actor_rollout_ref.actor
    generator_batch_size = config.data.get("gen_batch_size") or config.data.train_batch_size
    if actor.strategy != "megatron" or actor.ppo_epochs != 1 or actor.ppo_mini_batch_size != generator_batch_size:
        raise ValueError("Update receipts require native Megatron with one full optimizer mini-batch and one epoch")
    if config.trainer.resume_mode != "disable":
        raise ValueError("This task counts updates from original weights and requires resume_mode=disable")
    settings = observer_settings(config)
    args.observations.mkdir(parents=True, exist_ok=False)
    observations = args.observations

    @ray.remote
    class TaskRunner(BaseTaskRunner):
        def run(self, native_config):
            run_training(self, native_config, observations, settings)

    run_ppo(config, task_runner_class=TaskRunner)


if __name__ == "__main__":
    main()
