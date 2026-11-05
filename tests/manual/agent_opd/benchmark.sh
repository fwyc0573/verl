#!/usr/bin/env bash
# Launch one original or exported student benchmark on an authorized GPU worker.
set -euo pipefail
python_path=${1:?Usage: benchmark.sh PYTHON WORK_DIR [benchmark.py run arguments]}
work_root=${2:?Missing worker-local work directory}
shift 2
benchmark_args=("$@")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p "$work_root"
session_dir=$(mktemp -d "$work_root/benchmark.XXXXXX")
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$session_dir"
"$python_path" -B "$script_dir/benchmark.py" server-argv "$@" --work-dir "$session_dir" \
    > "$session_dir/server-argv"
mapfile -d '' -t server_command < "$session_dir/server-argv"
setsid "${server_command[@]}" > "$session_dir/server.log" 2>&1 &
server_pid=$!
cleanup() {
    status=$?
    trap - EXIT
    if kill -0 -- "-$server_pid" 2>/dev/null; then
        kill -TERM -- "-$server_pid" 2>/dev/null || true
    fi
    for ((attempt = 0; attempt < 30; attempt++)); do
        if ! kill -0 -- "-$server_pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    kill -KILL -- "-$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    "$python_path" -B "$script_dir/benchmark.py" archive "${benchmark_args[@]}" \
        --work-dir "$session_dir" --server-log "$session_dir/server.log" || status=1
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
"$python_path" -B "$script_dir/benchmark.py" run "$@" --work-dir "$session_dir" \
    --server-log "$session_dir/server.log" --server-pid "$server_pid"
