## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record execution steering and carry the recommended symmetric test matrix into execution. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# Requirements

## Original requests

[Original Request]
`$grill-with-docs 创建task和tickets，复刻任务（miles的/data/ycfeng/sota-engine/miles下的task），核心为对2个model组合执行在verl下的agent opd 完整workflow测试（包括确认训推一致性通过），及时清理产物`

[Original Request]
`补充：在new branch下执行，并及时推送到我的repo`

## Confirmed scope

- 在 verl 复刻 miles agent OPD 任务，覆盖以下两个独立 teacher → student 组合：
  - GLM-4.7-Flash-Coder → GLM-4.7-Flash。
  - FrogNano-4B-2609 → Qwen3.5-4B。
- 两组均须取得真实 workflow 和训推一致性验收结果。准备完成、训练进程退出成功、参数已启用、teacher/student 分布不同，均不能替代同一 student 的训推数值验证。
- 创建 task 和逐项 tickets，按 grill-with-docs 逐题确定关键设计选择。当前文件是可审阅草案；尚未确认的方案不得作为执行决定。
- 在新 branch 工作，及时将已验证的阶段成果推送到个人 repo。已核对 origin 为 https://github.com/fwyc0573/verl.git；本次新建 branch 为 agent-opd，起点为 e41dd697abd7d5a583c0b46b1cedb821ba402db3。
- 及时清理本任务不再被依赖的临时数据、原始日志、编译缓存、测试权重和 benchmark 产物；保留可复用代码及精简 Markdown 验证结论。保护共享模型、原始数据、miles 的工作和其他任务。
- 当前仓库原有未跟踪的 .serena/ 与本任务无关，保持原状，不暂存。
- 最新“开始执行”指令授权进入实施与真实测试。按上一轮推荐 A 推进两组对称的 20 次更新与完整前后评测；沿用来源单 turn 训练，执行中据实冻结技术配置。

## Source task and inheritance limits

来源为 /data/ycfeng/sota-engine/miles/task_memory/task_2026-11-05_agent_opd_warmup/ 下的 requirements.md、plan.md、progress.md 和两份 test_report。来源说明与 verl 复刻证据分别记录；miles 的通过结论不自动成为 verl 的通过结论，来源任务授权也不自动授权操作其作业或产物。

| 项目 | 本次已读取的 miles 记录 | verl 草案 |
| --- | --- | --- |
| GLM 训练和评测 | 20 次成功更新；原始和第 20 步各 20 题、四 seeds | 执行 20 次有效更新及两个版本各 80 个有效结果 |
| Frog/Qwen 训练和评测 | 8 H800、两次更新；明确未扩展到完整 benchmark | 执行与 GLM 相同的完整验收深度 |
| 训练输入 | Ticket07 glm5.2 原始 turn；GLM 80 turns、四类各 20 | 复用来源与排除约束；实际 Qwen 长度和类别须单独验证 |
| 训练交互 | 固定历史前缀上由当前 student 生成一个新 turn，再由 teacher 评分 | 沿用来源单 turn；真实多轮工具执行由原生 SWE 评测覆盖 |
| benchmark | Ticket06 fixed50 确定性选 20 题，继承 fixed175 排除；原生 SWE agent、工具和 grader | 复用固定题目与评分含义；实际 sandbox 可用性待验证 |
| 训推误差 | 已记录 trainer/decode/prefill 残差；没有校准后的数值通过阈值 | 必须单独定义并取得真实 PASS |
| 硬件 | 最后明确切换为 H800/codesign | 沿用当前工作区 H800/codesign 默认；实际总配额和每组布局待执行前核验 |
| 清理 | 消费后删除任务临时产物，保留共享前提 | 相同原则，使用独立 verl 命名空间 |

历史来源中 GLM 一次运行的 trainer/decode 平均绝对 logprob 差范围为 0.005970–0.035865、最大单 token 差 1.597615；报告明确拒绝据此宣称数值通过。Frog/Qwen 的实际两步记录也区分 workflow PASS 与数值资格，并指出最终第二步尚未由原 driver 发布。上述数值只解释本次新增验收需求，不是容差或当前作业状态。

## Execution steering

[Original Request] 开始执行

- 将该指令作为从已推送草案进入实施的明确要求，按上一轮推荐 A 执行：两组各 20 次成功更新，原始和更新后各 20 题 × 4 seeds，总计 320 个有效评分。用户未逐项重述矩阵，此处记录执行解释；如有后续纠正，以新指令为准。
- 复刻来源的固定历史前缀 + 当前 student 新单 turn；完整 SWE 工具交互与 grader 在 benchmark 执行。若需要训练中多轮工具交互，属于另一个明确能力，不混淆两者证据。
- 不继续等待逐题访谈。后端、配置、数值校准和资源布局按源代码、锁定环境和真实检查自主确定并记录；未有依据的数值 PASS 不得宣称。
- 使用当前 verl 的 uv.lock 及原生 megatron+sglang 作为首选；已从公司镜像代理解析 uv.cu130.dev5 的 amd64 manifest digest 466853285884bccd04c85f1c474cf5c4cc8f3ba4348d893f10de7738d3efc504。该解析只证明镜像身份，实际环境尚待验证。
- 20 步学习测试在各组两步资格完成后独立从原始权重启动；资格两步不混入 20 步计数。

## Acceptance common to both pairs

- 数据来源、student/teacher 身份、tokenizer/template 和历史消息对应关系可追溯。历史 completion 用于来源分类和检查；OPD loss 使用当前 student 新生成的 completion。
- thinking、普通正文和 tool call（包括 submit）的表示、原始 tokens 和训练 loss mask 可验证。来源类别、序列化测试和真实生成的类别覆盖分别报告，缺失类别不能凭空记为已覆盖。
- Frozen teacher 实际为 student 采样 tokens 评分；两组的训练更新有限、梯度有效、权重变化及发布版本有证据。
- 在一致性检查中同时报告 student decode、独立 prefill、trainer forward；固定权重版本、token IDs、位置、mask 和概率定义。GLM 的适用 MoE routes 要有真实 replay 证据；dense Qwen 不要求 MoE R3。
- 分组报告有效 token 数、mean/p95/p99/max 绝对 logprob 差、signed mean 和 importance-ratio 异常比例；按信号类型与长度检查。TIS 是校正机制，不构成数值通过证据。
- 若采用 20 步范围，以 20 次实际成功 optimizer update 计数；验证精确最终权重的完整导出、新进程重载及生成。目录名和 trainer loop index 不单独证明第 20 步身份。
- 若采用 benchmark 范围，avg@4 是每题四个有效 grader 分数的均值再对 20 题求均值；每个模型版本需要 80 个有效结果。基础设施错误计 missing，合法 unresolved 计模型失败；不得以 pass@4 替代。
- 每阶段核对当前任务的精确 job/UID、资源和业务输出，分别报告 Pending/Running/终态、CPU/preflight、workflow、数值、导出和评分结论。
- 结论记录后按依赖及时消费临时产物，最终确认任务临时目录已清空、任务作业已结束。精简 Markdown 记录删除目标、文件数/字节数和复核结果。
- 每个已验证的代码步骤提交并及时普通 push 到个人 agent-opd；独立核对远端 SHA。最终关闭前重读本文件。

## Out of scope unless separately requested

正式长训练、视觉训练资格、训练算法的大范围改写、上游 PR、miles 作业控制及产物删除。未发生需要 ADR 的长期架构取舍；暂不创建 ADR。
