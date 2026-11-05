#!/usr/bin/env bash
# Verify the actual source turns and native recipes without allocating GPUs.
set -euo pipefail
repo=/data/ycfeng/sota-engine/verl
python=/data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python
stage=/data/ycfeng/tmp/verl-agent-opd-20261106
job=${KUBEBRAIN_RJOB_NAME:?}
cloud=/mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/inputs/$job
records=$stage/input-preflight/$job
manifest=/data/ycfeng/steptron/.worktrees/behavior-turn-replay-step3p6/task_memory/task_2026-10-25_swe_behavior_turn_replay/evidence/glm-replay-subsets-20261104.json
parent=/data/ycfeng/steptron/.worktrees/behavior-turn-replay-step3p6/task_memory/task_2026-10-25_swe_behavior_turn_replay/evidence/swe-common-50.json
mkdir -p "$records"
cd "$repo"
export PYTHONPATH="$repo" PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for pair in glm qwen; do
    "$python" -B tests/manual/agent_opd/prepare_turns.py \
        --miles-root /data/ycfeng/sota-engine/miles --manifest "$manifest" \
        --pairs tests/manual/agent_opd/pairs.json --pair "$pair" \
        --output "$cloud/$pair-learning.parquet" --report "$records/$pair-turns.json" \
        --work-dir "$stage" --turns-per-category 20 --max-prompt-tokens 61440
done
"$python" -B - "$cloud" "$records" <<'PY'
import json
import sys
from collections import Counter
from pathlib import Path
import pyarrow.parquet as pq
from omegaconf import OmegaConf

cloud, records = map(Path, sys.argv[1:])
pairs = json.loads(Path('tests/manual/agent_opd/pairs.json').read_text())
base = json.loads(Path('tests/manual/agent_opd/settings.json').read_text())
for name, pair in pairs.items():
    table = pq.read_table(cloud / f'{name}-learning.parquet')
    qualification = table.slice(0, 8)
    counts = Counter(qualification['source_category'].to_pylist())
    if len(counts) != 4 or set(counts.values()) != {2}:
        raise ValueError('Qualification must contain two complete source turns per category')
    output = cloud / f'{name}-qualification.parquet'
    with output.open('xb') as stream:
        pq.write_table(qualification, stream)
    if not pq.read_table(output).equals(qualification):
        raise ValueError('Qualification parquet did not preserve exact prepared rows')
    agent = [{'name': 'prepared_turn_agent',
              '_target_': 'tests.manual.agent_opd.agent_loop.PreparedTurnAgentLoop',
              'reasoning_parser': pair['reasoning_parser'], 'tool_parser': pair['loop_tool_parser'],
              'ratio_bounds': base['importance_ratio_bounds'], 'numerical_limits': base['numerical_limits']}]
    OmegaConf.save(OmegaConf.create(agent), records / f'{name}-agent.yaml')
    for steps in (2, 20):
        settings = dict(base, save_directory=str(cloud / f'configuration-only-{name}-{steps}'),
                        experiment_name=f'preflight-{name}-{steps}')
        (records / f'{name}-{steps}-settings.json').write_text(json.dumps(settings, indent=2) + '\n')
print('VERL_AGENT_OPD_QUALIFICATION_INPUTS_VERIFIED', json.dumps({'pairs': list(pairs), 'rows_per_pair': 8}))
PY
for pair in glm qwen; do
    for steps in 2 20; do
        phase=learning
        if [[ "$steps" == 2 ]]; then phase=qualification; fi
        "$python" -B tests/manual/agent_opd/configure.py \
            --pairs tests/manual/agent_opd/pairs.json --pair "$pair" \
            --settings "$records/$pair-$steps-settings.json" --steps "$steps" \
            --dataset "$cloud/$pair-$phase.parquet" --agent-config "$records/$pair-agent.yaml" \
            --output "$records/$pair-$steps-recipe.yaml"
    done
done
"$python" -B /data/ycfeng/sota-engine/miles/tests/manual/agent_opd/prepare_benchmark.py \
    --parent "$parent" --output-root "$cloud/benchmark"
"$python" -B - "$cloud" "$records" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
cloud, records = map(Path, sys.argv[1:])
manifest = cloud / 'benchmark/membership.json'
receipt = {'status': 'PASS_INPUT_AND_CONFIG_PREFLIGHT', 'cloud_inputs': str(cloud),
           'membership': str(manifest), 'membership_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
           'training_started': False, 'numerical_agreement_verified': False}
(records / 'inputs.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
PY
