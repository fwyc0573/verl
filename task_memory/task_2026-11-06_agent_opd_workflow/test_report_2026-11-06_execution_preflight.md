## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record adapter CPU checks and the exact zero-GPU environment failure. |

# Ticket01 execution preflight

Scope: native workflow adapters and environment preparation. No GPU training, numerical qualification, export/reload or benchmark acceptance is claimed.

## Exact CPU checks

Working directory: /data/ycfeng/sota-engine/verl. Branch: agent-opd.

```sh
python3 -B -m unittest tests.manual.agent_opd.test_alignment -v
/data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -m unittest tests.manual.agent_opd.test_alignment -v
PYTHONPATH=/data/ycfeng/sota-engine/verl /data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B tests/manual/agent_opd/prepare_turns.py --help
bash -n tests/manual/agent_opd/environment.sh
git diff --check
```

Host Python3.10.6: six tests PASS. Existing CPU environment Python3.12.13, torch2.11.0+cu130, transformers5.19.0: six tests and dataset CLI import/help PASS. This environment is used for CPU interface checks only. Initial direct dataset-script invocation without repo PYTHONPATH failed `ModuleNotFoundError: verl`; the corrected invocation above passed.

AST parsing passed rjob_run.py, runtime_probe.py, prepare_turns.py, alignment.py, agent_loop.py, test_alignment.py and configure.py. The owning runtime agent also composed both real pair/settings entries for2/20steps through native Hydra and reloaded the four YAML outputs: PASS_HYDRA_COMPOSE, trainer_launched=False. Real dataset/parser/schema checks will be repeated with the locked interpreter.

Expected fault cases: token/version disagreement, missing version, nonfinite values, cancellation hiding absolute differences, extreme importance ratios and incomplete tolerance budgets cannot produce a numeric PASS. Actual: all six unittest cases PASS; unset tolerance yields `measured`.

## Actual environment job failure

Exact submission entrypoint: tests/manual/agent_opd/rjob_run.py with --gpus0 --replicas1 --cpus16 --memory-gb96 and command-file tests/manual/agent_opd/environment.sh. Personal auth initialized by the approved StepMind runbook before the process. Both jobs use the immutable image:

`artifactory.stepfun-inc.com/docker-public/verlai/verl@sha256:466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504`

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| Creator/source | Personal identity and current-machine mount | i-fengyicheng;100.96.128.195:/data/ycfeng:/data/ycfeng | PASS |
| Offline materialization | Every locked wheel available from image cache | deep-ep1.2.1 wheel absent; uv exited1 | FAIL |
| Interpreter selection | Mounted CPython3.12.13 | Exact mounted interpreter selected; venv created | PASS for selection only |
| Model/runtime imports | Required native packages import | Not reached | NOT RUN |
| GPU workflow/numerics | Actual native evidence | No GPU allocated | NOT RUN |

Job `exp-1106-012337-418890`, UID7182b2ad-7489-412e-83cf-159e4defa102, replica419c32a5-6ca7-4e68-9e01-8a768a8c7915, nodegpu-h800-0235. Container started2026-11-05T17:30:49Z, first error17:30:49.934Z, finished17:30:50Z, exit1/restart0; platformFailed17:30:54Z. Earlier ImagePullBackOff recovered before execution. Launcher cleanup followed the failure. Selected original logs/state/events/audits are in evidence/runtime-environment-failure.json; native Pod direct read403 is recorded as a limit.

Repair changes frozen sync from offline-only to fetching missing locked dependencies in a new zero-GPU environment job; it adds persistent installation logging and the documented worker proxy. The lock and versions are unchanged. Job `exp-1106-013411-959935` was created2026-11-06 01:34:12HKT; launcher session66632 remains alive. Result pending; this report will be updated from actual outputs.

## Second environment attempt and measured route hypothesis

Second job UID e9b3961b-3178-4be2-9363-695596a0eef6: online sync reached build of local verl, then failed fetching locked tokenspeed-triton3.9.10.post20261008 because proxy authentication was required. No native import was reached. Evidence/runtime-environment-online-failure.json preserves original error and query limits. Both audit queries timed out; they are not treated as successful empty results.

CPU host bounded HEAD checks: exact PyPI artifact directHTTP200; same request through deploy proxy timed out after CONNECT; exact GitHub deep-ep artifact direct timed out and deploy proxy returnedHTTP200; internal PyPI package index directHTTP200. Each check was read-only with15second timeout and no secret headers. These are CPU observations only.

Third command-file revision appends files.pythonhosted.org/pypi.org/download.pytorch.org to proxy bypass, retains GitHub deploy proxy, and executes two explicit pinned-artifact HEAD checks before frozen sync. This changes routing only; uv.lock and package versions are unchanged. The same zero-GPU resource/image/source command submitted exp-1106-014156-052221. Result pending.

Native observer review found and repaired completion parser propagation and premature asynchronous HF inventory reading. Six pure fault tests, Python syntax and staged whitespace checks PASS; actual Ray/Bridge/parser/trainer execution remains NOT RUN. Commit0fe1880f contains only agent_loop.py/train.py.
