## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Verify user-requested task pause, exact job stops, cloud checkpoint/log cleanup and local smoke/cache cleanup. |

# User-requested pause and cleanup verification

## Request, scope and expected result

The user requested a temporary task pause and cleanup of existing artifacts/smoke files to avoid disk use. Stop current task jobs, preserve compact evidence/continuation state, remove task-owned disposable files, verify exact candidate absence and retained-file metadata, and push the record. Shared original models/data/environment and unrelated files are outside deletion scope. This is cleanup acceptance, not full OPD workflow acceptance.

## Environment and commands

- Submission host/current source: kun-workspace-vgen2, `/data/ycfeng/sota-engine/verl`, branch`agent-opd`; cleanup launched from source`a851bcbb1c47fffbf674b4f701e831cc76986e0a`.
- Personal StepMind Python RJobBackend, creator`i-fengyicheng`, charged_group`codesign`; current local NFS source`/data/ycfeng` and canonical cloud mount. Only `/mnt/codesign-exp/ycfeng` was accessed by workers.
- Image: `artifactory.stepfun-inc.com/docker-public/verlai/verl@sha256:466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504`.
- Host cleanup: Python3.10.6; first unprivileged attempt failed on the first root-owned file with zero deletions. Identical scoped preflight/deletion ran through existing passwordless local sudo, without chmod/chown. Worker cleanup used the pinned image's`python3`standard library; its exact Python patch version was not sampled. Submission interpreter:`/data/ycfeng/tmp/stepmind-env/bin/python`.

Prescribed stop command, after the documented proxy environment was established:

```bash
bash /data/ycfeng/steptron/playground/users/ycfeng/tools/rjob_stop.sh   --creator i-fengyicheng   --reason "User requested temporary pause and task-owned artifact/smoke cleanup on 2026-11-06"   exp-1106-153147-652892 exp-1106-030308-839669   exp-1106-033246-436787 exp-1106-153941-344108
```

Cleanup submission used the existing adapter (credentials loaded through the established personal-auth route, never written to artifacts):

```bash
/data/ycfeng/tmp/stepmind-env/bin/python -u -B   /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/rjob_run.py   --image artifactory.stepfun-inc.com/docker-public/verlai/verl@sha256:466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504   --command-file /data/ycfeng/tmp/verl-agent-opd-commands-20261106/pause-cleanup-cloud.sh   --gpus 0 --replicas 1 --cpus 4 --memory-gb 8   --name verl-user-pause-cleanup-20261106
```

Worker deletion scope was each exact terminal qualification's`logs`directory and only Qwen589683`checkpoints`. All nine names, actual UIDs, personal creator and terminal phases were captured before cleanup. The worker checked normal canonical resolution, no symlinks, regular file types, size/mtime and exactHF2shard count/bytes. It wrote the complete candidate/retained manifest before deleting files, removed only empty target directories, then checked candidate absence and every retained size/mtime.

Host commands:

```bash
sudo -n python3 -B /data/ycfeng/tmp/verl-agent-opd-cleanup-audit-20261106/cleanup-host-phase1.py
sudo -n python3 -B /data/ycfeng/tmp/verl-agent-opd-cleanup-audit-20261106/cleanup-host-phase2.py
```

Phase1 checked the pinned read-only audit manifest and exact device/inode/size/mtime, excluded tracked code and still-needed command/download roots, then removed consumed runtime/regression/rendezvous/cache entries. Phase2 verified selected evidence hashes in the durable task directory, wrote a fresh exact manifest, checked file identity and removed consumed raw/duplicate downloads plus disposable repair/smoke scripts. Seven small continuation/cleanup commands remain.

## Actual results

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Personal job identity before control | Exact names/UIDs/creator | All4refreshed15:44:19HKT; creator`i-fengyicheng` | PASS |
| Stop active task jobs | Three stopped; already-ended checker untouched | GLMqualificationStopped15:45:09; QwenoriginalStopped15:45:43; GLMoriginalStopped15:45:45; checkeralreadyFailed | PASS |
| Launcher/observer lifecycle | No continued workload/observer | Known3GPUlaunchers returned terminalstopped/exit0; allsoleobservers exited; cleanup launcher exit0 | PASS |
| Cleanup worker identity | Normal0GPU/currentmount/pinnedimage | exp-1106-154737-250834, UIDdde47c66-2903-4bce-9329-7792fc2fb296,0GPU4CPU8000Mi | PASS |
| Native cleanup termination | Worker marker and actual exit0 | VERL_PAUSE_CLEANUP PASS; container15:47:44–15:47:50Completed/exit0; platformSucceeded15:47:53HKT | PASS |
| Cloud candidate preflight/deletion | Every exact candidate checked and absent |45files/9,102,170,079logicalbytes;32emptydirectories removed;allabsent | PASS |
| Cloud retention | Retained inputs/benchmark/receipts preserve size/mtime |892files/362,228,155B allpreserved | PASS |
| Host phase1 | Exact candidates absent |180files/2,315,871B;24emptydirectories removed | PASS |
| Host phase2 | Selected evidence durable before deletion; exact candidates absent |127files/5,375,659B;2emptydirectories removed | PASS |
| Host total | Smoke/cache/rendezvous/raw files consumed |307files/7,691,530B deleted; allcandidatepathsabsent | PASS |
| Shared inputs/code/environment and permissions | No unrelated deletion or permission change | Tracked21sourcefiles retained; no shared model/environment paths targeted; no chmod/chown | PASS |
| Qwen complete qualification | Actual tensor scope and changed-value witness | Checker failed before tensor checks; HF2 retired by pause cleanup | UNVERIFIED |
| Full20-update/320-score workflow | All original acceptance gates | Neitherfresh20 nor updatedscoring submitted; originals partial | INCOMPLETE |

Cloud plus host deletion totals:352files/9,109,861,609logicalbytes. These are logical file sizes, not a measured physical-space recovery. Cloud manifest SHA256:`762db69ec9db7173a4ba561fd4326dd366f4ef14b6cb4b41ae7f945e7c5e339a`.

## Errors and verification limits

1. First stop invocation failed its first API read with TLS/SSL EOF, before any stop action. The same prescribed script succeeded after restoring the explicit runbook proxy environment. No alternate job-control mechanism was used.
2. First host deletion failed on its first root-owned file, deleting0. The same candidate identity checks/deletion used local passwordless sudo; permissions were unchanged.
3. HF2 checker exp-1106-153941-344108 actually failed15:43:19 with Git dubious ownership: its initial`git rev-parse HEAD`returned128, propagating CalledProcessError. It never reached the inventory/value body. That failed check is recorded, not fixed or retried during the pause.
4. Qwen actual2updates/numericalPASS remain valid observations. Header-only MTP/dtype explanations are not accepted complete tensor/value checks. DeletedHF2 cannot now establish the pending weight-change gate; a new actual export is required after resume.
5. Original benchmark replicas areStopped, but containerStatuses retain stale running fields. Platform stop times and launcher exits are known; exact original worker exit timestamps and physical allocation release counts are not inferred.
6. Shared model and installed environment contents were not scanned or hashed. Retention verification covers the892manifested task files plus tracked code, not an unrelated full filesystem audit.

## Durable evidence

- `evidence/user-pause-job-terminals.json`, `user-pause-stop-actions.json`, `user-pause-qualification-cleanup-terminals.json`.
- `evidence/user-pause-cloud-cleanup.json`, `user-pause-cloud-cleanup-platform.json`, `user-pause-cloud-cleanup-identity.json`.
- `evidence/user-pause-host-cleanup.json`; detailed host audit/deletion manifests remain under`/data/ycfeng/tmp/verl-agent-opd-cleanup-audit-20261106`.
- `evidence/qwen-fused-qualification-business.json`, `qwen-fused-qualification-platform-terminal.json`, `qwen-hf2-header-observation.json`, `qwen-hf2-values-inspection-failure.json`.
- Full cloud cleanup manifest:`/mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/runs/cleanup/exp-1106-154737-250834/manifest.json`.

No further training, scoring or numeric/export repair will run until the user resumes the task.

Independent post-terminal verification also passed: read-only SSH metadata access through the authorized cloud alias checked all45deleted files and all10target directories absent and all892retained files unchanged against the pinned manifest. A separate host check verified all307deleted paths absent, zero ignoredpyc left in the task source and7retainedcommands totaling18,106B. AlltaskevidenceJSON parses andgitdiff--check passes. See evidence/user-pause-independent-verification.json.
