## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 02: GLM 两步真实 OPD 与训推一致性

**What to build:** 让 GLM student 在真实 agent 输入上生成新 completion，由固定 Coder teacher 评分，完成两次有效更新，并通过约定的同 student 训推数值验收。

**Blocked by:** 01: 冻结并验证两组 workflow 合同.

**Status:** pending — predecessor acceptance required.

- [ ] 使用冻结的真实数据与交互边界，teacher 实际评分的 token IDs 与当前 student 采样一致。
- [ ] thinking、正文和工具信号的源字段、tokens、mask、实际生成覆盖分别可核验；MoE routes 按约定真实录制并 replay。
- [ ] 两次实际更新具有有限 loss/梯度和有效权重变化；初始及更新后 rollout 对应正确 student 权重，最终更新也发布并验证。
- [ ] 在相同 tokens、权重、概率定义上比较 decode、独立 prefill 和 trainer，按冻结预算逐项 PASS；缺失或超限不得以 TIS 掩盖。
- [ ] 记录真实硬件、代码/环境身份、job/replica 和业务/终态证据；消费不再依赖的临时产物。
