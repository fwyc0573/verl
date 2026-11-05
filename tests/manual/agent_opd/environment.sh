#!/usr/bin/env bash
# Materialize the repository's locked native environment on the mounted local disk.
set -euo pipefail
repo=/data/ycfeng/sota-engine/verl
stage=/data/ycfeng/tmp/verl-agent-opd-20261106
mkdir -p "$stage"
exec > >(tee -a "$stage/environment-sync.log") 2>&1
export TMPDIR="$stage"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$repo"
export UV_PROJECT_ENVIRONMENT=/data/ycfeng/envs/verl-agent-opd-megatron-sglang
export LD_LIBRARY_PATH="/usr/local/cuda-13.0/compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$repo"
set +x
proxy_script=$(curl --noproxy '*' --fail --silent --show-error --max-time 15 http://deploy.i.shaipower.com/httpproxy)
eval "$proxy_script"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" ALL_PROXY="$all_proxy" NO_PROXY="$no_proxy"
uv sync --frozen --extra sglang --extra megatron \
    --python /data/ycfeng/envs/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
"$UV_PROJECT_ENVIRONMENT/bin/python" -B tests/manual/agent_opd/runtime_probe.py \
    --pairs tests/manual/agent_opd/pairs.json --output "$stage/runtime-preflight.json"
