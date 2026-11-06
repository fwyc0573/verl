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
"""Compose a native Megatron/SGLang OPD recipe; never start a worker or trainer.

Layout values belong to each pairs.json entry's runtime mapping. Shared run
values are explicit in --settings JSON. --dry-run permits nonexistent asset
paths so Hydra schema validation can run before cloud assets are mounted.
"""

import argparse
import json
import sys
from pathlib import Path

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from tests.manual.agent_opd.alignment import validate_numerical_limits
from verl.utils.config import omega_conf_to_dataclass

RUNTIME_FIELDS = (
    "actor_gpus", "teacher_gpus", "actor_tp", "actor_pp", "actor_cp", "actor_ep", "actor_etp",
    "rollout_tp", "teacher_tp", "router_replay_mode", "inference_engine_kwargs",
)
SETTING_FIELDS = (
    "context_length", "response_length", "train_batch_size", "ppo_max_token_len_per_gpu",
    "learning_rate", "seed", "save_directory", "project_name", "experiment_name", "optimizer_betas",
    "weight_decay", "clip_ratio", "clip_ratio_high", "importance_ratio_bounds",
    "rollout_memory_utilization", "teacher_memory_utilization", "max_running_requests", "chunked_prefill_size",
    "numerical_limits", "use_fused_kernels",
)


def require_fields(mapping, names, label):
    missing = sorted(set(names) - mapping.keys())
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")


def cloud_path(value):
    path = Path(value)
    root = Path("/mnt/codesign-exp/ycfeng")
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(root):
        raise ValueError(f"Artifact path must be under {root}: {path}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Artifact symlink leaves {root}: {path}")
    return str(path)


def hydra_value(value):
    if isinstance(value, dict):
        return "{" + ",".join(f"{key}:{hydra_value(item)}" for key, item in value.items()) + "}"
    return json.dumps(value)


def recipe_overrides(pair, settings, *, dataset, agent_config, steps, repository):
    runtime = pair["runtime"]
    require_fields(runtime, RUNTIME_FIELDS, "Pair runtime")
    require_fields(settings, SETTING_FIELDS, "Run settings")
    validate_numerical_limits(settings["numerical_limits"])
    if steps <= 0 or settings["train_batch_size"] <= 0:
        raise ValueError("steps and train_batch_size must be positive")
    if settings["context_length"] <= settings["response_length"] + 1 or settings["response_length"] <= 0:
        raise ValueError("context_length must fit a positive prompt, response, and one teacher scoring token")
    for key in RUNTIME_FIELDS:
        if key not in ("router_replay_mode", "inference_engine_kwargs") and (
            not isinstance(runtime[key], int) or runtime[key] <= 0
        ):
            raise ValueError(f"runtime.{key} must be a positive integer")
    if runtime["router_replay_mode"] not in ("disabled", "R3"):
        raise ValueError("This task supports disabled routing replay or rollout-origin R3 replay")
    for pool, tp in (("actor_gpus", "actor_tp"), ("actor_gpus", "rollout_tp"), ("teacher_gpus", "teacher_tp")):
        if runtime[pool] % runtime[tp]:
            raise ValueError(f"runtime.{pool} must be divisible by runtime.{tp}")
    # Megatron-Core core_v0.19.2 parallel_state initializes separate dense and
    # expert rank grids. EP consumes the expert grid, whose TP is ETP, not TP.
    grids = {
        "dense": runtime["actor_tp"] * runtime["actor_pp"] * runtime["actor_cp"],
        "expert": runtime["actor_etp"] * runtime["actor_ep"] * runtime["actor_pp"],
    }
    for name, size in grids.items():
        if runtime["actor_gpus"] % size:
            raise ValueError(f"Actor world size must be divisible by the native {name} parallel grid size {size}")
    lower, upper = settings["importance_ratio_bounds"]
    if not 0 < lower <= upper:
        raise ValueError("importance_ratio_bounds must contain positive ordered bounds")
    if pair["student"] == pair["teacher"]:
        raise ValueError("OPD requires distinct student and teacher checkpoint paths")
    engine_kwargs = {
        "disable_cuda_graph": True,
        "enable_deterministic_inference": True,
        "attention_backend": "fa3",
        "moe_runner_backend": "triton",
        "disable_radix_cache": True,
        "max_running_requests": settings["max_running_requests"],
        "chunked_prefill_size": settings["chunked_prefill_size"],
    }
    engine_kwargs.update(runtime["inference_engine_kwargs"])
    overrides = {
        "trainer.use_v1": False,
        "trainer.nnodes": 1,
        "trainer.n_gpus_per_node": runtime["actor_gpus"],
        "trainer.total_training_steps": steps,
        "trainer.total_epochs": 1,
        "trainer.save_freq": steps,
        "trainer.test_freq": -1,
        "trainer.val_before_train": False,
        "trainer.resume_mode": "disable",
        "trainer.default_local_dir": cloud_path(settings["save_directory"]),
        "trainer.project_name": settings["project_name"],
        "trainer.experiment_name": settings["experiment_name"],
        "trainer.logger": ["console"],
        "data.train_files": [cloud_path(dataset)],
        # The legacy trainer requires a nonempty validation loader even when
        # validation is disabled. This placeholder is never used for evaluation.
        "data.val_files": [cloud_path(dataset)],
        "data.train_batch_size": settings["train_batch_size"],
        "data.train_max_samples": steps * settings["train_batch_size"],
        "data.shuffle": False,
        # Native teacher scoring needs one generated token after the student's response.
        "data.max_prompt_length": settings["context_length"] - settings["response_length"] - 1,
        "data.max_response_length": settings["response_length"],
        "data.truncation": "error",
        "data.filter_overlong_prompts": False,
        "data.custom_cls.path": str(repository / "tests/manual/agent_opd/prepare_turns.py"),
        "data.custom_cls.name": "PreparedTurnDataset",
        "algorithm.adv_estimator": "grpo",
        "algorithm.use_kl_in_reward": False,
        "algorithm.rollout_correction.bypass_mode": False,
        # Native IcePop keeps the in-range importance ratio and zeros the rest,
        # matching the source task's token TIS mask rather than changing logits.
        "algorithm.rollout_correction.rollout_is": "token",
        "algorithm.rollout_correction.rollout_is_threshold": f"{lower}_{upper}",
        "algorithm.rollout_correction.rollout_rs": "token_k1",
        "algorithm.rollout_correction.rollout_rs_threshold": f"{1.0 / upper}_{1.0 / lower}",
        "actor_rollout_ref.model.path": cloud_path(pair["student"]),
        "actor_rollout_ref.model.use_remove_padding": True,
        "actor_rollout_ref.model.use_fused_kernels": settings["use_fused_kernels"],
        "actor_rollout_ref.model.mtp.enable": False,
        "actor_rollout_ref.actor.ppo_mini_batch_size": settings["train_batch_size"],
        "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu": 1,
        "actor_rollout_ref.actor.ppo_epochs": 1,
        "actor_rollout_ref.actor.shuffle": False,
        "actor_rollout_ref.actor.data_loader_seed": settings["seed"],
        "actor_rollout_ref.actor.use_dynamic_bsz": True,
        "actor_rollout_ref.actor.ppo_max_token_len_per_gpu": settings["ppo_max_token_len_per_gpu"],
        "actor_rollout_ref.actor.use_kl_loss": False,
        "actor_rollout_ref.actor.entropy_coeff": 0.0,
        "actor_rollout_ref.actor.optim.lr": settings["learning_rate"],
        "actor_rollout_ref.actor.optim.lr_warmup_steps": 0,
        "actor_rollout_ref.actor.optim.lr_warmup_steps_ratio": 0.0,
        "actor_rollout_ref.actor.optim.lr_decay_style": "constant",
        "actor_rollout_ref.actor.optim.weight_decay": settings["weight_decay"],
        "actor_rollout_ref.actor.optim.betas": settings["optimizer_betas"],
        "actor_rollout_ref.actor.checkpoint.save_contents": ["hf_model"],
        "actor_rollout_ref.actor.megatron.use_dist_checkpointing": False,
        "actor_rollout_ref.actor.megatron.use_mbridge": True,
        "actor_rollout_ref.actor.megatron.param_offload": True,
        "actor_rollout_ref.actor.megatron.optimizer_offload": True,
        "actor_rollout_ref.actor.megatron.tensor_model_parallel_size": runtime["actor_tp"],
        "actor_rollout_ref.actor.megatron.pipeline_model_parallel_size": runtime["actor_pp"],
        "actor_rollout_ref.actor.megatron.context_parallel_size": runtime["actor_cp"],
        "actor_rollout_ref.actor.megatron.dynamic_context_parallel": False,
        "actor_rollout_ref.actor.megatron.expert_model_parallel_size": runtime["actor_ep"],
        "actor_rollout_ref.actor.megatron.expert_tensor_parallel_size": runtime["actor_etp"],
        "actor_rollout_ref.actor.megatron.router_replay.mode": runtime["router_replay_mode"],
        "actor_rollout_ref.actor.megatron.seed": settings["seed"],
        "actor_rollout_ref.actor.megatron.override_transformer_config.recompute_granularity": "full",
        "actor_rollout_ref.actor.megatron.override_transformer_config.recompute_method": "uniform",
        "actor_rollout_ref.actor.megatron.override_transformer_config.recompute_num_layers": 1,
        "+actor_rollout_ref.actor.megatron.override_transformer_config.mtp_num_layers": 0,
        "actor_rollout_ref.rollout.name": "sglang",
        "actor_rollout_ref.rollout.tensor_model_parallel_size": runtime["rollout_tp"],
        "actor_rollout_ref.rollout.gpu_memory_utilization": settings["rollout_memory_utilization"],
        "actor_rollout_ref.rollout.n": 1,
        "actor_rollout_ref.rollout.temperature": 1.0,
        "actor_rollout_ref.rollout.top_p": 1.0,
        "actor_rollout_ref.rollout.top_k": -1,
        "actor_rollout_ref.rollout.seed": settings["seed"],
        "actor_rollout_ref.rollout.full_determinism": True,
        "actor_rollout_ref.rollout.calculate_log_probs": True,
        "actor_rollout_ref.rollout.enable_rollout_routing_replay": runtime["router_replay_mode"] == "R3",
        "actor_rollout_ref.rollout.max_model_len": settings["context_length"],
        "actor_rollout_ref.rollout.log_prob_use_dynamic_bsz": True,
        "actor_rollout_ref.rollout.log_prob_max_token_len_per_gpu": settings["ppo_max_token_len_per_gpu"],
        "actor_rollout_ref.rollout.agent.default_agent_loop": "prepared_turn_agent",
        "actor_rollout_ref.rollout.agent.num_workers": settings["train_batch_size"],
        "actor_rollout_ref.rollout.agent.agent_loop_config_path": str(agent_config),
        "actor_rollout_ref.rollout.engine_kwargs": {"sglang": engine_kwargs},
        "distillation.enabled": True,
        "distillation.nnodes": 1,
        "distillation.n_gpus_per_node": runtime["teacher_gpus"],
        "distillation.teacher_models.teacher_model.model_path": cloud_path(pair["teacher"]),
        "distillation.teacher_models.teacher_model.inference.name": "sglang",
        "distillation.teacher_models.teacher_model.inference.tensor_model_parallel_size": runtime["teacher_tp"],
        "distillation.teacher_models.teacher_model.inference.gpu_memory_utilization": (
            settings["teacher_memory_utilization"]
        ),
        "distillation.teacher_models.teacher_model.inference.max_model_len": settings["context_length"],
        "distillation.teacher_models.teacher_model.inference.engine_kwargs": {"sglang": engine_kwargs},
        "distillation.distillation_loss.loss_mode": "k1",
        "distillation.distillation_loss.use_policy_gradient": True,
        "distillation.distillation_loss.use_task_rewards": False,
        "distillation.distillation_loss.loss_max_clamp": None,
        "distillation.distillation_loss.log_prob_min_clamp": None,
        "distillation.distillation_loss.clip_ratio": settings["clip_ratio"],
        "distillation.distillation_loss.clip_ratio_low": settings["clip_ratio"],
        "distillation.distillation_loss.clip_ratio_high": settings["clip_ratio_high"],
        "ray_kwargs.ray_init.runtime_env.py_executable": sys.executable,
    }
    return ["model_engine=megatron"] + [
        f"{'++' if key.endswith('.engine_kwargs') else ''}{key}={hydra_value(value)}"
        for key, value in overrides.items()
    ]


def validate_assets(args, pair, settings):
    import pyarrow.parquet as pq

    metadata = pq.read_metadata(cloud_path(args.dataset))
    expected = args.steps * settings["train_batch_size"]
    if metadata.num_rows != expected:
        raise ValueError(f"Prepared dataset must contain exactly {expected} turn rows, got {metadata.num_rows}")
    loops = OmegaConf.load(args.agent_config)
    entries = [entry for entry in loops if entry.name == "prepared_turn_agent"]
    if len(entries) != 1 or entries[0]["_target_"] != "tests.manual.agent_opd.agent_loop.PreparedTurnAgentLoop":
        raise ValueError("Agent config must register the task's PreparedTurnAgentLoop exactly once")
    entry = entries[0]
    if entry.reasoning_parser != pair["reasoning_parser"] or entry.tool_parser != pair["loop_tool_parser"]:
        raise ValueError("Agent loop parsers differ from the selected pair registry")
    if list(entry.ratio_bounds) != list(settings["importance_ratio_bounds"]):
        raise ValueError("Agent observer ratio bounds differ from the training correction bounds")
    if validate_numerical_limits(entry.get("numerical_limits")) != validate_numerical_limits(
        settings["numerical_limits"]
    ):
        raise ValueError("Agent observer numerical limits differ from the explicit run settings")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--pair", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--agent-config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[3]
    cloud_path(args.dataset)
    if not args.dry_run:
        for path in (args.dataset, args.agent_config):
            if not path.is_file():
                raise FileNotFoundError(path)
    pair = json.loads(args.pairs.read_text())[args.pair]
    settings = json.loads(args.settings.read_text())
    if not args.dry_run:
        validate_assets(args, pair, settings)
    overrides = recipe_overrides(
        pair, settings, dataset=args.dataset, agent_config=args.agent_config,
        steps=args.steps, repository=repository,
    )
    with initialize_config_dir(version_base=None, config_dir=str(repository / "verl/trainer/config")):
        config = compose(config_name="ppo_trainer", overrides=overrides)
    if len(config.distillation.teacher_models) != 1:
        raise ValueError("The source task requires exactly one frozen teacher for each student run")
    omega_conf_to_dataclass(config.distillation)
    # Preserve lazy optional-role fields (some legitimately contain ???). They
    # are resolved by native validation for the roles actually used at launch.
    if args.output.is_relative_to(Path("/mnt/codesign-exp")):
        cloud_path(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        output.write(OmegaConf.to_yaml(config, resolve=False))
    print(json.dumps({
        "status": "PASS_HYDRA_COMPOSE", "pair": args.pair, "steps": args.steps,
        "native_distillation_config_verified": True,
        "output": str(args.output), "asset_existence_checked": not args.dry_run,
        "trainer_launched": False, "numerical_agreement_verified": False,
    }))


if __name__ == "__main__":
    main()
