## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Close verified input/configuration prerequisites and record four independent GPU jobs. |
| 2026-11-06 | Use model-specific run settings to resolve measured Qwen input underfill without changing populations. |
| 2026-11-06 | Correct coarse prerequisites so model qualification and original benchmarks advance independently. |
| 2026-11-06 | Adopt the user-selected Steptron numerical standard; record cache repair and native launch adapters. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# Plan

## Execution status

用户已指示“开始执行”。按上一轮推荐的两组对称 20 步及前后评测推进，使用已创建的 agent-opd 分支。01 的 native runtime、两组80/8输入、2/20配置和 benchmark 题单均已实际通过并关闭。两组资格与原始评测均已独立提交；原始 Qwen 首次因 sandbox token 环境变量未解析失败，最小修复通过原生配置解析回归后已重提，实际鉴权及有效评分仍待验证。代码、配置和每阶段结论及时提交/push，临时产物随消费随清理。

Qwen 在原61440预算下真实候选不足14/15/17/20；采用模型原生支持内的独立 qwen-settings.json：context131072、response4096、训练/logprob预算131072。prepare.sh 从 pairs.json 的既有模型条目选择明确 settings 文件并推导 prompt 预算，复用同一 preparation/configuration 路径。GLM settings.json 的65536合同保持。新的Qwen输入已实际80/8行和2/20步配置PASS，其8GPU资格已提交；不截断、不减类别、不降低数值门槛。

首选 native megatron+sglang，固定 company image amd64 digest，创建挂载本地目录中的持久环境。先在 CPU host 补齐原锁定 GitHub wheels 并验证完整 cache 合并后的 frozen/offline 安装，再用零 GPU CPU worker 从镜像及补充 cache materialize 环境并执行真实 imports/config/tokenizer/index preflight；该环境此后由训练直接使用，正常训练不安装依赖。该阶段不读大 tensor，不把配置检查当作模型加载或数值通过。

## Tickets

| ID | Deliverable | Blocked by |
| --- | --- | --- |
| [01](tickets/01-workflow-contract.md) | 冻结两组执行合同，并验证真实数据和配置可到达运行入口 | None |
| [02](tickets/02-glm-alignment.md) | GLM 真实两步 OPD 和同一 student 训推一致性 | 01: GLM runtime/input/config prerequisites |
| [03](tickets/03-qwen-alignment.md) | Frog/Qwen 真实两步 OPD 和同一 student 训推一致性 | 01: Qwen runtime/input/config prerequisites |
| [04](tickets/04-glm-update20.md) | GLM 20 次更新、精确最终权重导出和重载 | 02 |
| [05](tickets/05-qwen-update20.md) | Frog/Qwen 20 次更新、精确最终权重导出和重载 | 03 |
| [06](tickets/06-glm-original-benchmark.md) | 原始 GLM 在固定题目上的 80 个有效原生评分 | 01: runtime and fixed benchmark inputs |
| [07](tickets/07-qwen-original-benchmark.md) | 原始 Qwen 在同一固定题目上的 80 个有效原生评分 | 01: runtime and fixed benchmark inputs |
| [08](tickets/08-glm-updated-benchmark.md) | 第 20 步 GLM 的 80 个评分和前后比较 | 04, 06 |
| [09](tickets/09-qwen-updated-benchmark.md) | 第 20 步 Qwen 的 80 个评分和前后比较 | 05, 07 |
| [10](tickets/10-cleanup-and-delivery.md) | 两组结果归档、最终清理及分支同步 | 08, 09 |

依赖：01.GLM -> 02 -> 04; 01.Qwen -> 03 -> 05; 01.benchmark -> {06,07}; {04,06} -> 08; {05,07} -> 09; {08,09} -> 10。01整体在所有子交付完成后关闭；一个模型的输入失败不能阻挡已满足真实前提的另一模型。原生benchmark prepare可在对应worker启动阶段完成，必须在server/评分启动之前验证固定题单和真实digest。

确认合同后，02、03、06、07 不互相等待，可在实测配额允许时并行运行独立 RJobs。运行合同的代码适配已由并行 sub-agents 协作实现。每项完成即可消费不再依赖的临时产物并推送代码/结论；10 仅负责最终核对，不能成为延迟日常清理或推送的理由。

## Reuse and code anchors

- 复用 verl 原生 AgentLoopWorker 的 teacher dispatch、response_mask、rollout_log_probs 与 routed_experts 传递，参考 verl/experimental/agent_loop/agent_loop.py 和 tool_agent_loop.py。
- 复用 verl/experimental/teacher_loop/ 的独立 teacher 池与 distillation 配置；同一 student 的数值对比不以 teacher 为 reference。
- 已读取 examples/on_policy_distillation_trainer/run_qwen3_5_4b_fsdp.sh；它是 Qwen3.5 的现有入口，默认 geo3k/视觉与本任务不一致，必须核对并配置文本任务。它的存在不证明 Frog/Qwen 在 H800 上已兼容。
- 复用 verl/workers/config/actor.py 的 RouterReplayConfig 与 examples/router_replay/；GLM 模型支持、实际后端 routes 和选定运行镜像仍待验证。
- 复用仓库 rollout correction 和已有连续 token/工具调用测试。只补充实际覆盖缺口；不另建通用训练框架、工具系统或评测器。
- miles/examples/agentic_opd/rollout.py 的 generate 当前生成单个新 turn；历史字段与解析结果作为观测。miles/tests/manual/agent_opd/alignment.py 提供独立 prefill 观测模式，可迁移语义，不能直接宣称适用 verl。
- 复用 miles 测试所采用的原生 SWE agent、工具与 grader 接口及 Ticket06/07 输入定义。具体环境和引用路径在 ticket01 中核验；不要复制其临时结果或操控仍在运行的任务。

## Verification and operational boundaries

1. 规划阶段已完成并推送。当前执行阶段依次验证持久环境、真实输入、两组 GPU 资格及后续 20 步/评测。
2. ticket01 冻结实际命令、uv 管理的 Python 环境、镜像、模型 revision、精度、后端、batch/length/loss/sampling、采用 Steptron Q59 的双 MAE≤0.03 合同及固定题目。不得从示例默认参数推断已经批准的实验参数。
3. 每个执行 ticket 以真实输入和运行证据判定，记录预期、实测值和 PASS/FAIL/UNVERIFIED；只添加必要的可重复回归测试。
4. 运行前遵循 StepMind handbook、个人 RJobBackend、H800/codesign 默认、当前机器 source mount 和 launcher 生命周期要求。所有云读写限制在 /mnt/codesign-exp/ycfeng 内本任务或明确复用的共享输入。
5. 本任务临时本地根建议 /data/ycfeng/tmp/verl-agent-opd-20261106；云端根建议 /mnt/codesign-exp/ycfeng/verl/agent-opd-20261106。本地目录已由环境 job 创建；云端根尚待真实数据阶段创建。为每次运行保留独立身份，不复用 miles 输出目录。
6. 原生训练故障与辅助观测故障分别处理。任何辅助观测出错先标记 unverified，不以其异常结束健康训练；32 卡及以上运行严格遵循工作区 soft-gate 规则。合格结论仍必须等证据齐全。
7. 每个关键交付后执行 check-progress 自检并先应用必要纠正。最终交付 summary.md 使用 English，并逐项对应 requirements.md；不把当前草案记为完成任务。
