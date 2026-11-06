## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Add actual GLM memory evidence and validate the existing FP32-head configuration. |
| 2026-11-06 | Record Qwen native old-logprob OOM, the scoped fused option check and consumed-log cleanup. |
| 2026-11-06 | Separate the actual Qwen task-reward failure from the non-blocking prefill API error; verify the native no-task-reward dispatch repair. |
| 2026-11-06 | Record actual initialization failures, real partial native scores and corrected fresh qualification submissions. |
| 2026-11-06 | Record one bounded capacity-alternative check and preserve the existing H800 queue. |
| 2026-11-06 | Record current four GPU job identities, resources and queued state. |
| 2026-11-06 | Distinguish actual Qwen serving from four infrastructure failures and still-queued GLM runs. |
| 2026-11-06 | Record independent GPU submissions, exact prerequisites, and initial platform state. |

# Native agent OPD workflow

This report preserves dated execution evidence separately from scientific acceptance. Current15:00HKT:GLM fourth qualification is initializing; Qwen fourth qualification failed in native old-logprob CUDA allocation, with its existing fused output configuration verified for the next attempt. Original GLM/Qwen benchmarks have16/49valid grades and continue. Neither training pair has an observed completed optimizer update or numerical PASS. Earlier queued/auth-failure sections are historical.

## Source and environment

- Repository /data/ycfeng/sota-engine/verl, branch agent-opd; submitted source commit1f5942c4c8df7acddaeed94992dd503913b8146f, independently matched on personal origin.
- Image artifactory.stepfun-inc.com/docker-public/verlai/verl@sha256:466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504.
- Native interpreter /data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python, Python3.12.13, torch2.13.0+cu130, transformers5.16.1, SGLang0.5.20, Bridge0.6.2, Core0.19.2.
- uv.lock SHA df508db0b957fa181c229fb75885cd3863cb651fd5233d0fa5af95e990bda0be. Native Core attention.py uses the recorded upstream FA4 metadata-first backport, SHA a733e2a6b5eb24e99fe4ca55a68f88bddf56ab0e5fd7ffd56a4b231c7262f5c8.
- Actual zero-GPU native imports/config-only Bridge dispatch passed; model construction, tensor conversion and CUDA kernels remain unverified until GPU execution.
- Personal i-fengyicheng RJobBackend, H800/codesign, source100.96.128.195:/data/ycfeng:/data/ycfeng. All cloud access stays under /mnt/codesign-exp/ycfeng.

## Submitted jobs and exact launcher parameters

All calls use tests/manual/agent_opd/rjob_run.py after the documented personal auth initialization, STEPMIND_BACKEND=rjob, and the image above. The local launcher stays alive. Resource memory units below are the --memory-gb argument; platform requests were verified in Mi.

| Ticket | RJob and UID | Command file | Per-replica resources | Launcher session | Actual state at03:04:17HKT |
| --- | --- | --- | --- | --- | --- |
| 02 | exp-1106-030133-940211 / b6976435-4e8a-4099-8777-800a18db25a1 | /data/ycfeng/tmp/verl-agent-opd-commands-20261106/qualification-glm.sh | --gpus8 --replicas2 --cpus48 --memory-gb600 | 86165 | Pending/queuing, no replicas |
| 06 | exp-1106-030308-839669 / f74fa974-ea86-4149-a823-3276ce493f8b | /data/ycfeng/tmp/verl-agent-opd-commands-20261106/benchmark-original-glm.sh | --gpus4 --replicas1 --cpus24 --memory-gb300 --sandbox-auth | 41495 | Pending/queuing, no replicas |
| 07 | exp-1106-030308-817360 / b20e47ee-bc8e-4486-84fb-829209bd915b | /data/ycfeng/tmp/verl-agent-opd-commands-20261106/benchmark-original-qwen.sh | --gpus2 --replicas1 --cpus12 --memory-gb150 --sandbox-auth | 34265 | Pending/queuing, no replicas |
| 01 | exp-1106-030308-851863 / 008947c3-7bc4-4fb9-9571-73b8608acb31 | tests/manual/agent_opd/prepare.sh | --gpus0 --replicas1 --cpus16 --memory-gb96 | 49616 | Starting/ContainerCreating onH8000344 |

The zero-GPU replica UIDcd3967cb-748c-4e00-8db9-f0ce730b97db matches its job owner. Creator, group, immutable image, source mount, non-preemptible setting and resources were verified for all four. The three GPU requests total22GPUs; allocated GPUs for this task were0 at this snapshot. No other job was stopped or changed.

At02:57:53–54HKT one current group API read returned totalQuota128, charged/nonpreemptible127, used128 includingpreemptible1, and enabled best-util queue. Immediately schedulable freeH800 is UNKNOWN; a queue request is not an allocation or a native result.

## Independent execution prerequisites

GLM uses the actual verified80-row dataset from input job exp-1106-024352-115509. Rank0 of the qualification command uses the existing physical slice(0,8), checks four source categories each2, writes a unique pending Parquet, verifies exact roundtrip and atomically publishes glm-qualification.parquet before native worker/recipe initialization. Other ranks use the same platform rank contract and enter normal rendezvous. The source dataset is:

`/mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/inputs/exp-1106-024352-115509/glm-learning.parquet`

The native worker command is:

```sh
bash /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/worker.sh \
  --pair glm --steps 2 \
  --dataset /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/inputs/exp-1106-024352-115509/glm-qualification.parquet \
  --output-root /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/runs/qualification \
  --settings /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/settings.json \
  --pairs /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/pairs.json \
  --shared-dir /data/ycfeng/tmp/verl-agent-opd-20261106/rendezvous \
  --nodes 2 --gpus-per-node 8 --gpu-type H800 \
  --startup-timeout 1800 --training-timeout 14400
```

The two original benchmarks independently call the existing benchmark.py prepare entrypoint under a shared fcntl lock before starting SGLang. They create or validate the same canonical membership at:

`/mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/inputs/fixed-benchmark/benchmark/membership.json`

Its actual SHA must be computed and validated on the worker. There is no invented SHA or overall training-input PASS. The original source parent is swe-common-50.json, selection seed1234,2astropy/18django, seeds1729–1732, temperature1/top_p0.95. Existing membership validation checks20distinct ordered IDs, the dataset hash, sampling and seeds; the launch prefix also checks the current parent hash. Both serving jobs consume that exact path and digest.

Benchmark native engine resources: GLM TP4, Qwen TP2; context131072, prefill8192, memory fraction0.75, max-running-requests4, startup600seconds, native per-question/seed timeout21600seconds, BaseMind. Qwen uses the pinned supported triton linear-attention backend. Native SWE subprocess cwd/PYTHONPATH preserve native-eval imports and avoid verl tests.e2e shadowing. Original model identity is the pinned student path/version0; no learned model or teacher is substituted.

The separate input job uses the reorganized existing prepare.sh. Benchmark and each pair publish independent real receipts. Qwen scans the same verified train bank using its own rendered length; budget61440 and20percategory stay fixed. Overall inputs.json is published only if every independent component passes.

## Required actual acceptance

| Gate | Passing condition | Current result |
| --- | --- | --- |
| Native GPU | Actual requested workers/nvidia-smi, Ray topology, model construction/conversion, correct teacher/student paths | Qwen original SGLang loaded TP0/1; training/teacher and actual nvidia-smi receipt remain unverified |
| Two-step workflow | Two finite native optimizer updates, valid nonzero gradients, teacher scores actual student tokens | NOT RUN |
| Same-weight numerics | Decode/prefill/trainer same token-position-mask/probability and versions0then1; per-input/global-token MAE≤0.03; native-pack limit measured or strictly proven under the documented whole-row condition | NOT RUN |
| GLM R3 | Real route payload plus native replay initialization/old-logprob/update return; independent kernel route-consumption audit not claimed | NOT RUN |
| Fresh20 | Separate run from original weights, exactly20successful updates; not the qualification weights | NOT RUN |
| Export/reload | Complete exact step20HF identity/inventory, observed changed weight, new SGLang process and actual generation | NOT RUN |
| SWE | Each pair/version80valid grader results,320total; valid unresolved0, infrastructure failures missing; avg@4 fixed denominator | Qwen first-question four seeds infrastructure HTTP401, zero valid grades; remaining scores NOT RUN |
| Cleanup | Consume task-owned temporary artifacts after their dependents, preserve shared models/data and other jobs | Partial cache cleanup only |

Auxiliary observation errors are unverified evidence, not grounds to terminate healthy native training. Native failures retain their normal handling. Final conclusions require business outputs and explicit comparisons, not Running/SERVER_READY/exit0 alone.


## Actual Qwen original native start and sandbox authentication failure

Job exp-1106-030308-817360, RJobUIDb20e47ee-bc8e-4486-84fb-829209bd915b, replicaUID5d296e9a-4c5a-4c67-9504-07af26a1b347, H800-0057, actually ran03:22:09–03:24:22HKT and exited1/restart0; platformFailed03:24:24. Personal creator, pinnedimage and currentNFS match. OriginalQwen SGLang loaded TP0/1, triton linear backend and model_infoHTTP200. Canonical membership was actually created/validated withSHA0f4ab340bedb7a64f3089af679be829aefcf8ecbbeb11c3a164578ba6b702877. Serving is observed; valid grader outputs remain0.

Firstquestion all4seeds returned infrastructureHTTPStatusError in0.19–0.25seconds; native subprocess exit0 does not make those outcomes valid. SessionRouter POST/session returned401 Unauthorized, response action decrypt_auth_token/error illegal base64 data at input byte0. Native sweagents_configs.py130 uses literal ${SESSION_ROUTER_USER_TOKEN}; actual ConfigManager._substitute_env_vars (swe_agents/config.py91–113) preserves an unresolved placeholder. The forwarded environment hadSR_USER_TOKEN present andSESSION_ROUTER_USER_TOKEN absent, so env.py294 passed the placeholder to SessionRouterClient User-Token header (session_router_client.py403). Selected platform+redactednative evidence: evidence/runtime-qwen-original-auth-failure.json. Raw native log stays in this job's cloud attempt directory; no credentials are archived.

Smallest repair in benchmark.py's existing child environment: copy the already present SR_USER_TOKEN only when SESSION_ROUTER_USER_TOKEN is empty; preserve a supplied canonical token. rjob_run and credentials are unchanged, with no auth bypass/retry. CPU3.12.13 exercised real run/run_attempt paths for fourseeds in three environment cases (onlySR/onlycanonical/bothcanonicalpreferred); all12children invoked actual native SWE Python3.10 ConfigManager substitution and passed without a literal placeholder. Missingtoken still failed readiness, and synthetic token bytes were absent from stdout/report artifacts. First fixture attempt exposed missingtoml in the separate CPU3.12 fixture environment; using the existing native3.10 parser succeeded, with no installation or production dependency change.

benchmark.sh now records actual nvidia-smi GPU index/name/UUID/memory/driver before serving, and the existing archive function preserves itsCSV alongside server.log then consumes workerlocal copies. Actual archive fixturePASS; bash-n/AST/diff-checkPASS. The test fixture was consumed. This is CPU/mock validation of the repair; a real successful SessionRouter request and validgrader remain required.

The existing identity excludes sourceGitSHA/credentials; model/pair/version/membership/benchmark/parser/sandbox identity remains identical. Existing Miles result reader excludes the fourfailedgeneration/missinggrading attempts, so a rerun in the same outputroot creates newUUIDattempts only for missing slots. Running/reserved/interrupted slots remain protected. No existing identity/result policy was changed.


Exact CPU fixture entry: `PYTHONPATH=/data/ycfeng/sota-engine/verl timeout 60s /data/ycfeng/envs/miles-agent-opd-cpu/bin/python -B -` with an inline driver. Native child interpreter: `/data/ycfeng/steptron/.worktrees/step3p6-replay-v1/.venv/br-native-swe-py310-1008am/environment/bin/python`; child PYTHONPATH=`/data/ycfeng/steptron/.worktrees/step3p6-native-eval-1015z/third_party/swe-agents/src`. Actual child call: `ConfigManager._substitute_env_vars({'env': {'session_router_user_token': '${SESSION_ROUTER_USER_TOKEN}'}})`. Unique child stdout NATIVE_TOKEN_RESOLVED; final driver statusPASS/cases3×native_children4/actual_native_config_substitutionPASS/token_values_loggedfalse/missing_credentials_rejectedtrue/archive_preserves_gpu_receipttrue/GPU_or_network_callsfalse. The inline fixture directory `/data/ycfeng/tmp/opd-benchmark-token-pprq797h` was removed after consumption.


## Current four GPU jobs after verified preparation and auth repair

At03:37:58HKT all four jobs were Pending/RJob is queuing, with no replicas or allocatedGPUs. Totalrequested30H800. The originalGLMqualification exp-1106-030133-940211 (2×8) andGLMoriginal exp-1106-030308-839669 (4) retain their initialidentities/launchers. Two new calls use the same rjob_run.py/image/personal/currentNFS setup:

| Ticket | RJob / UID | Command / resources | Launcher |
| --- | --- | --- | --- |
| 07 | exp-1106-033246-436787 / f5c97c61-7868-44f6-8a74-34ab529bd6b2 | same benchmark-original-qwen.sh; --gpus2 --replicas1 --cpus12 --memory-gb150 --sandbox-auth | 30922 |
| 03 | exp-1106-033627-955641 / 9ad17773-2d4e-4b21-8dc2-2150ab8a6f85 | qualification-qwen.sh; --gpus8 --replicas1 --cpus32 --memory-gb300 | 13885 |

The07retry followed source3c7541c1998c4bde1f63d662693364bb98178712 commit/push and independent remoteSHA match; immediate previous-job API read verified originalUID andFailed. The03 firstsubmission followed actual complete input/configPASS, not an inferred sourceMiles result. Its command is:

```sh
bash /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/worker.sh \
  --pair qwen --steps 2 \
  --dataset /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/inputs/exp-1106-032827-028041/qwen-qualification.parquet \
  --output-root /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/runs/qualification \
  --settings /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/qwen-settings.json \
  --pairs /data/ycfeng/sota-engine/verl/tests/manual/agent_opd/pairs.json \
  --shared-dir /data/ycfeng/tmp/verl-agent-opd-20261106/rendezvous \
  --nodes 1 --gpus-per-node 8 --gpu-type H800 \
  --startup-timeout 1800 --training-timeout 14400
```

Quota-only03:32:37–38HKT HTTP200 selectedfields: totalgpu/H800128, chargedgpu127, usedgpu120, nonpreemptiblequota/usedgpu127, preemptiblequota/usedgpu1; enabled best-utilqueue. Inconsistent field meanings do not prove immediatelyschedulablefreeH800; that value remainsUNKNOWN. Two localparser-shape failures caused repeatedreads before fields were selected; this observer defect was corrected by stoppingrequests and requiring raw-response preservation for futureparsing. It did not change quota or jobs. Existing launcher processes remain alive; inputlauncher92790 returned succeeded03:35:02 after nativecompletion and its cleanupstop was subsequent.


## Capacity alternatives during the external queue wait

At04:32–04:33HKT a single current quota request percodesign/step_main followed by the conditionally authorized personal H200 activejob/owner-replica read was completed. Rawquota JSON was retained0600before localparsing; no retry. Aggregate selected evidence/capacity-wait.json records exact selected source paths andSHA. codesigntotal128,used124,charged123,nonpreemptibleused127/preemptibleused1 still does not identify immediatefreeH800. step_maintotal512/used488 gives onlyledger24; personal H200 currently has56nonpreemptible and16preemptibleGPU across9Runningreplicas, completepagination. Under the configured32nonpreemptible cap, addedheadroom for this task is0. No H200 submission or otherjobcontrol was performed; existing4H800jobs remainqueued. Other tasks' historical authorizations are outside this record. This is externalcapacity evidence, not model/workflow failure or scientificacceptance.


## Resumed actual failures, partial original scores and fresh qualifications

InitialQwen exp-1106-033627-955641 actually reached8H800 but failed08:04:26HKT at native DistillationConfig:126976+4096+1=131073>131072, containerexit1at08:04:36. InitialGLM exp-1106-030133-940211 reached2×8H800, actual8input/Ray/loaders, then failedat61440+4096+1=65537>65536, rank0exit1at08:24:10; the platformfailurepolicy stoppedrank1afterward. Its stale running container snapshot leaves the rank1exitcodeUNKNOWN. Both failedbeforefit, so no update/numerical/R3/weightchangePASS. Selected actualbusiness evidence: evidence/qwen-qualification-context-failure.json and glm-qualification-context-failure.json; exactpre-retry terminal reread: qualification-retry-terminal-read.json. The correctedprompt native-regression/input checks are in the executionpreflightreport, not relabelledGPUacceptance.

Fix86618c51379ba9abd20468435599fb999008e8b7 was committed/pushed and independently matched by `git ls-remote origin refs/heads/agent-opd` before the new submissions. Same initialized personalRJobBackend/image/currentNFS/rjob_run.py as before:

| Pair | Newjob / UID | Commandfile | Resources perreplica | Launcher |
| --- | --- | --- | --- | --- |
| GLM | exp-1106-134352-384471 /66f0521c-831e-4336-abba-6a1dfeae74bd | /data/ycfeng/tmp/verl-agent-opd-commands-20261106/qualification-glm.sh |8H800/48CPU/600000Mi ×2 |56549 |
| Qwen | exp-1106-134403-815066 /41b7cae1-d62e-4624-bfb1-cd5839d4617e | /data/ycfeng/tmp/verl-agent-opd-commands-20261106/qualification-qwen.sh |8H800/32CPU/300000Mi ×1 |35793 |

Submission invocation is the earlier exact `rjob_run.py --image ... --command-file ... --gpus8 --replicas2/1 --cpus48/32 --memory-gb600/300 --name verl-opd-{glm,qwen}-qualification-retry-1106`, from currentmachine with STEPMIND_BACKEND=rjob and existingpersonalcredentials. Source/image remain pinned to the documented company image. GLMcommand now only validates/reuses the alreadycreated8parquet, then sameworker. Selected metadata evidence/qualification-retry-identities.json confirmscreator/currentNFS100.96.128.195:/data/ycfeng:/data/ycfeng/codesign/nonpreemptible/RDMA/resources. At13:46:26HKT GLMStarting/twoContainerCreating, QwenPending/noreplica; bothoriginalsRunning/restart0. Localmetadataobserver3781 was stopped onlyafter exactPIDbinding, exit143, then sole4job observer89373 started sequentially. No workloadlauncher orhealthyjobwasstopped.

Originals now have realnativepartialoutcomes:13:38:17HKT GLM10/80valid(5resolved/5unresolved),Qwen38/80(29resolved/9unresolved). Bothfirst4gatespassed. Actualnvidia-smi4H800/2H800,modelpath/version0,canonicalmembershipSHA unchanged. RealQwensandbox/tool/generation/grader execution nowverifies the earlierauthrepair. ThreeQwencontextoverflowepisodes stillmissing: inputs131334/131150/131177>131072 led oldgenericModelError→no normaltrajectory→FileNotFoundError/invalidgrading. Theirprocessreturned0/generationreturned do notmakevalidgrades. Selectedpaths/hashes/counts evidence/original-benchmarks-partial-1338.json; no full80oravg@4PASS.

Read-onlysourceinvestigation found an existingMiles fix72fe633d76b8ed3315081a81b36678257dd6de81 (native_benchmark.pySHA7196ce82e4d22767e46fa4a44f39cbd14f4a1f37209e950a82edf379cfde46c4): exactSGLangHTTP400contextoverflow becomes nativeContextWindowExceedError, entering actualDefaultAgent latest_half/exit_context/autosubmit, patch extraction and normaltrajectorysaving→actualgrader. Oldthreeattempts startedbeforethatcommit andremainmissing; no retroactivegrade. The currentrun's laternewsubprocesses canuseexistingfix. NoMilesedits/contextincrease/newhandler. Existingbenchmarkrun has no three-slot selector and protects running/reserved slots while skippingvalid results; aftercurrentterminal use originalsame2GPUcommand/outputroot to recover actualmissingonly. Detailedsource/provenance/recoveryreceipt evidence/qwen-benchmark-context-recovery.json. Preserveallhealthycurrentattempts; do not start a secondwholebankrunwhileitsuntouchedfuture slotswouldbeeligible.


## Actual first-rollout failure and second repair

Both retries passed the former teacher-context guard, initialized native models/SGLang and entered fit. Their first rollout failed in agent_loop.py1335 → protocol.py871: `DataProto` had4rows while agent.num_workers defaulted to8. GLM exp-1106-134352-384471 exited1 at13:58:27HKT on both ranks; Qwen exp-1106-134403-815066 exited1 at14:02:44HKT, with its actual assertion at14:02:32. Each actual training.json records zero actor update calls, zero completed updates, empty update outcomes, native_fit_returned=false and final_export=null. GLM also logged46routing-replay layers initialized; actual replay/updates are not verified. Selected native causal evidence: evidence/glm-qualification-batch-failure.json and qwen-qualification-batch-failure.json. No OOM cause is inferred.

The single override `actor_rollout_ref.rollout.agent.num_workers=train_batch_size` derives4workers for the fixed4prompt/n1 batch. Actual native DataProto chunk/concat checks across both2/20recipes reproduced old4/8failure, passed new4/4dispatch and preserved exact token/UID order. Every other recipe field and the previously validated teacher context remain unchanged. Detailed command and native results are in execution_preflight and evidence/native-agent-worker-batch-regression.json. Fixffb83e83d65f9c93251f5f27ea259e18305f22ff was pushed and independently matched before submission.

The platform owner re-read both previous exact Failed UIDs at14:08:40HKT. New GLM exp-1106-140852-369748 / UIDb20d2692-2e74-4b68-a2b2-6b3cd0e29cb4 was created14:08:52, launcher96491. New Qwen exp-1106-140853-397005 / UIDf400952c-ee74-4b55-8f2b-26828705a417 was created14:08:53, launcher24467. Commands, original inputs, pinned image and resources are unchanged. At14:11:01 both wereStarting; original jobs remainedRunning/restart0. Creator/currentNFS/codesign/nonpreemptible/H800/image/RDMA/resource fields actually matched in evidence/qualification-agent-worker-retry-identities.json; old terminal evidence is qualification-batch-retry-terminal-read.json. Local read-only watcher59518 exited143 after exact process binding, then sole4job watcher96841 started; no GPU workload was stopped or duplicated.

## Actual Qwen task-reward failure and auxiliary prefill API repair

Qwen exp-1106-140853-397005 crossed the repaired native four-worker dispatch. Primary generate returned, but its response IDs/count were not retained before the later failure, so no nonempty token population or teacher scoring is inferred. At14:21:51HKT independent-prefill observation raised TypeError `Unexpected keyword argument detokenize`; the existing observer caught it and continued native processing. At14:21:52 the distinct terminal chain was AgentLoopWorker._compute_score -> RewardLoopWorker.compute_score -> NaiveRewardManager.run_single -> default_compute_score, which rejected data_source=np.str_('qwen'). Native teacher scoring follows _compute_score and was not verified. Actual training.json remains completed_updates0/actor_update_call_count0/update_outcomes[]/native_fit_returnedfalse/final_exportnull. Container exit1/Error14:22:05, job Failed/finish14:22:07. Selected complete causal chains/source hashes/zero-update receipt: evidence/qwen-qualification-reward-failure.json.

This task has explicit distillation use_task_rewards=false. Its task-specific PreparedTurnAgentLoop now supplies the existing AgentLoopOutput.reward_score=0.0 field, so native _compute_score skips the unrelated default task scorer. The following native teacher-logprob call and teacher-derived k1 OPD policy-gradient objective remain in place; no fallback exception handler or custom scorer is added. The independent-prefill request only removes detokenize, preserving max_tokens1/temperature1/prompt_logprobs0/full prompt+response/radix-cache exclusion. Pinned SGLang0.5.20 SamplingParams reproduces the old TypeError and accepts the supported request; GenerateReqInput accepts unchanged input/logprob fields. See evidence/native-prefill-api-regression.json. These are CPU/API results, not actual GPU prefill or MAE acceptance.

Exact native CPU command:

```sh
timeout 60s env PYTHONPATH=/data/ycfeng/sota-engine/verl \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/ycfeng/tmp \
  /data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python -B -m unittest \
  tests.manual.agent_opd.test_agent_loop tests.manual.agent_opd.test_alignment -v
```

Actual result:12tests/OK. The new repeatable native dispatch regression covers both np.str_ pair labels: old default scorer rejects them; actual task loop preserves fixture prompt/response IDs, logprobs, masks and routed experts, returns zero task reward, native task-score method skips its reward worker, and native teacher dispatcher still receives the exact complete sequence/routing key. The11existing alignment tests also pass. Generation/teacher outputs are fixtures; GPU generation, actual teacher scores, optimizer updates, versions and numerical agreement are not proved. Receipt: evidence/native-no-task-reward-regression.json. Requested systemd system scope failed with interactive-authentication-required, and user scope had no bus, both before Python execution; the bounded small CPU fixture then ran with timeout60 and no model tensor reads.

GLM's two current workers started14:21:11/14:22:09HKT and remain active. Since agent_loop.py is mounted live and was edited during initialization, its launch SHA ffb83e83 does not prove which module version each process loaded. Preserve the healthy job; record its actual native behavior and this code-identity limit rather than guessing or restarting it.

## Native teacher detokenize conversion and consolidated repair

GLM exp-1106-140852-369748 subsequently passed primary generation/task-score handling and failed in native teacher scoring. Actual chain: _compute_teacher_logprobs -> teacher_manager.compute_teacher_logprobs_single -> SGLangHttpServer.generate -> TokenizerManager._create_tokenized_object -> SamplingParams(**sampling_kwargs), TypeError unexpected detokenize. Native teacher_manager returns the same vLLM-style output option as the task prefill. Both must use the SGLang adapter's existing translation; removing the key from only the task caller was incomplete. Actual training.json remains zero calls/updates, no final export; turns/aggregate absent. Selected complete evidence: evidence/glm-qualification-teacher-api-failure.json. Platform Failed14:35:11HKT; rank1exit1at14:35:09; rank0Stopped/stale running snapshot does not establish its exitcode.

Shared fix in async_sglang_server.py consumes detokenize beside the existing max_tokens/logprobs/prompt_logprobs translations. This API reads output_ids and numerical logprobs, ignoring response text; no logprob-text flag is substituted for detokenize. Teacher_manager remains unchanged for vLLM. Task prefill's original detokenize=false field is restored, so both observed producers now exercise the same translation. Numerical masks, tokens, temperatures, teacher/student identities and objective are unchanged.

Exact affected check uses the preceding timeout/env/native-interpreter command, with `-m unittest tests.workers.rollout.test_sglang_teacher_sampling_on_cpu -v`. Final result:1test/2subcases/OK, covering native teacher-produced prompt_logprobs0 and2. The real SGLangHttpServer.generate creates the real GenerateReqInput, whose sampling dictionary is accepted by pinned SamplingParams; input IDs, max_new_tokens1, temperature1, return_logprobtrue, logprob_start_len0, optional topK, output IDs/logprobs and native prompt-logprob extraction all match explicit expectations. Tokenizer responses/Ray actor-name context are fixtures, not GPU scoring. The old direct SamplingParams(detokenize=false) negative case reproduces TypeError. Evidence: evidence/native-sglang-teacher-translation-regression.json. Three earlier test iterations failed due fixture setup/expectation only (read-only LoRA property, missing disabled MTP field, native None topK default); no extra production change was made for them. The12existing native dispatch/alignment checks had passed; no unrelated test expansion follows.

Qwen exp-1106-143409-709386 /UIDa0ed2fa1-9007-4456-8196-f24c148be472 was submitted14:34:09 after7965a385 push/remote match and a14:33:43 exact previous Failed reread. Launcher72859, same8H800/32CPU300GB/command/input/image/currentNFS, actual worker14:35:39/H8000128. It remains initializing while shared adapter source was edited; actual behavior must establish which repair it loaded. No healthy run was canceled.


## Qwen old-logprob memory failure and native fused output setting

Actual exp-1106-143409-709386 / UIDa0ed2fa1-9007-4456-8196-f24c148be472 failed at14:47:43HKT native RayPPOTrainer._compute_old_log_prob -> Megatron forward_only -> transformer_impl.py1205 logits.clone. CUDA requested37.04GiB, free33.80GiB, capacity79.19GiB; worker exit1/Error14:47:57 and jobFailed14:47:59. This is CUDA allocation failure, not platformOOMKilled. Training receipt0calls/0updates/native_fit_returnedfalse/exportnull; turns/aggregate absent. Native teacher scoring returned by the uncaught awaited control flow and score-row assertion, but raw finite teacher values and independent-prefill success are not retained. Exact recipe/input/memory/error-chain evidence: evidence/qwen-qualification-old-logprob-oom.json. The inferred80072logit rows are explicitly an upper-bound calculation, not an observed tensor shape.

Change only the existing model.use_fused_kernels setting totrue for Qwen, explicitfalse for GLM. Existing Qwen35VLBridge -> Qwen3VLModel -> Qwen3VLGPTModel(GPTModel) forwards native output_processor/context before full logits materialization. Existing Triton linear_cross_entropy computes numerical logprobs/entropy; GDN, token populations, lengths, masks, packing and loss stay unchanged. No engine code or entropy switch was added.

Exact CPU entry: timeout60s env PYTHONPATH=/data/ycfeng/sota-engine/verl PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/ycfeng/tmp /data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python -B - with the inline four-case driver. Python3.12.13. The driver uses actual recipe_overrides/Hydra compose/native DistillationConfig for GLM/Qwen×2/20; verifies Qwen's sole changed override is model.use_fused_kernelstrue, GLM none; checks full context/token budgets, batch, CP1/nonDCP, remove-padding/MTPdisabled and k1 teacher-PG settings. Actual4/4PASS. Receipt: evidence/native-qwen-fused-config-regression.json. An initial driver unnecessarily instantiated HFModelConfig, whose tokenizer side effects cannot read unmounted canonical cloud assets on this host; it failed and was corrected to inspect the composed model config and instantiate only DistillationConfig. No model tensor was read.

Attempted existing check: timeout60s with the same env/interpreter, -m pytest tests/models/test_model_forward_fused.py -q -p no:cacheprovider. Actual collectionBLOCKED before tests: OSError /lib/x86_64-linux-gnu/libstdc++.so.6: version GLIBCXX_3.4.32 not found (required by transformer_engine/libtransformer_engine.so). This known CPU-host boundary was not patched; no testPASS claimed. Actual fused CUDA compilation/runtime, memory, three-way MAE≤0.03, optimizer updates and weight changes remain pending the next real worker. Do not expand host environment work.

## Exact consumed old-log cleanup

0GPU exp-1106-145012-595571 / UIDef494491-785b-46ff-b40c-e5248eb9129a, same rjob_run.py/image/personal/currentNFS, command /data/ycfeng/tmp/verl-agent-opd-commands-20261106/cleanup-consumed-qualification-logs.sh; --gpus0 --replicas1 --cpus4 --memory-gb8, launcher52396. Command SHA7e6184fccc0a1ea81ab17648aaf8155d6cbc2cf571ed91c2332321957e5b8bd5, bash-nPASS. Native API Succeededfinish14:54:27 precedes launcher observed success14:54:28 and exit cleanupstop14:54:29. Worker normal mount ownership used; no chmod/sudo/trash operations.

Expected/actualPASS: all52manifest files preflight verified,38available hashes verified; exactly28old raw logs/1,360,048bytes deleted and absent;24retained files/161,309bytes size/mtime preserved. Receipt canonical /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106/runs/cleanup/exp-1106-145012-595571/receipt.json,17633bytes,SHAcee4f7a899c2a951c495520ceba7692c3fc2ca6e0240afc211347cb98fcc4965, independently read through readonlySSH alias. Selected full receipt and platform terminal are in evidence/consumed-qualification-logs-cleanup.json and evidence/consumed-qualification-logs-cleanup-platform.json. Physical reclaimed space unverified; no directories/permissions changed.


GLM fourth qualification produced actual step1 numerical FAIL before this commit: four inputs / 1,265 loss-eligible tokens at version0. Global token MAE decode/prefill=0.0390841902, decode/trainer=0.0310881366, prefill/trainer=0.0382872158; every pair exceeds0.03. Per-input maxima0.0418422823/0.0357459613/0.0419510390 also prevent whole-input bounds from proving native-pack acceptance. Token/version checks match; two turns pass and two fail. Native training continues normally for the remaining update/version/HF2 evidence. GLM fresh20 remains gated on full numerical qualification; do not relax thresholds. Selected source-backed diagnosis is pending.


## GLM native memory failure after the first numerical FAIL

Actual GLM954702 job Failed15:12:38HKT before launcher exit cleanup15:12:40.754; rank1 exit1/Error15:12:35. The finally training receipt has1actor_update_call,0verified completed updates, native_update_returnedfalse/ActorUnavailableError/rpc14. Whether the interrupted optimizer changed weights is UNKNOWN; no step2/version1/HF2 artifact exists. Actual numerical step1 FAIL remains independent.

Ray used memory reached629140910080B against total629145600000B and95%threshold597688320000B on rank0/H8000401. Its actual killed processes PID10294/10295 are AgentLoopWorker actors of about1.07GiB, not the failed update actor69ea. The update actor exit mechanism remains incompletely mapped; do not claim CUDA OOM or containerOOMKilled. Objectstore53.5MB does not explain the exhaustion. Selected full business and platform evidence: evidence/glm-qualification-native-memory-failure.json and evidence/glm-qualification-memory-platform-failure.json. Actual finally logs/selected lines/hashes and unknown fields are retained.

The header-only native inventory reads shapes/dtypes from48safetensors headers without tensor payloads: decoder29,943,393,920params=expert27,783,069,696+dense/shared/head2,160,324,224; disabledMTP1,278,094,656 excluded. Evidence/glm-student-header-memory-inventory.json. Native TP/DP/EP placement gives approximate CPU BF16 model64,207,436,288B + FP32 masters119,773,575,680B + twoAdam moments239,547,151,360B =423,528,163,328B before SG/cache/export. DDP offload releases GPUgrad storage; it does not add a CPUgrad plane. Sharedmmap RSS cannot be summed as actual cgroupused. Select the upper end1000 of the sourced800–1000normal-memory candidate range; actual requested1000000Mi/replica, not a proven sufficient allocation. Preserve offload/Ray monitor/GPU/layout/algorithm.

## Existing FP32-output head hypothesis: configuration check only

Hypothesis before the next actual GPU run: BF16 head-output rounding may contribute enough cross-shape drift that existing FP32-output heads satisfy the unchanged three-way MAE≤0.03 contract on the same8source prompts. Falsifier: actual numerical qualification still fails; then the change is insufficient and no causal fix is claimed. Existing observations do not prove the head is the root cause; attention/MoE/dense shape sensitivity remains a candidate. Same-weight protocol tags are not a live tensor checksum.

SGLang0.5.20 ServerArgs enable_fp32_lm_head flows through GLM ParallelLMHead/LogitsProcessor and BF16 CUDA torch.mm(out_dtype=torch.float32). Megatron GLM47Bridge targets GPTModel; disabledMTP/remove-padding/CP1 satisfy existing fused constraints, R3 route setup precedes the fused branch, and use_ligerfalse selects existing Triton linear_cross_entropy FP32 accumulators. Model weights remainBF16; backend/reduction order differs, so no bit-identity promise. The current shared GLM kwargs also set the frozen teacher's head output toFP32. Benchmark settings are unchanged and are not claimed numerically qualified for every possible serving configuration.

Exact check: timeout60s env PYTHONPATH=/data/ycfeng/sota-engine/verl PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/data/ycfeng/tmp /data/ycfeng/envs/verl-agent-opd-megatron-sglang/bin/python -B - with inline driver. Python3.12.13. Actual recipe_overrides/Hydra compose/native DistillationConfig for GLM/Qwen×2/20:4/4PASS; GLMonly changes model.use_fused_kernels and its existing rollout/teacher engine_kwargs; Qwen unchanged. Full lengths/batch/loss/optimizer/CP1/nonDCP/R3/input/model identities preserved. Receipt evidence/native-glm-fp32-head-config-regression.json. No new host library or fixture expansion, GPU calls or model payload reads. Actual runtime/MAE/update/capacity/HF2 gates still open.
