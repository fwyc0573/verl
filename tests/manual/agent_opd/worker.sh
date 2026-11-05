#!/usr/bin/env bash
# Run the authorized stage in the existing native environment without installing dependencies.
set -euo pipefail
set +x
repo=/data/ycfeng/sota-engine/verl
native_python=/data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python
export LD_LIBRARY_PATH="/usr/local/cuda-13.0/compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$repo"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
cd "$repo"
exec "$native_python" -B -m tests.manual.agent_opd.worker "$@"
