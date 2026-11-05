## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 07: 原始 Qwen 的固定 20 题评测

**What to build:** 取得原始 Qwen 在同一固定题目上的真实 agent 评测基线。

**Blocked by:** 01 runtime and verified fixed benchmark inputs; independent of either training dataset. Existing native benchmark preparation must pass before server/scoring starts.

**Status:** in-progress — submitted exp-1106-030308-817360; platform Pending/queuing at03:04:17HKT, no serving or score yet. Existing benchmark preparation must validate the frozen membership before server/scoring.

- [ ] 验证 Qwen 原生工具和 reasoning 解析能完成真实 episode 与 grader。
- [ ] 同一固定 20 题、四 seeds 得到 80 个有效结果；使用该模型适用且前后保持一致的 template 和采样合同。
- [ ] missing、有效 unresolved 与 resolved 分开；记录真实运行身份、avg@4 和每题结果。
- [ ] 可在 Qwen 训练期间独立执行，遵循实际共享 GPU 配额和及时消费规则。
