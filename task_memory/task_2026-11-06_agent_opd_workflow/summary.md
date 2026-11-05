## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record an incomplete execution checkpoint while all four GPU jobs wait for workers. |

# Agent OPD workflow: incomplete execution checkpoint

**Overall status: INCOMPLETE.** This is a continuation record, not a completion archive or numerical acceptance. Ticket01 is done. The four independent GPU frontier jobs are submitted and waiting for workers; their native platform state is Pending. Tickets02/03/06/07 are therefore BLOCKED in the planning checkpoint. Tickets04/05/08/09/10 remain unfinished.

## Requested deliverables and observed results

The task replicates the Miles agent OPD workflow in verl for GLM-4.7-Flash-Coder → GLM-4.7-Flash and FrogNano-4B-2609 → Qwen3.5-4B. Each pair requires a real two-update qualification followed by a separate fresh run with20successful updates, exact final HF export, new-process reload and generation, and original/updated SWE evaluations of20questions ×4seeds. The total required grading population is320valid outcomes. Infrastructure failures are missing outcomes, not valid zero scores.

- **Task and tickets:** [requirements.md](requirements.md), [plan.md](plan.md), and ten files in [tickets/](tickets/) record scope, decisions, acceptance criteria and component dependencies. The source task is `/data/ycfeng/sota-engine/miles/task_memory/task_2026-11-05_agent_opd_warmup/`; its results are not treated as verl results.
- **Environment, data and configuration:** Actual zero-GPU workers verified the pinned native environment, both80-row training datasets with20turns per source category, the first8qualification rows with2per category, and actual2/20-update recipes. Source UID/order and exclusion checks passed. Qwen uses its own131072context/token budget after the61440prompt-budget scan actually underfilled; GLM retains65536context. Actual Qwen80prompt lengths are11430–67951. Its first8qualification rows have a maximum48129, so the qualification alone cannot verify GPU behavior above64k.
- **Train/inference agreement:** The user-selected Steptron Q59 standard is adopted: native pack MAE and global token MAE must each be≤0.03 for every input/completion population on all loss-eligible tokens before TIS, using identical actual student weights, tokens, positions, masks and probability definition. p95/p99/max, signed error, importance-ratio outliers and K3 are diagnostic. Structural mismatches block acceptance. No actual GPU numerical comparison or optimizer update has been observed.
- **Benchmark execution:** The earlier Qwen original job actually loaded SGLang TP2 and returned model information, then all four first-question seeds failed with sandbox HTTP401. The literal unresolved `${SESSION_ROUTER_USER_TOKEN}` was the observed cause. The smallest child-environment repair uses the already supplied token and passed12real native-configuration child checks. The new GPU retry has not yet run, so repaired live authentication remains unverified. Valid SWE outcomes remain0.
- **Code and publication:** Reusable workflow scripts and configuration are in [tests/manual/agent_opd/](../../tests/manual/agent_opd/). Work is on the new `agent-opd` branch of `https://github.com/fwyc0573/verl.git`. Each verified code step and selected evidence has been committed and pushed; the checkpoint commit is also pushed and checked against the remote head. No upstream PR was opened. Unrelated `.serena/` remains untouched.
- **Cleanup:** Consumed duplicate caches/proofs of7,642,059,117bytes, the subsequently consumed native wheel cache of1,472,526,489bytes, selected raw RCA logs, and the later standalone uv/offline fixtures of60,735,741bytes have recorded cleanup evidence. Active model inputs, the installed environment, launchers and still-needed artifacts are retained. Final run/checkpoint/benchmark cleanup is pending its real consumers.

## Current GPU frontier

All four jobs were Pending with reason `RJob is queuing`, no replicas, and0allocated GPUs at04:44:49HKT on2026-11-06. Total requested:30H800 GPUs. The four launcher sessions were independently polled and remained alive before this checkpoint. Exact fresh selected status is retained in [evidence/checkpoint-gpu-status.json](evidence/checkpoint-gpu-status.json).

| Ticket | Job | RJob UID | GPUs | Launcher session |
| --- | --- | --- | --- | --- |
| 02 | exp-1106-030133-940211 | b6976435-4e8a-4099-8777-800a18db25a1 | 2×8 | 86165 |
| 03 | exp-1106-033627-955641 | 9ad17773-2d4e-4b21-8dc2-2150ab8a6f85 | 1×8 | 13885 |
| 06 | exp-1106-030308-839669 | f74fa974-ea86-4149-a823-3276ce493f8b | 1×4 | 41495 |
| 07 | exp-1106-033246-436787 | f5c97c61-7868-44f6-8a74-34ab529bd6b2 | 1×2 | 30922 |

The four jobs retain personal creator `i-fengyicheng`, H800/codesign, the pinned company image and the current-machine NFS mount. Keep their local launchers alive. Do not duplicate submissions. A bounded capacity check found no additional H200 non-preemptible headroom under the configured32GPU limit; physical free H800 capacity remains UNKNOWN. No other task's jobs were controlled. Aggregate evidence is in [evidence/capacity-wait.json](evidence/capacity-wait.json).

## Continuation route

1. Re-read requirements, plan, progress and exact current job/UID/replica state. Monitor the four existing jobs in parallel. On Starting/Running inspect actual business outputs; on failure retain the initiating native error before changing anything. Do not infer progress from a stale snapshot.
2. For each model, verify both real optimizer updates, nonzero finite gradients, frozen-teacher scoring, version-consistent decode/prefill/trainer comparisons, GLM R3 where applicable, actual changed weights and final two-step publication. Numerical agreement and workflow acceptance remain separate gates. Preserve qualification HF output until the real weight-change witness has consumed it.
3. Only after the same-model qualification passes, submit its already prepared `learning20-glm.sh` or `learning20-qwen.sh` from `/data/ycfeng/tmp/verl-agent-opd-commands-20261106/`. Those command files are currently unsubmitted. Start from the original student, not qualification weights. Require exactly20successful updates and the verified final export.
4. Once a verified final export exists, start that model's updated benchmark immediately. Its new SGLang process, identity check and actual generation provide the reload evidence for04/05. Original benchmark completion is required for final comparison, not for starting updated scoring. Require80valid outcomes per model/version and report avg@4 with the fixed denominator.
5. Consume each artifact after its final dependent, finalize ticket statuses and English completion archive, and push the verified results to the personal branch. Do not close the task while any numerical, update, export/reload, scoring or final cleanup gate is open.

## Evidence and verification limits

Exact commands, Python/runtime versions, native errors, expected/actual results and selected evidence paths are in [test_report_2026-11-06_execution_preflight.md](test_report_2026-11-06_execution_preflight.md) and [test_report_2026-11-06_native_workflow.md](test_report_2026-11-06_native_workflow.md). [progress.md](progress.md) records the implementation trace and check-progress correction that removed unnecessary benchmark dependency edges. CPU fixtures, source checks, successful preparation, server readiness and queued jobs do not establish GPU workflow or numerical acceptance.
