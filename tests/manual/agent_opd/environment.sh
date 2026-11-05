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
no_proxy="$no_proxy,pypi.org,.pypi.org,files.pythonhosted.org,.pythonhosted.org,download.pytorch.org"
export no_proxy
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" ALL_PROXY="$all_proxy" NO_PROXY="$no_proxy"
curl --noproxy '*' --head --fail --silent --show-error --max-time 30 --output /dev/null \
    --write-out 'PYPI_PINNED_WHEEL_HTTP=%{http_code}\n' \
    https://files.pythonhosted.org/packages/1c/79/ffd666bee268dc27ee34ed471e43f0357f9154c93d5180381861f8673c21/tokenspeed_triton-3.9.10.post20261008-cp312-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
curl --head --fail --silent --show-error --max-time 30 --output /dev/null \
    --write-out 'GITHUB_PINNED_WHEEL_HTTP=%{http_code}\n' \
    https://github.com/verl-project/verl-wheelhouse/releases/download/deep-ep-3f601f7ac1c062c46502646ff04c535013bfca00-py3.12-torch2.13.0-cu130/deep_ep-1.2.1-cp312-cp312-linux_x86_64.whl
uv sync --frozen --extra sglang --extra megatron \
    --python /data/ycfeng/envs/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
"$UV_PROJECT_ENVIRONMENT/bin/python" -B tests/manual/agent_opd/runtime_probe.py \
    --pairs tests/manual/agent_opd/pairs.json --output "$stage/runtime-preflight.json"
bash tests/manual/agent_opd/prepare.sh
