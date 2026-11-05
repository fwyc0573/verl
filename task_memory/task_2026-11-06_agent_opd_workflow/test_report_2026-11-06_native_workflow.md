## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Distinguish actual Qwen serving from four infrastructure failures and still-queued GLM runs. |
| 2026-11-06 | Record independent GPU submissions, exact prerequisites, and initial platform state. |

# Native agent OPD workflow

This report covers actual worker execution and scientific acceptance separately. GLM qualification and original benchmark are queued. Qwen original serving actually loaded, but all four first-question seeds failed in sandbox authentication; no native numerical or SWE score is accepted yet.

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
