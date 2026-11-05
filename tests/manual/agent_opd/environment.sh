#!/usr/bin/env bash
# Materialize the repository's locked native environment on the mounted local disk.
set -euo pipefail
repo=/data/ycfeng/sota-engine/verl
stage=/data/ycfeng/tmp/verl-agent-opd-20261106
mkdir -p "$stage"
exec > >(tee -a "$stage/environment-sync.log") 2>&1
printf '\nVERL_ENVIRONMENT_JOB=%s\n' "${KUBEBRAIN_RJOB_NAME:?}"
export TMPDIR="$stage"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$repo"
export UV_PROJECT_ENVIRONMENT=/data/ycfeng/envs/verl-agent-opd-megatron-sglang
export UV_CACHE_DIR=/root/.cache/uv
export UV_LINK_MODE=copy
export LD_LIBRARY_PATH="/usr/local/cuda-13.0/compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$repo"
supplement=/data/ycfeng/tmp/verl-agent-opd-downloads-20261106/uv-cache
test -d "$supplement/archive-v0"
test -d "$supplement/wheels-v6/index"
mkdir -p "$UV_CACHE_DIR"
stat -f -c 'UV_CACHE_FILESYSTEM=%T' "$UV_CACHE_DIR"
readlink -f "$UV_CACHE_DIR"
# The worker cache filesystem rejects chmod metadata preservation. uv needs
# cache contents and links; ownership, ACLs and timestamps are not inputs.
cp -R -n --no-preserve=all "$supplement/." "$UV_CACHE_DIR/"
printf 'MERGED_PREFETCH_CACHE=%s\n' "$supplement"
set +x
proxy_script=$(curl --noproxy '*' --fail --silent --show-error --max-time 15 http://deploy.i.shaipower.com/httpproxy)
eval "$proxy_script"
no_proxy="$no_proxy,pypi.org,.pypi.org,files.pythonhosted.org,.pythonhosted.org,download.pytorch.org"
export no_proxy
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" ALL_PROXY="$all_proxy" NO_PROXY="$no_proxy"
curl --noproxy '*' --head --fail --silent --show-error --max-time 30 --output /dev/null \
    --write-out 'PYPI_PINNED_WHEEL_HTTP=%{http_code}\n' \
    https://files.pythonhosted.org/packages/1c/79/ffd666bee268dc27ee34ed471e43f0357f9154c93d5180381861f8673c21/tokenspeed_triton-3.9.10.post20261008-cp312-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
uv sync --frozen --extra sglang --extra megatron \
    --python /data/ycfeng/envs/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
"$UV_PROJECT_ENVIRONMENT/bin/python" -B tests/manual/agent_opd/fa4_detection.py
"$UV_PROJECT_ENVIRONMENT/bin/python" -B tests/manual/agent_opd/runtime_probe.py \
    --pairs tests/manual/agent_opd/pairs.json --output "$stage/runtime-preflight.json"
bash tests/manual/agent_opd/prepare.sh
