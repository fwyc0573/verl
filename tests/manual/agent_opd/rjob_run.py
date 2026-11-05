"""Submit one authorized verl test stage through the personal Python RJob backend.

Initialize credentials according to the StepMind runbook before invoking this
entrypoint. The launcher remains alive until the submitted workload terminates.
"""

import argparse
import json
import os
import shlex
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--command-file", type=Path, required=True)
    parser.add_argument("--gpus", type=int, required=True)
    parser.add_argument("--replicas", type=int, required=True)
    parser.add_argument("--cpus", type=int, required=True)
    parser.add_argument("--memory-gb", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--sandbox-auth", action="store_true", help="Forward existing native benchmark credentials")
    args = parser.parse_args()
    if os.environ.get("STEPMIND_BACKEND") != "rjob":
        raise RuntimeError("Initialize STEPMIND_BACKEND=rjob before submission")
    for key in ("BRAINPP_ACCESS_KEY", "BRAINPP_SECRET_KEY", "KUBEBRAIN_WORKSPACE_NAME"):
        if not os.environ.get(key):
            raise RuntimeError(f"Missing required submission environment: {key}")
    command_file = args.command_file.resolve(strict=True)
    repository = Path(__file__).resolve().parents[3]
    source = repository.parents[1]
    if not command_file.is_relative_to(source):
        raise ValueError("The worker command must be in the mounted local source")
    from steptron.exp.base_exp import ResourceConfig
    from steptron.utils.stepmind import spawn_tasks

    os.chdir(source)
    os.environ["EXP_ID"] = args.name
    sandbox_env = {}
    if args.sandbox_auth:
        for key in ("AK_BASEMIND", "SK_BASEMIND"):
            if not os.environ.get(key):
                raise RuntimeError(f"Missing native sandbox credential: {key}")
        if not (os.environ.get("SR_USER_TOKEN") or os.environ.get("SESSION_ROUTER_USER_TOKEN")):
            raise RuntimeError("Missing native session-router token")
        sandbox_env = {
            key: os.environ[key]
            for key in ("AK_BASEMIND", "SK_BASEMIND", "SR_USER_TOKEN", "SESSION_ROUTER_USER_TOKEN")
            if os.environ.get(key)
        }
    cfg = ResourceConfig(
        cpu=args.cpus,
        gpu=args.gpus,
        mem_gb=args.memory_gb,
        replica=args.replicas,
        image=args.image,
        positive_tags=["H800"],
        extra_requirements=[],
        mounts=["juicefs+s3://oss.i.shaipower.com/codesign-exp:/mnt/codesign-exp"],
        envs=sandbox_env,
        command="{COMMAND}",
        preemptible=False,
        task_specs={"default": {"is_critical": True}},
    )
    if args.gpus == 0:
        cfg.custom_resources = []
    print(json.dumps({
        "stage": args.name, "image": args.image,
        "gpus_per_replica": args.gpus, "replicas": args.replicas,
        "source": str(source), "command_file": str(command_file),
    }), flush=True)
    workers = spawn_tasks(
        cfg,
        command="bash " + shlex.quote(str(command_file)),
        charged_group="codesign",
        use_image=True,
        code_mount_point=str(source),
    )
    print("VERL_STAGE_TERMINAL", workers.rjob.meta.name, workers.poll(), flush=True)


if __name__ == "__main__":
    main()
