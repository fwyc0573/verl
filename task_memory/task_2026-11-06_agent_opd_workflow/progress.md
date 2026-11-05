## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Adopt the user-selected Steptron numerical standard; record cache repair and native launch adapters. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# Progress

## Current state

- completed: 规划草案、10 tickets、新分支及个人 repo 推送；已有文档检查证据。
- in-progress: 用户已指示“开始执行”，按推荐 A 的两组对称 20 步与原始/更新后评测推进。沿用来源单 turn 训练。
- in-progress: ticket01 原生锁定环境、模型支持、真实数据适配、同 student 数值观测。已解析 CI image amd64 digest；首个零 GPU 环境 worker 因离线 wheel 缺失失败，正在补齐锁定依赖。
- pending: 两组 GPU 资格、独立 20 步、导出重载、320 个有效评测、最终清理。
- 本任务尚未提交 GPU 作业；当前新增代码与环境阶段不代表 workflow 或数值通过。既有 .serena/ 始终保护。

## Investigation commands and conclusions

- git status --short; git branch --show-current; git log -1 --format='%H %s'; git remote -v; git branch --list。
  - Actual: main 起点；仅 .serena/ 未跟踪；origin fetch/push 均为个人 repo。
- git ls-remote --heads origin agent-opd。
  - Actual: 退出 0、无输出；检查时远端没有该分支。
- git switch -c agent-opd。
  - Actual: 成功建立并切换到新分支。
- 读取 miles task 的 requirements.md、plan.md；按 alignment/Frog/Qwen 等关键词读取 test_report_2026-11-05_agent_opd_learning.md，读取 progress.md 末段。
  - Actual: 来源 GLM 20 步 + benchmark，Frog/Qwen 两步；最新已读记录并未提供校准的数值通过阈值。当前 live jobs 未查询，文档状态不作为实时状态。
- 读取 miles/examples/agentic_opd/rollout.py 与 tests/manual/agent_opd/alignment.py。
  - Actual: 新单 turn + teacher 评分；另取同 student 独立 prefill。训练期间实际多轮工具执行尚不能由这些实现证明。
- 读取 verl 的 OPD 文档、Qwen3.5 FSDP 示例，以及 agent_loop.py/actor.py 的相关 symbols。
  - Actual: 已有可复用路径；尚未验证目标模型/镜像/长上下文/数值的实际兼容性。

## Historical planning decisions (superseded by execution steering below)

- Requirements 中的 Questions to resolve 是唯一未决设计列表；ticket 不将推荐值伪装成用户确认。
- 推荐两组对称完成 20 次更新与两版本各 80 次有效 benchmark。来源的非对称范围作为第一题的真实备选。
- 不以来源 GLM 误差数值设置新阈值；不以 student/teacher 相等为准；不以 TIS 或训练成功替代数值验收。
- 每次只问一个决定；前一题答复后再推进相关分支。文件创建与已批准的个人 branch 同步可继续。

## Next actions

1. 监控零 GPU 环境修复 exp-1106-013411-959935，保持 launcher 存活；对照首次缓存缺失错误核对结果。
2. 并行落实数据适配和原生数值观测，完成 ticket01 的运行合同；必要缺口用最小变更修复。
3. 按实测配额推进两组资格及基线评测，完成一项即检查、提交、推送并消费无后续依赖的产物。

## 1. 规划完成情况

**汇总：** PASS 2｜BLOCKED/FAILED/SKIPPED 0｜TODO 10

| 子任务 | 状态 | 简要依据 |
| --- | --- | --- |
| 规划草案与本地直接检查 | PASS | 新 branch、来源核对、10 个草案及结构检查完成 |
| 个人分支首次同步 | PASS | fe8c108e 本地与独立远端 SHA 一致 |
| 01 合同 | TODO | 测试矩阵、训练交互和数值预算待访谈 |
| 02 GLM 两步一致性 | TODO | 依赖 01，未运行 |
| 03 Qwen 两步一致性 | TODO | 依赖 01，未运行 |
| 04 GLM 20 步与重载 | TODO | 依赖 02，未运行 |
| 05 Qwen 20 步与重载 | TODO | 扩展范围待确认，未运行 |
| 06 原始 GLM 评测 | TODO | 依赖 01，未运行 |
| 07 原始 Qwen 评测 | TODO | 扩展范围待确认，未运行 |
| 08 更新 GLM 评测 | TODO | 依赖 04、06，未运行 |
| 09 更新 Qwen 评测 | TODO | 依赖 05、07，未运行 |
| 10 最终清理与交付 | TODO | 依赖最终范围内的真实结果 |

## 2. 偏离检测

**结论：** 未偏移，正常推进。
**检测窗口：** 本轮创建规划草案至首次 push 复核｜**当前前沿：** 01 访谈

| 模式 | 判定 | 依据 |
| --- | --- | --- |
| D1 工具打磨 | CLEAR | 只做一次无依赖文档检查，未新增运行 harness |
| D2 细节反复重试 | CLEAR | 无失败修复循环 |
| D3 支线问题修补 | CLEAR | 所有读取对应来源范围、复用入口或用户指定 Git 交付 |
| D4 可并行任务停滞 | CLEAR | 运行合同尚未确定，GPU tickets 尚不可执行；文档同步独立推进 |
| D5 超范围镀金 | CLEAR | Qwen 扩展标为建议，没有新增执行或架构实现 |
| D6 分析空转 | CLEAR | 调查已落实为 task、tickets 和第一项待决问题 |
| D7 路线违背 | CLEAR | 先访谈、写草案和新 branch，没有提前训练 |

**文档检查：** S1–S6 均未发现当前草案的明显缺陷；01 明确负责解决未定数值标准，未把未定标准写成可执行合同。原始评测不依赖训练结束，两组无虚假串行依赖。
**归因：** 无。

## 3. 纠正建议

**分支：** A：spec/tickets 草案合理，无需改动。
**需停止的偏离行为：** 无。

**接下去的路线：**
1. 本次仅补录首次推送和检查回执，按相同路径同步；.serena/ 始终保持未暂存。
2. 01：逐题完成访谈，更新同一组文件；完成标志为范围、交互、数值预算和真实配置均可执行且有依据。
3. 合同完成后按实际配额并行推进 02、03、06、07，阶段完成即消费产物并推送结论。

## 4. 最值得关注的 3 点

1. miles 两组原范围不同；第二组完整 20 步及评测属于本次建议，尚待确认。
2. miles 测量值没有已校准的通过预算，verl 需要独立数值资格。
3. 新分支和文档准备完成不代表任何 GPU、导出或评分验收通过。

## Staged verification

首次 git diff --cached --check 返回 exit 2，原因是新建文档末尾多了一个空行；此前未暂存的 diff 检查没有覆盖这些新文件。仅修正本次 15 个 Markdown 的末尾空行，重新暂存后检查 exit 0。随后 Python 3.10.6 检查确认暂存范围恰为 GLOSSARY.md 与本任务目录共 15 个文件，未包含 .serena/，未发现所检查的 credential markers。没有实现代码或运行参数变化；这是一次文档格式修正，不影响未决实验范围。

## Publication receipt

执行 git commit 创建 fe8c108edf6dc72b7810fde9917cf7ac0698d2bc（含 Co-authored-by: OpenAI Codex）。git push -u origin agent-opd 成功新建个人远端分支，随后 git rev-parse HEAD 和 git ls-remote --heads origin refs/heads/agent-opd 均返回该完整 SHA。没有发起 PR 或触碰上游。当前仍未运行 GPU；所有 tickets 保持 draft。此回执跟进仅修改 progress 和 test_report，随后普通提交和 push；最终 tip 由当次终端回执核对。

## Execution start

[Original Request] 开始执行

采用上一轮推荐 A：两组各 20 次成功更新与原始/更新后各 80 个有效评分。用户指令进入执行，故不再等待原访谈问题。源训练仍为固定 history 上的新单 turn；原生 benchmark 执行真实工具 episode。

并行职责：runtime_compat 负责 runtime_probe；data_benchmark 负责精确历史/数据适配；alignment_contract 负责 native Agent Loop 观测和数值汇总；root 负责本地 Python RJob launcher、运行、合同和交付。所有修改在同一 branch 协作。

环境观察：本机 /data 可用约 105 GiB，只有小型 Docker 镜像，无现成 verl venv。没有拉取大型镜像到本机。通过公司镜像代理解析 verlai/verl:uv.cu130.dev5 的 amd64 digest；将使用零 GPU worker 的镜像离线缓存，在当前机器挂载的 /data 下 materialize 一套 uv.lock 环境，供后续直接调用。运行脚本不打印 credentials。

## Execution checkpoint: native adapters and environment repair

- Ticket01: source-exact prepared dataset, model/runtime registry, Hydra native recipe, same-token logprob comparison and personal RJob entrypoint implemented. CPU checks do not establish model/runtime qualification. Additional trainer/benchmark integration remains in progress.
- Original CPU environment job `exp-1106-012337-418890`, UID `7182b2ad-7489-412e-83cf-159e4defa102`, requested 0 GPUs/16 CPUs/96000Mi. Creator and local NFS `100.96.128.195:/data/ycfeng:/data/ycfeng` verified. Image eventually pulled; native container exited1 on offline `deep-ep==1.2.1` cache miss. Terminal Failed precedes launcher atexit cleanup. Selected RCA: evidence/runtime-environment-failure.json.
- Repair hypothesis: the pinned wheel is absent from the image cache, while mounted interpreter and venv creation work. Allowing the frozen sync to fetch missing dependencies in a zero-GPU job should populate the persistent environment without changing the lock. Falsifying result: download/version/build failure or affected imports still fail. Repair job `exp-1106-013411-959935`, launcher session66632, same immutable image/source/resources; current business outcome pending. Persistent installation log: /data/ycfeng/tmp/verl-agent-opd-20261106/environment-sync.log.
- CPU checks: Python3.10.6 and existing miles-agent-opd-cpu Python3.12.13 each passed six alignment fault tests. Existing CPU environment imports torch2.11.0+cu130/transformers5.19.0; these are not this task's locked training versions. Prepared dataset CLI import/help passed with explicit PYTHONPATH pointing to verl. The first direct script invocation without that path failed ModuleNotFoundError:verl; no package behavior was changed to hide it.
- Native recipe composition: GLM/Qwen ×2/20 steps constructed through actual Hydra configs. This checks schema composition only; CUDA/model load, 8/80 real turns, numeric budget, full updates and exports remain unverified. Source seed42, LR2e-6, Adam betas0.9/0.98, no warmup/weight decay, PGk1/no task rewards, BF16/FA3 and token IS/rejection0.5–2 are explicit.
- GLM pools planned8 actor+8 teacher, denseTP4 and expertTP1×EP8; Qwen4 actor+4 teacher, denseTP2. Actual GPU allocation, devices, dispatch and collective execution remain pending. No other jobs were controlled.

### Check-progress self-check after adapter CPU milestone

Ticket01 remains TODO; tickets02–10 remain TODO behind recorded dependencies. Mainline frontier is the real environment/data/config qualification in01; runtime, exact-input, trainer observations and native benchmark adaptation progressed in parallel. D1–D7 CLEAR: each adapter supplies evidence required by the next workflow stage, no repeated parameter-tuning loop, and the single environment repair tests the documented cache hypothesis. S1–S6 show no immediate contradiction requiring a scope change. Numerical limits remain deliberately unset rather than copied from Miles residual errors. Next route: finish persistent imports/data receipts, run independent calibration and freeze justified limits, then native qualification and baseline benchmark. Do not add general framework features or broaden CPU test machinery.

## Consumed RCA artifacts cleanup

Selected errors, exact identities, terminal states, event order and query limits are retained in the two evidence/runtime-environment-*.json records. After those receipts were reviewed, task-owned raw collector directories were consumed and removed:

- /data/ycfeng/tmp/rca-exp-1106-012337-418890: 10 files, 93793 bytes; absent after cleanup=True.
- /data/ycfeng/tmp/rca-exp-1106-013411-959935: 10 files, 44678 bytes; absent after cleanup=True.

No model weights, Miles files, active job outputs or unrelated temporary directories were touched. The native environment and live environment-stage log remain in use.

## Native observer commit and second environment diagnosis

- Published initial native adapter milestone `1c1f93f619bdbbb2e0216fabde2e5e9af05eea6f`: ordinary push succeeded and independent ls-remote matched HEAD.
- Native AgentLoop + trainer observer completed in `0fe1880f4a79d7385adee8f192127bb14cfbb46d`. It subclasses the supported native runner/trainer seam, preserves OPD tensors, and observes before actual updates. Completion/parser failures are auxiliary unverified observations. Native optimizer success, one full mini-batch and one epoch establish successful-update counting; final HF receipt waits for native fit/async save completion. Locked native imports/execution still pending.
- Environment repair `exp-1106-013411-959935`, UID `e9b3961b-3178-4be2-9363-695596a0eef6`, failed after container execution on gpu-h800-0080. Pinned tokenspeed PyPI wheel fetch received proxy authorization failure. Container17:38:24–17:38:28Z, exit1/restart0; platformFailed17:38:31Z. Two audit queries timed out and remain unavailable. Selected evidence: evidence/runtime-environment-online-failure.json.
- Handbook already documents pip proxy407 and direct internal PyPI; applying the platform proxy to all package sources was an avoidable routing mistake. CPU host tests show exact PyPI artifact direct200 and exact GitHub artifact through deploy proxy200; the opposite paths timed out. The next hypothesis is PyPI proxy bypass with GitHub proxy retained, keeping exact original URLs/lock hashes. Worker HEAD checks precede sync so the worker route is measured rather than inferred from CPU host.
- Third zero-GPU environment/input job `exp-1106-014156-052221` created01:41:56HKT, launcher session46445. Same personal identity/source/digest/resource shape; no duplicate live environment job. The command now includes prepare.sh after runtime probe: both actual80-turn datasets, exact first8 qualification rows (source preparer interleaves categories), four normal recipe constructions, and frozen native20-question membership. Each output uses its exact new job namespace; no previous output is overwritten.
- Runtime/config review repaired cloud symlink confinement. Pinned MCore uses independent dense and expert rank grids, so GLM world8/TP4/ETP1/EP8 yields denseDP2/expertDP1; the real formula is checked before launch. This topology remains unverified at GPU collective/model execution.

### Check-progress after native observation milestone

All ten tickets remain TODO because actual environment/data/GPU gates are incomplete. D1–D7 remain CLEAR in this window: native observer and benchmark adapters advance01, and the next environment attempt has an explicit source-specific network hypothesis and worker precheck. This is not repeated tolerance tuning or backend substitution. The two failed environment attempts narrowed different causes (missing offline artifact, then routing policy). Do not repeat after an identical route failure; use CPU-host artifact acquisition with the original hashes if worker egress is unavailable. S1–S6: no new scope defect identified; numerical qualification remains an explicit unsatisfied gate. Next action is the current worker's route/sync/import/data output, while benchmark and multi-node native launch integration finish in parallel.


## Native worker/benchmark entrypoints and cache repair

- Stable worker.py/worker.sh join the exact allocated Ray replicas, verify actual devices/interpreters and native update/export receipts, preserve platform NCCL variables and archive/consume task-owned local caches. Stable benchmark.py/benchmark.sh reuse Miles native SWE preparation, RunCheckPipeline, tools, grader and summaries, preserve the frozen 20×4 population, gate further work on four valid first-question seeds, and distinguish valid unresolved from infrastructure missing. Updated runs require the exact step20 export receipt. CPU fixture results validate interfaces/recovery only, not a live benchmark.
- rjob_run.py now optionally forwards only existing native sandbox auth fields after presence checks; values are never printed or stored in task records. No native sandbox call has yet passed.
- Root checks: Python3.10.6 six alignment unittests PASS; bash syntax for benchmark/worker/environment PASS; AST for benchmark/worker/launcher PASS; benchmark run help PASS; worker help PASS with repo PYTHONPATH under CPU Python3.12.13. A direct worker script without that PYTHONPATH failed import tests; the authorized worker.sh supplies it. Prefetch CLI requires Python3.12 tomllib and passed under mounted CPython3.12.13; host3.10 lacks tomllib.
- Third zero-GPU job exp-1106-014156-052221, UID401da978-7273-421c-b232-f510b22cd367, replica1407f5f4-ab53-4761-b018-b491f8baaaa8 on gpu-h800-0039: container17:45:32Z exit22/restart0; platformFailed17:45:37Z. PyPI pinned wheel direct200; worker GitHub proxy407. This disproves transporting CPU-host GitHub route assumptions to workers. Selected evidence: evidence/runtime-environment-route-failure.json. No fourth route-only rerun was submitted.
- CPU host acquired the original five locked native wheels through the original wheelhouse registry and fixed versions. Final cache has five archives/1,472,510,706bytes, original uv.lock SHA df508db0b957fa181c229fb75885cd3863cb651fd5233d0fa5af95e990bda0be. Complete cp-a merged cache followed by uv0.11.16 frozen/offline sync PASS: all five packages, prepare0.59ms/install605ms. This is metadata/cache consumption only. The initial test omitted archive-v0; its failure does not prove a registry-vs-URL cache incompatibility. Retained receipt: evidence/runtime-native-wheel-prefetch.json. Original lock wheel entries do not supply ZIP hashes, so extracted-content hashes are not advertised as lock hash verification.
- Consumed duplicate/target/proof cache artifacts:7,642,059,117bytes removed with per-path receipts. The required supplemental cache and uv0.11.16 tool remain until native environment installation completes, because cache symlinks are absolute. Native venv uses UV_LINK_MODE=copy so its installed files will not depend on that cache afterward.
- After that CPU proof, fourth zero-GPU job exp-1106-015912-607567 was submitted01:59:12HKT, launcher19002. Same immutable image/personal identity/local source/0GPU16CPU96GB. environment.sh non-destructively merges the full supplemental cache into the image cache, retains PyPI direct bypass and uses original frozen lock. Complete sync/import/model/config/data outputs remain pending.

## User-selected numerical standard

[Original Request] 参考steptron的训推一致要求的相关docs的标准

Found and inspected source requirements.md Q59 (lines143–151) and glm-numerical-acceptance-proposal.md (lines10–22) in the behavior-turn-replay-step3p6 task. Adopted engineering standard: both native pack and global token MAE≤0.03, separately per input/completion population, before TIS, same student weight version/token-position-mask/probability. Tails and K3 are diagnostics. This corrects the earlier conclusion that no usable threshold was available. Original Lark retained-response SHA b37402e99ac0c49b2c699720d1975e95930317e6b49e683123fabc95cffba607 was verified by the source-reading agent. This task applies the common standard to both pairs' newly generated completions; it does not inherit the older task's historical rule2 population or model/topology. Numerical code is being aligned with MAE-only acceptance; no artificial tail budgets or independent FP32 expansion.

## 1. 规划完成情况

**汇总：** PASS0｜BLOCKED/FAILED/SKIPPED0｜TODO10

| 子任务 | 状态 | 简要依据 |
| --- | --- | --- |
| 01 | TODO | 缓存安装证明与native入口已交付；完整环境/data、聚合合同待验证 |
| 02 | TODO | GLM真实两步未运行 |
| 03 | TODO | Qwen真实两步未运行 |
| 04 | TODO | 依赖02 |
| 05 | TODO | 依赖03 |
| 06 | TODO | 等待环境/data |
| 07 | TODO | 等待环境/data |
| 08 | TODO | 依赖04/06 |
| 09 | TODO | 依赖05/07 |
| 10 | TODO | 局部消费已清理，最终交付未到 |

## 2. 偏离检测

**结论：** 未偏移，正常推进。
**检测窗口：** 上次native observation checkpoint至今；环境阻塞回溯首次提交｜**当前前沿：** 01环境、真实输入及数值合同

| 模式 | 判定 | 依据 |
| --- | --- | --- |
| D1 工具打磨 | CLEAR | worker/benchmark稳定后停止扩展，cache仅补齐缺失依赖 |
| D2 细节反复重试 | CLEAR | 三次环境结果分别收窄离线缺包、PyPI代理、worker GitHub出口；第四次提交前完整复制offline证明通过 |
| D3 支线问题修补 | CLEAR | 均属于01真实运行前提 |
| D4 可并行任务停滞 | CLEAR | 环境、数值来源、worker和benchmark并行；真实运行共享未完成环境 |
| D5 超范围镀金 | CLEAR | 用户标准找到后停止额外FP32/calibration范围 |
| D6 分析空转 | CLEAR | 结果落实为可安装cache、native入口与明确阈值 |
| D7 路线违背 | CLEAR | 当前用户指令支持执行和标准选择，未变更模型/backend/lock |

**文档检查：** S5：旧预算未决及草案措辞被最新执行指令和用户指定标准取代，已在requirements/plan/01更新；S1–S4、S6未发现新缺陷。
**归因：** 无。

## 3. 纠正建议

**分支：** B：spec/tickets存在过期内容，先更新文档再继续。

**文档更新（先执行）：**
1. requirements/plan/01：记录用户指定Steptron标准和来源，删除额外校准作为阈值前置的旧解释（可直接执行；已应用）。

**需停止的偏离行为：** 无。

**接下去的路线：**
1. 01：当前zeroGPU job完成锁定imports、四组真实配置和两组80turn数据回执。
2. 并行：落实双MAE数值合同；环境就绪后02/03与06/07在实际资源允许下独立启动。
3. 各资格通过后分别从初始权重执行20次有效更新、精确导出与新进程重载，再进行更新后固定评测。

## 4. 最值得关注的 3 点

1. CPU缓存PASS尚未证明完整native环境或模型可用。
2. 数值标准已确定为双MAE≤0.03；实现必须忠实表达原生聚合，不能虚标。
3. 当前没有训练GPU或有效benchmark；继续按真实业务证据推进。


## Fourth worker filesystem failure and next repair hypothesis

Fourth job exp-1106-015912-607567 UID1e015548-8956-46b4-b530-bb9395fd2d81, replicaUIDa7703131-365e-48e0-bfc3-c7f6e3735102, H8000195: creator and local NFS verified; container18:03:36–18:03:40Z exit1/restart0, platformFailed18:03:56Z. New worker log contains2048 cp preserving-permissions errors/318065bytes. uv sync was not reached. Exact selected evidence: evidence/runtime-environment-copy-failure.json. Target filesystem type is UNKNOWN; source sample xattrs are empty, so this is not established as a source ACL defect. The cp failure is inferred from last command/set-e/containerexit1, not a directly captured command status.

Before a fifth attempt, the specific repair hypothesis is that `cp -R -n --no-preserve=all` preserves cache contents and symlinks without requesting the unsupported ownership/mode/ACL/timestamp operations. No dependency/lock/backend change. Falsifiers: content/link copy itself fails, or uv cannot consume copied metadata. The script now reports exact job identity and target stat-f/readlink before copy so the next outcome is attributable. The prior CPU cp-a success did not validate worker metadata support. Native MAE code is ready for CPU verification; no calibration or arbitrary tolerance sweep is added.

Native evaluator import check PASS under existing Python3.10.20 from cwd=/data/ycfeng/tmp with PYTHONPATH ordering native-eval worktree, StepTron root, native SWE src and StepAlign root. Source native adapter, RunCheckPipeline and swe_formal import successfully; pipeline/scorer resolve to step3p6-native-eval-1015z. Running the same stdin check from verl cwd failed tests.e2e import because local tests takes precedence; benchmark launches by absolute script path and uses its explicit native PYTHONPATH. This is import-only, no sandbox or live scoring acceptance.

Personal publication receipt: ordinary push87a764def5ade727fd5b155ddfd8e0ba4a97dcf4 succeeded; independent ls-remote equals localHEAD. .serena remains untouched. Benchmark scheduling review found a real throughput issue: source runs four fixed seed streams concurrently; serializing the first three historical attempts alone would exceed3hours. The adapter is receiving only the necessary four-seed scheduling correction, preserving within-seed order and the first-question four-result gate.


## MAE contract implementation milestone

- settings.json explicitly freezes numerical_limits={mean_abs_diff:0.03}; configure requires the same mapping in agent YAML. Tail/signed/ratio/K3 values remain diagnostics. Raw full-support sampling semantics are checked before comparison; structurally changed sampling becomes soft-unverified.
- Every input is checked separately. Aggregates report the real global token numerator/denominator and MAE. Current native Megatron forward uses complete-row grouping (engine/utils.py prepare_micro_batches and seqlen_balancing.py rearrange_micro_batches), CP1 and dynamic_context_parallel=False. Thus max(per-input MAE) bounds each possible native pack MAE and any subsequent pack/time/DP mean. Report native_pack_mean_abs_diff=null, native_pack_boundary_observed=false, native_pack_acceptance=proven_bounded when that sufficient condition passes. This proves the adopted limit without inventing measured pack boundaries.
- Actual native order computes old logprobs before TIS correction, so observer covers all eligible response tokens before rejection. Missing records, changed versions, wrong tokens/masks/positions and unsupported pack layouts cannot produce outer aggregate PASS. The diagnostic flattened metrics.status can pass despite a failed short input; acceptance consumes the outer by_training_step/step/all/comparisons/pair/status and per-input statuses.
- Eleven alignment regressions PASS on hostPython3.10.6 and CPU Python3.12.13. Owning agent executed the real train aggregation function against a short-input dilution fault and version mismatch; actual AgentLoop rescore function checked raw full-support versus transformed sampling; four realHydra schema compositions PASS. These CPU results are not native GPU numerical qualification.
- Check-progress self-check: milestone remains within01, all ten ticketsTODO; D1–D7 CLEAR because changes implement the now-defined criterion and stop after affected checks. No new scope/threshold/reference/FP32 expansion; S1–S6 no new inconsistency. Next route remains real environment/data, then both2stepqualifications and original benchmarks in parallel.
- Fifth zero-GPU job exp-1106-020650-487444 created02:06:50HKT, launcher65336alive; exact target filesystem and content-copy result pending. No training GPU allocated.


Benchmark scheduling correction: source Miles uses four fixed seed streams; measured historical first-question generation3738.97/4053.83/4095.01seconds plus grading107–114seconds explains the cost of serial execution. Adapter now joins four concurrent q0 results before advancing, then each seed executes q1..19 in order. SGLang max-running-requests derives from the frozen seed count4. No additional scheduler/CLI flags; per-attempt locks, valid-result reuse and unknown-active preservation remain. CPU mock checks PASS for observed maxconcurrency4, no same-seed overlap, q0 gate, full resume0newattempts, missing-only77, known-active preservation and local-child interruption under3seconds despite21600second attempt timeout. Only benchmark.py changed; no live grader result claimed.
