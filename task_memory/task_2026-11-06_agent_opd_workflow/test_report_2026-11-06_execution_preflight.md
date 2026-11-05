## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Adopt the user-selected Steptron numerical standard; record cache repair and native launch adapters. |
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


## Fourth environment stage prerequisites and adapter checks

The third worker route check failed before sync: exact PyPI wheel directHTTP200, GitHub through proxy407, containerexit22/restart0. Selected exact evidence: evidence/runtime-environment-route-failure.json. The fourth stage was not another network-route retry: CPU host first prefetched all five original native wheels and validated complete cp-a cache merging using uv0.11.16 frozen/offline install. Result PASS, prepare0.59ms/install605ms; five exact versions, no CUDA import. Receipt evidence/runtime-native-wheel-prefetch.json records extracted file hashes, absent upstream wheel ZIP hashes and consumed-cache cleanup. Preserved cache1,472,510,706bytes; consumed duplicates/proofs7,642,059,117bytes. No lock/version change.

```sh
python3 -B -m unittest discover -s tests/manual/agent_opd -p test_alignment.py -v
bash -n tests/manual/agent_opd/benchmark.sh tests/manual/agent_opd/worker.sh tests/manual/agent_opd/environment.sh
python3 -B tests/manual/agent_opd/benchmark.py run --help
PYTHONPATH=/data/ycfeng/sota-engine/verl /data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B tests/manual/agent_opd/worker.py --help
/data/ycfeng/envs/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12 -B tests/manual/agent_opd/prefetch.py --help
```

All above PASS. AST PASS for worker.py, benchmark.py and rjob_run.py. Worker direct script without repository PYTHONPATH failed import tests, then passed with worker.sh's explicit environment; host3.10 prefetch failed missing tomllib, then exact mounted3.12 CLI passed. These are interpreter/interface constraints, not hidden model failures. Worker agent's lifecycle/fault fixtures and benchmark agent's synthetic 80-outcome/resume/failure checks passed; all remain CPU/mock validation without a live native engine, sandbox or grader outcome.

Fourth stage exact submission: rjob_run.py --image artifactory.stepfun-inc.com/docker-public/verlai/verl@sha256:466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504 --command-file /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/environment.sh --gpus0 --replicas1 --cpus16 --memory-gb96 --name verl-agent-opd-env-cache-20261106d. Job exp-1106-015912-607567 created2026-11-06 01:59:12HKT; launcher19002 remains alive. Actual environment/input result pending.

Numerical acceptance is now source-backed by user steering: Steptron Q59 requires native pack MAE and global token MAE≤0.03 per input/completion population; tails/K3 only diagnostic. No numerical runtime result has yet been measured or accepted in this task. Code adoption is independently in progress.


Fourth worker FAILED before uv: exact cp metadata preservation errors, containerexit1/restart0, platform18:03:56Z. This does not invalidate the CPU five-wheel offline install proof; it shows target filesystem metadata behavior differs. Selected evidence runtime-environment-copy-failure.json records original logs and unknown mount type. Next command uses cp-R-n --no-preserve=all and reports target filesystem; expected contents/links copied without permission-preservation operations, then actual uv/import/data gates.

Native evaluator import PASS in existing Python3.10.20 with cwd=/data/ycfeng/tmp and PYTHONPATH=/data/ycfeng/steptron/.worktrees/step3p6-native-eval-1015z:/data/ycfeng/steptron:/data/ycfeng/steptron/.worktrees/step3p6-native-eval-1015z/third_party/swe-agents/src:/data/ycfeng/steptron/.worktrees/step3p6-native-eval-1015z/third_party/step_align. Actual Miles native_benchmark.py, pipeline and scorer imported; no sandbox call. The prior stdin check from verl cwd failed due local tests precedence, corrected by explicit cwd/path used for source import inspection.


## Adopted numerical contract regression checks

```sh
python3 -B -m unittest discover -s tests/manual/agent_opd -p test_alignment.py -v
/data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -m unittest discover -s tests/manual/agent_opd -p test_alignment.py -v
```

Expected11cases cover MAE-only acceptance, diagnostic tails/K3, overflow-safe JSON, exact tokens/version, missing inputs, unsupported packing and a failed short input hidden by a low global token mean. Actual11/11PASS onPython3.10.6 and3.12.13. Direct function checks of train aggregation/AgentLoop rescore and four nativeHydra compositions also PASS in the existing CPU environment. Full-support probability semantics are mandatory. Source rationale: StepTron ppo_trainer.py2173–2180 uses mean(pack MAE), rlhf.py496 averages time/DP; current verl whole-row packing with CP1/nonDCP permits a strict max(per-input MAE) upper bound. Physical pack boundaries are explicitly unobserved; no tail/K3 threshold was introduced.

Fifth zero-GPU stage uses the same exact resource/image/source contract with name verl-agent-opd-env-copy-20261106e, job exp-1106-020650-487444, launcher65336. It changes only cache copy metadata behavior and diagnostic identity/filesystem output. Result pending.


Benchmark scheduling correction: source Miles uses four fixed seed streams; measured historical first-question generation3738.97/4053.83/4095.01seconds plus grading107–114seconds explains the cost of serial execution. Adapter now joins four concurrent q0 results before advancing, then each seed executes q1..19 in order. SGLang max-running-requests derives from the frozen seed count4. No additional scheduler/CLI flags; per-attempt locks, valid-result reuse and unknown-active preservation remain. CPU mock checks PASS for observed maxconcurrency4, no same-seed overlap, q0 gate, full resume0newattempts, missing-only77, known-active preservation and local-child interruption under3seconds despite21600second attempt timeout. Only benchmark.py changed; no live grader result claimed.


Decoder-only configuration check: pinned MegatronBridge0.6.2 GLM47 provider takes HF num_nextn_predict_layers and defaults MTP loss scaling0.3. The model mtp.enable=False alone does not clear that provider field for GLM. The recipe now explicitly freezes model.mtp.enable=False and existing override_transformer_config.mtp_num_layers=0 for both pairs, matching the source decoder-only objective through the existing override mechanism. The first Hydra composition rejected a missing struct key; using its documented + addition syntax (also used by the repo's Qwen3.8/27B example) resolved it. Actual GLM/Qwen×2/20 Hydra compose and assertions PASS under CPU Python3.12.13. No core module, interface or loss implementation changed; actual provider construction/export still requires native execution.
