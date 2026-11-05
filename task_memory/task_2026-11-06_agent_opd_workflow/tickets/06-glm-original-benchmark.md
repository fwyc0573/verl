## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 06: 原始 GLM 的固定 20 题评测

**What to build:** 使用固定原始 GLM 权重完成真实 SWE agent、工具执行和原生 grader 的 20 题四 seed 基线。

**Blocked by:** 01 runtime and verified fixed benchmark inputs; independent of either training dataset. Existing native benchmark preparation must pass before server/scoring starts.

**Status:** in-progress — submitted exp-1106-030308-839669; platform Pending/queuing at03:04:17HKT, no serving or score yet. Existing benchmark preparation must validate the frozen membership before server/scoring.

- [ ] 确认 benchmark 范围后，对冻结的 20 题和四 seeds 获取 80 个有效原生评分，模型权重/环境/采样/超时身份完整。
- [ ] 基础设施错误保留为 missing，合法 unresolved 作为模型失败；先取得可用的原生结果再扩大提交。
- [ ] 缺失恢复先核对精确现存作业和结果，不重复有效或正在健康运行的 attempt。
- [ ] 记录 avg@4 与每题四个有效分数以供后续比较；消费轨迹和原始日志时保留计算所必需的精简结果。
