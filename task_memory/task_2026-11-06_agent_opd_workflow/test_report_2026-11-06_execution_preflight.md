## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record complete Qwen underfill and verify independent 64k/128k native recipe composition. |
| 2026-11-06 | Adopt the user-selected Steptron numerical standard; record cache repair and native launch adapters. |
| 2026-11-06 | Record adapter CPU checks and the exact zero-GPU environment failure. |

# Ticket01 execution preflight

Scope: native workflow adapters and environment preparation. No GPU training, numerical qualification, export/reload or benchmark acceptance is claimed.

## Complete Qwen source-bank result and native context repair

Actual input job exp-1106-030308-851863, UID008947c3-7bc4-4fb9-9571-73b8608acb31, independently passed benchmark and GLM80/8/native2/20 configurations. Qwen failed in turns preparation: `ValueError: Insufficient verified student-length-eligible source turns`. The full-runtime forward query returned26rows belowlimit1000 and exposed the previously missing eligibility summary and traceback; an earlier14-row tail had incomplete coverage. Selected evidence: evidence/runtime-qwen-input-underfill.json.

| Category | Verified candidates checked | Over61440 | Selected | Pool exhausted |
| --- | --- | --- | --- | --- |
| control_and_thinking | 242 | 228 | 14 | true |
| control_only | 241 | 226 | 15 | true |
| thinking_only | 239 | 222 | 17 | true |
| neither | 20 | 0 | 20 | false |

No source/token/template validation exception occurred. Complete selection failed honestly; no Qwen learning/qualification/configuration or overall inputPASS was published. Duplicate source/group skip counts14/15/17/18 and zero duplicate student prompts are retained in the selected evidence. No estimate is made for unscanned neither candidates.

Both exact pinned Qwen and Frog config.json files were read through personal read-only SSH:3161bytes each, identical SHA ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670; text_config.max_position_embeddings262144, default RoPE/no scaling. New Qwen-only settings use context131072, response4096 and ppo_max_token_len_per_gpu131072. GLM settings remain65536/4096/65536. CP1 means native dynamic microbatch budget must cover a complete single sequence; TP2 does not double that budget. Existing actor/rollout/teacher topology, recomputation and precision remain unchanged.

CPU Python3.12.13 direct execution with PYTHONPATH=/data/ycfeng/sota-engine/verl used configure.py --dry-run for both models at2/20updates. All four actual Hydra compositions PASS. Reloaded fields were explicitly asserted: data.max_prompt_length61440/126976, response4096, student and teacher max_model_len65536/131072, actor train and logprob token budgets65536/131072, requested updates2/20. The two settings files differ only in context_length and ppo_max_token_len_per_gpu. bash-n prepare.sh and git diff--check PASS. Temporary composition outputs were consumed automatically. Real128k Qwen inputs and GPU construction/memory/numerics remain UNVERIFIED; Miles's historical64k/eight-turn qualification is not inherited as128k training evidence.

## Actual GLM data PASS and Qwen length rejection

Input-only job exp-1106-024352-115509 actually prepared GLM80rows,80distinct sourceUIDs,20percategory, prompt10366–57113≤61440 and exact parquet roundtrip. Report: evidence/glm-input-preflight.json. Qwen then correctly rejected a63213-token rendered source instead of truncating. Containerexit1 at02:49:39HKT/platformFailed02:49:42; exact identity/logs in evidence/runtime-qwen-input-length-failure.json. No overall inputPASS or Qwen dataset was produced.

The source adapter now selects from the same verified training bank by each student's actual complete rendered length, reusing unchanged Miles source/hash/token verification. Targeted Python3.12.13 fault checks PASS with `/data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B /data/ycfeng/tmp/verl-agent-opd-qwen-selection-regression.py` and repository PYTHONPATH:80distinct/fourclasses20, deterministic selection,61440boundary, cached original rows, duplicate-prompt replenishment, preserved original metadata, source/template exception propagation and honest underfill counts. Historical Qwen counts remain unverified until execution.

Reorganized prepare.sh independently publishes benchmark and per-pair receipts, with overall inputs.json only after allpass. bash-n/diff-check PASS. CPU Python3.12.13 executed actual inline parquet/agent/settings and realHydra composition in four flow cases: allpass exit0; Qwen turnfailure exit63 with earlier benchmark/GLMPASS; GLM20recipefailure exit42 whileQwencompletes; benchmarkfailure exit31 whilebothpairscomplete. All failure cases omit overall inputs.json and retain actual stage/exitcode. Fixture /data/ycfeng/tmp/opd-prepare-flow-1gu_80yf was consumed. These checks do not replace real Qwen preparation or GPU qualification.

## Actual repaired native runtime result

The zero-GPU job exp-1106-023143-126576 ran /data/ycfeng/tmp/verl-agent-opd-commands-20261106/environment-repair.sh using installed Python3.12.13/torch2.13.0+cu130. The FA4 backport was actually applied with the expected final source SHA. runtime_probe.py returned PASS_CPU_PREFLIGHT, failures=[]/incomplete=[]; actual megatron.bridge import and GLM47FlashBridge/Qwen35VLBridge config-only dispatch PASS. Four pinned model configurations/tokenizers/index-shard metadata and two exact vocabulary/special-token comparisons PASS. Actual CUDA/model construction/weight conversion remains NOT RUN. Retained exact reports: evidence/runtime-preflight-cpu.json and evidence/runtime-fa4-repair.json.

Actual prepare.sh then failed after its source producer reported80records: prepare_turns.py175 json.loads(line) raised `JSONDecodeError: Unterminated string starting at: line 1 column 11 (char 10)`. Container exit1 at02:38:38HKT; platformFailed02:38:40HKT. Selected identity/mount/traceback/query limits: evidence/runtime-input-jsonl-failure.json. No complete inputs.json. Producer temporary JSONL was automatically removed on failure; its exact bytes and Unicode separator counts are unavailable. The next test targets the consumer's JSONL delimiter contract; malformed physical records must continue to raise.

Targeted JSONL regression PASS under hostPython3.10.6 via an inline stdlib check executing the actual Miles writer AST and current reader AST. Three records containing U+0085/U+2028/U+2029 in prompt/history became9segments under the old splitlines reader, reproducing the same position10 Unterminated string error. Physical file iteration restored exactly3records, identical row values and unchanged original bytes. An actually malformed physical JSON record still raised JSONDecodeError. prepare_turns.py now only replaces splitlines with UTF-8 file-line iteration; no skipping or content normalization. Source compile, bash-n prepare.sh and git diff--check PASS. The actual dataset rerun is still required.

## Native optional-FA4 import repair

Fifth job installed300packages, then failed Bridge import with `cutlass.cute.core.ThrMma` AttributeError. Actual package/import/model results, terminal identity and query limits are retained in evidence/runtime-environment-bridge-failure.json. The installed MCore0.19.2 attention.py imported flash_attn.cute before checking flash-attn-4 metadata, despite this repository explicitly excluding FA4. Its FA2 package's old cute API conflicts with installed CUTLASS DSL4.6.2. TE's metadata-first detection did not require a change. CPUhost GLIBCXX failure is a separate boundary, not the worker traceback.

fa4_detection.py backports the exact metadata-first guard from [NVIDIA upstream commit90f4d5279b951a408d7bf605a24776c248357c03](https://github.com/NVIDIA/Megatron-LM/blob/90f4d5279b951a408d7bf605a24776c248357c03/megatron/core/transformer/attention.py). It accepts only active-environment Core0.19.2 and the exact original/patched file; an unknown source is refused. No package version, FA2/FA3 execution path or actual installed-FA4 unexpected exception is changed. Original whole-file SHA a019cd00a708a22237383456a7ba85bf522201c14a5b7cb0c1e4f0f12eac9837; expected patched SHA a733e2a6b5eb24e99fe4ca55a68f88bddf56ab0e5fd7ffd56a4b231c7262f5c8.

CPU13checks PASS under Python3.12.13 using inline `PYTHONPATH=/data/ycfeng/sota-engine/verl /data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -`: exact original and patched hashes, single block change, idempotence, unknown-source refusal, original missing-metadata ThrMma reproduction, repaired missing/b19/b20 import behavior, existing optional ImportError behavior and propagation of real AttributeError when FA4 is present. AST and120-column checks PASS. No persistent fixture and no host native-environment mutation occurred. Actual worker import is the next check; CPU mocks are not native qualification.

## Completed export adapter checks

Exact root checks:

```sh
/data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -m tests.manual.agent_opd.export --help
git diff --check
```

Both PASS; Python3.10 AST parsing of export.py and exact Qwen benchmark registry assertions also PASS. The owning agent executed fifteen small synthetic acceptance/fault cases using the inline entrypoint `PYTHONPATH=/data/ycfeng/sota-engine/verl /data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -` with an inline fixture (no retained standalone script), Python3.12.13/torch2.11.0+cu130. Expected: complete strict Qwen and explicitly decoder-only GLM exports can publish a receipt; missing or corrupted GLM aliases, wrong step/duplicate update sequence, wrong role, dtype/inventory/index/shard defects, unchanged weights and unfinished native fit cannot. Actual:15PASS. The fake cloud-path mapping was limited to the CPU fixture; these checks are not actual model export/reload verification. Fixture /data/ycfeng/tmp/opd-export-fixtures-8rbte95d,154files/100611bytes, was consumed and removed.

SGLang0.5.20 installed source was inspected without native imports: ExecMamba.linear_attn_prefill_backend in arg_groups/fields/exec_.py:411, allowed triton in choices.py:194–195, constructor assembly in server_args.py:527–551 and underscore-to-hyphen CLI rule in arg_utils.py:353. Qwen benchmark args now use the supported triton backend, matching training. Actual kernel execution remains NOT RUN.

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
