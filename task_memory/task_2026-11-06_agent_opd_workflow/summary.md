## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Resume after actual qualification failures and partial native benchmark outcomes. |
| 2026-11-06 | Record an incomplete execution checkpoint while all four GPU jobs wait for workers. |

# Agent OPD workflow: incomplete execution checkpoint

**Overall status: INCOMPLETE.** This is a continuation record, not a completion archive or numerical acceptance. Both initial qualifications actually failed before training at the native teacher context guard. The next attempts passed that guard and initialized native models, then failed before sampling because batch4 was split among8agent workers. Both scoped fixes have now passed native CPU regressions and are pushed asffb83e83; new same-resource qualifications are submitted. Original GLM/Qwen benchmarks are running and have partial valid native outcomes. Tickets04/05/08/09/10 remain unfinished. The earlier all-Pending checkpoint is historical.

## Requested deliverables and observed results

The task replicates the Miles agent OPD workflow in verl for GLM-4.7-Flash-Coder → GLM-4.7-Flash and FrogNano-4B-2609 → Qwen3.5-4B. Each pair requires a real two-update qualification followed by a separate fresh run with20successful updates, exact final HF export, new-process reload and generation, and original/updated SWE evaluations of20questions ×4seeds. The total required grading population is320valid outcomes. Infrastructure failures are missing outcomes, not valid zero scores.

- **Task and tickets:** [requirements.md](requirements.md), [plan.md](plan.md), and ten files in [tickets/](tickets/) record scope, decisions, acceptance criteria and component dependencies. The source task is `/data/ycfeng/sota-engine/miles/task_memory/task_2026-11-05_agent_opd_warmup/`; its results are not treated as verl results.
- **Environment, data and configuration:** Actual zero-GPU workers verified the pinned native environment, both80-row training datasets with20turns per source category, the first8qualification rows with2per category, and actual2/20-update recipes. Source UID/order and exclusion checks passed. Qwen uses its own131072context/token budget after the61440prompt-budget scan actually underfilled; GLM retains65536context. Actual Qwen80prompt lengths are11430–67951. Its first8qualification rows have a maximum48129, so the qualification alone cannot verify GPU behavior above64k.
- **Train/inference agreement:** The user-selected Steptron Q59 standard is adopted: native pack MAE and global token MAE must each be≤0.03 for every input/completion population on all loss-eligible tokens before TIS, using identical actual student weights, tokens, positions, masks and probability definition. p95/p99/max, signed error, importance-ratio outliers and K3 are diagnostic. Structural mismatches block acceptance. No actual GPU numerical comparison or optimizer update has been observed.
- **Benchmark execution:** The earlier Qwen original job failed its first four seeds with sandbox HTTP401 because `${SESSION_ROUTER_USER_TOKEN}` remained unresolved. The smallest existing-token environment repair has now passed real sandbox/tool/generation/grader execution. At13:38:17HKT the original Qwen run has38/80valid outcomes (29resolved/9unresolved), and GLM has10/80 (5resolved/5unresolved). Three new Qwen context-overflow episodes and four historical auth failures remain missing. Both healthy original jobs continue; no full benchmark or avg@4 acceptance is claimed.
- **Code and publication:** Reusable workflow scripts and configuration are in [tests/manual/agent_opd/](../../tests/manual/agent_opd/). Work is on the new `agent-opd` branch of `https://github.com/fwyc0573/verl.git`. Each verified code step and selected evidence has been committed and pushed; the checkpoint commit is also pushed and checked against the remote head. No upstream PR was opened. Unrelated `.serena/` remains untouched.
- **Cleanup:** Consumed duplicate caches/proofs of7,642,059,117bytes, the subsequently consumed native wheel cache of1,472,526,489bytes, selected raw RCA logs, and the later standalone uv/offline fixtures of60,735,741bytes have recorded cleanup evidence. Active model inputs, the installed environment, launchers and still-needed artifacts are retained. Final run/checkpoint/benchmark cleanup is pending its real consumers.

## Actual execution and current frontier

The initial GLM qualification reached both8H800 ranks, verified its real8-row input, initialized Ray/data loaders, then failed at `61440 + 4096 + 1 = 65537 > teacher65536`. Rank0 exited1 at08:24:10HKT; rank1 was subsequently stopped by the job failure policy. Qwen qualification reached8H800 and failed at `126976 + 4096 + 1 = 131073 > teacher131072`, exiting1 at08:04:36HKT. Neither reached a successful update, numerical observation or HF2 weight-change witness.

The scoped repair reserves one native teacher scoring token in the existing preparation/recipe formula: prompt caps61439/126975 with context65536/131072 and response4096 retained. Actual native dataclass validation and unchanged80/8 input identity both passed before the new submissions. The existing agent.num_workers is also derived from train_batch_size:4 workers for the4-prompts/n1 batch. Actual DataProto chunk/concat reproduced the old failure and preserved every token/UID with the new split for all four recipes. The original benchmarks do not wait for these repairs. Selected partial outcomes and source hashes are retained in [evidence/original-benchmarks-partial-1338.json](evidence/original-benchmarks-partial-1338.json).

| Ticket | Job | RJob UID | GPUs | Observed state |
| --- | --- | --- | --- | --- |
| 02 | exp-1106-140852-369748 | b20d2692-2e74-4b68-a2b2-6b3cd0e29cb4 | 2×8 | Starting at 14:11:01 HKT |
| 03 | exp-1106-140853-397005 | f400952c-ee74-4b55-8f2b-26828705a417 | 1×8 | Starting at 14:11:01 HKT |
| 06 | exp-1106-030308-839669 | f74fa974-ea86-4149-a823-3276ce493f8b | 1×4 | Running |
| 07 | exp-1106-033246-436787 | f5c97c61-7868-44f6-8a74-34ab529bd6b2 | 1×2 | Running |

The jobs retain personal creator `i-fengyicheng`, H800/codesign, the pinned company image and current-machine NFS. Keep the healthy original launchers41495/30922 alive and preserve their slots. Fresh qualification launchers96491/24467 must also remain alive; their new identities/resources/currentNFS/RDMA were actually verified. Old failed identities were re-read before the retries. The04:44status receipt and04:33capacity check remain historical evidence, not current scheduling or benchmark status. No other task's jobs were controlled.

## Continuation route

1. Observe the already submitted fresh qualifications and both healthy originals in parallel. The existing Miles SGLang adapter commit72fe633d76b8ed3315081a81b36678257dd6de81 maps exact context overflow to native history handling/autosubmit and normal trajectory saving. After the current Qwen original run terminates, use its existing same2GPU command/outputroot to recover actual missing slots only; preserve valid outcomes and all old failures. No new context, selector flag or exception handler is needed. See evidence/qwen-benchmark-context-recovery.json.
2. For each model, verify both real optimizer updates, nonzero finite gradients, frozen-teacher scoring, version-consistent decode/prefill/trainer comparisons, GLM R3 where applicable, actual changed weights and final two-step publication. Numerical agreement and workflow acceptance remain separate gates. Preserve qualification HF output until the real weight-change witness has consumed it.
3. Only after the same-model qualification passes, submit its already prepared `learning20-glm.sh` or `learning20-qwen.sh` from `/data/ycfeng/tmp/verl-agent-opd-commands-20261106/`. Those command files are currently unsubmitted. Start from the original student, not qualification weights. Require exactly20successful updates and the verified final export.
4. Once a verified final export exists, start that model's updated benchmark immediately. Its new SGLang process, identity check and actual generation provide the reload evidence for04/05. Original benchmark completion is required for final comparison, not for starting updated scoring. Require80valid outcomes per model/version and report avg@4 with the fixed denominator.
5. Consume each artifact after its final dependent, finalize ticket statuses and English completion archive, and push the verified results to the personal branch. Do not close the task while any numerical, update, export/reload, scoring or final cleanup gate is open.

## Evidence and verification limits

Exact commands, Python/runtime versions, native errors, expected/actual results and selected evidence paths are in [test_report_2026-11-06_execution_preflight.md](test_report_2026-11-06_execution_preflight.md) and [test_report_2026-11-06_native_workflow.md](test_report_2026-11-06_native_workflow.md). [progress.md](progress.md) records the implementation trace and check-progress correction that removed unnecessary benchmark dependency edges. CPU fixtures, source checks, successful preparation, server readiness and queued jobs do not establish GPU workflow or numerical acceptance.
