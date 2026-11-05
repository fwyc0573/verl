## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Close actual runtime/input/configuration contract; retain all GPU acceptance gates in successor tickets. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 01: 冻结并验证两组 workflow 合同

**What to build:** 将来源任务和 verl 原生入口落实为两个可复现、可验证的运行合同，消除范围、数据、工具交互和数值验收歧义。

**Blocked by:** None (can start immediately).

**Status:** done — actual native runtime, both80/8 datasets,2/20recipes and canonical benchmark inputs verified; GPU training and numerical acceptance belong to02/03.

Independent readiness: zero-GPU input job exp-1106-032827-028041 actually passed both models'80-row learning datasets,8-row qualification datasets and2/20 native configurations, then Succeeded/exit0. All80 source UIDs/order match original Miles selection; Qwen tokens use its own complete template. Canonical benchmark membership is independently frozen at fixed-benchmark/benchmark/membership.json, SHA0f4ab340bedb7a64f3089af679be829aefcf8ecbbeb11c3a164578ba6b702877. Runtime imports/config-only dispatch are verified. CUDA construction, optimizer updates, same-weight numerical PASS, HF value change and actual grader results remain open in later tickets.

- [x] 记录“开始执行”的最新指令和采用的推荐矩阵：两组各 20 次更新、原始/更新后各 80 份有效评分；沿用来源单 turn 训练。
- [x] 固定模型 revision、tokenizer/template、真实输入及训练/评测排除关系；按各模型 tokenizer 验证长度和四种来源类别，超长样本不静默截断。
- [x] 采用用户指定 Steptron Q59 合同：native pack MAE 与 global token MAE 均≤0.03，tails/K3仅诊断；实现准确的 native 聚合及同版本/token-position-mask 检查，覆盖原始及更新后权重。标准与observer实现及CPU回归已完成；GPU实测验收属于02/03。
- [x] 复用原生 OPD、Agent Loop、teacher scoring、路由记录、导出及 native grader；验证真实配置可以构建，明确目标模型支持缺口。
- [x] 冻结 GPU 数量和训练/rollout/teacher 拓扑、精度、backend、loss、采样及版本；复用已存在的机制，记录确需修改的最小范围。
- [x] 若 benchmark 被确认，固定 20 个题目、四个 seeds、完整分母和原生评分合同；不得在看到结果后换题。
- [x] 明确本任务运行身份、临时目录和产物依赖；完成相关 CPU/preflight 检查及精确命令记录后才标记 done。
