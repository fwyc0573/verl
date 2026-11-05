## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record actual original serving, four infrastructure failures, and canonical token environment repair. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 07: 原始 Qwen 的固定 20 题评测

**What to build:** 取得原始 Qwen 在同一固定题目上的真实 agent 评测基线。

**Blocked by:** 01 runtime and verified fixed benchmark inputs; independent of either training dataset. Existing native benchmark preparation must pass before server/scoring starts.

**Status:** in-progress — exp-1106-030308-817360 loaded original Qwen TP2 and model_info200, then failed all four first-question seeds with sandbox SessionRouter HTTP401. No valid grades. The literal ${SESSION_ROUTER_USER_TOKEN} reached native auth because only SR_USER_TOKEN was forwarded; the existing child environment now supplies the canonical name with canonical precedence. CPU native-config regression passed; same-population missing-only retry exp-1106-033246-436787 / UIDf5c97c61-7868-44f6-8a74-34ab529bd6b2 submitted2H800/12CPU/150GB andPending/queuing at03:37:58HKT. No valid scores yet.

- [ ] 验证 Qwen 原生工具和 reasoning 解析能完成真实 episode 与 grader。
- [ ] 同一固定 20 题、四 seeds 得到 80 个有效结果；使用该模型适用且前后保持一致的 template 和采样合同。
- [ ] missing、有效 unresolved 与 resolved 分开；记录真实运行身份、avg@4 和每题结果。
- [ ] 可在 Qwen 训练期间独立执行，遵循实际共享 GPU 配额和及时消费规则。
