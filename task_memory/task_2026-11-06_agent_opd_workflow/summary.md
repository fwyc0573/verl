## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record Qwen actual two-update and numerical PASS; preserve incomplete HF2/learning/benchmark gates. |
| 2026-11-06 | Distinguish GLM numerical and native memory failures; record current Qwen execution. |
| 2026-11-06 | Record current GLM qualification, Qwen old-logprob OOM and exact old-log cleanup. |
| 2026-11-06 | Resume after actual qualification failures and partial native benchmark outcomes. |
| 2026-11-06 | Record an incomplete execution checkpoint while all four GPU jobs wait for workers. |

# Agent OPD workflow: paused execution checkpoint

**Status: PAUSED / INCOMPLETE, explicitly requested by the user on 2026-11-06.** Training and evaluation have stopped. The requested artifact/smoke cleanup is verified complete. This record preserves observed results and continuation requirements; it does not authorize a resume or declare full workflow acceptance.

## Requested scope and publication

Replicate the Miles agent OPD workflow in verl for GLM-4.7-Flash-Coder → GLM-4.7-Flash and FrogNano-4B-2609 → Qwen3.5-4B. Each pair requires a real two-update qualification, a separate fresh20-successful-update run, exact final HF export, new-process reload/generation, and original/updated SWE evaluation of20questions ×4seeds. The final grading population is320valid outcomes; infrastructure failures remain missing. Requirements, the dependency plan and ten tickets are in this task directory.

Reusable code/configuration remains in [tests/manual/agent_opd/](../../tests/manual/agent_opd/). All verified work and this pause record are published on the personal `agent-opd` branch at `https://github.com/fwyc0573/verl.git`, with a normal push and independent remote-SHA check. No upstream PR was opened. Unrelated `.serena/` is untouched.

## Observed results before the pause

- **Ticket01: PASS.** Actual workers verified the pinned native environment, both80-row training datasets with20per source category, first8qualification rows, actual2/20recipes, source identity/order/exclusions and frozen benchmark membership. Qwen80prompt lengths are11430–67951; qualification only reaches48129, so it does not prove GPU training above64K.
- **Ticket02: incomplete.** Previous GLM qualification144604-954702 has real step1 numerical FAIL: global token MAEs0.0390841902/0.0310881366/0.0382872158 exceed0.03. It later failed under host memory pressure with0verified successful updates. The next original-weight FP32/fused-head and1000000Mi-per-replica candidate153147-652892 was stopped while Pending, before any new numerical or capacity result.
- **Ticket03: numerical/update subgates PASS; full qualification incomplete.** Qwen150433-589683 completed2verified native optimizer updates, with finite loss/grad and positive grad norm. Step1 version0 global MAEs(decode/prefill,decode/trainer,prefill/trainer)=0.0045300183/0.0050332894/0.0052872581; step2 version1=0.0096232827/0.0111447289/0.0107622501. All outer comparisons pass; every per-input native-pack bound≤0.03. Physical pack means remain null/unobserved. Token IDs, positions, masks, independent prefill and reported versions match. Final version2 publication follows the awaited native update control flow; there is no subsequent version2 numerical observation or independent live checksum. See [selected business evidence](evidence/qwen-fused-qualification-business.json).
- **HF2 remains unverified and is now retired.** Qwen wrote2HF shards/9,078,620,224B bound to native step2. Header observations show738original versus723export tensors and48F32→BF16 changes. Pinned native MTP-disabled/BF16 mappings explain candidate scope/dtype behavior but were not accepted against a complete actual inventory/value witness. The0GPU checker153941-344108 failed at Git dubious ownership before its tensor checks ran. No repair/retry was made during the pause. HF2 was then deleted under the explicit cleanup instruction; qualification03 cannot be closed from optimizer/manifest receipts alone.
- **Tickets04/05/08/09: not executed.** No fresh20 learning run or updated-model benchmark was submitted.
- **Tickets06/07: partial, stopped.** Last pre-pause business snapshot: GLM17/80valid(11resolved/6unresolved), Qwen52/80(39resolved/13unresolved). These are dated partial counts, not final stop-time totals or accepted avg@4. Frozen inputs, existing valid grader results, identities and trajectories remain for unchanged missing-only continuation. Historical auth/context infrastructure failures remain missing.

## Pause and cleanup evidence

The prescribed creator-checked `rjob_stop.sh` stopped these exact personal jobs:

| Workload | Exact job | Observed terminal state |
| --- | --- | --- |
| GLM qualification | exp-1106-153147-652892 | Stopped15:45:09HKT; never started |
| GLM original benchmark | exp-1106-030308-839669 | Stopped15:45:45HKT |
| Qwen original benchmark | exp-1106-033246-436787 | Stopped15:45:43HKT |
| HF2 value checker | exp-1106-153941-344108 | Failed15:43:19HKT, before pause stop |

All known workload launchers and observers exited. Original replicas are Stopped, but stale running containerStatus snapshots do not establish exact container exit times. The first stop attempt failed its first API read with SSL EOF and performed no action; restoring the documented proxy environment enabled the same-script retry. Exact UIDs/actions/states are retained in [pause job terminals](evidence/user-pause-job-terminals.json) and [stop actions](evidence/user-pause-stop-actions.json).

The cleanup-only normal0GPU job `exp-1106-154737-250834` / UID`dde47c66-2903-4bce-9329-7792fc2fb296` completed actual container exit0 at15:47:50HKT/platformSucceeded15:47:53. Nine exact terminal qualification identities were checked before deletion. It removed45files/9,102,170,079logicalbytes and32emptydirectories, including HF2 checkpoints and consumed raw qualification logs. All deletion candidates are absent. It preserved892files/362,228,155B by size and mtime, including partial benchmark results, frozen inputs and qualification observations. See [cloud cleanup receipt](evidence/user-pause-cloud-cleanup.json) and [native platform/worker evidence](evidence/user-pause-cloud-cleanup-platform.json).

Host cleanup removed307files/7,691,530logicalbytes: consumed smoke/regression outputs, stale rendezvous/recipes, raw/duplicate downloads, disposable repair scripts and4ignoredPython caches. All candidate paths are absent. Seven small command scripts and detailed cleanup manifests remain for audit/continuation; tracked code, shared original models/data and installed environment are retained. No permissions were changed. Physical reclaimed capacity is unverified. See [host cleanup receipt](evidence/user-pause-host-cleanup.json) and [exact commands and results](test_report_2026-11-06_pause_cleanup.md).

## Continuation after explicit user resume

1. Re-read requirements, plan, progress and retained evidence. Restore an actual Qwen export and verify exact pinned MTP scope/dtype behavior plus a changed value in a direct-mapped same-dtype weight. Casting and zero-centered normalization roundtrips cannot count as learning. Keep strict20 export verification distinct from the two-update qualification.
2. Re-submit the original-weight GLM precision/capacity qualification only after resume. Preserve fixed numerical thresholds, model/input identities, native R3 and the recorded hypothesis. Capacity recovery cannot substitute for numerical PASS.
3. Resume the original benchmarks through their unchanged commands/output roots using native missing-only behavior. Preserve every valid grade; do not replace infrastructure failures with valid zero scores.
4. Only after same-model qualification passes, start its prepared fresh20 from original weights. A verified20export releases updated scoring immediately, sharing new-process reload evidence. Require complete80valid outcomes per model/version before final comparison.
5. Keep the task paused until new user steering. Ticket10's requested pause cleanup passes, while complete workflow acceptance and final delivery remain open.
