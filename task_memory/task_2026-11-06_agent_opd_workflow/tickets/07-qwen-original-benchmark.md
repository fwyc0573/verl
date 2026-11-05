## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |

# 07: 原始 Qwen 的固定 20 题评测

**What to build:** 在对称测试范围确认后，取得原始 Qwen 在同一固定题目上的真实 agent 评测基线。

**Blocked by:** 01: 冻结并验证两组 workflow 合同.

**Status:** draft — interview pending; not approved for runtime execution.

- [ ] 先取得该范围的实际确认，再验证 Qwen 原生工具和 reasoning 解析能完成真实 episode 与 grader。
- [ ] 同一固定 20 题、四 seeds 得到 80 个有效结果；使用该模型适用且前后保持一致的 template 和采样合同。
- [ ] missing、有效 unresolved 与 resolved 分开；记录真实运行身份、avg@4 和每题结果。
- [ ] 可在 Qwen 训练期间独立执行，遵循实际共享 GPU 配额和及时消费规则。
