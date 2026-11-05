## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |

# 05: Frog/Qwen 第 20 次更新的导出与重载

**What to build:** 在两组对称完整测试的建议范围下，为 Qwen 完成 20 次更新、完整最终权重导出和实际重载；该扩展尚待第一题确认。

**Blocked by:** 03: Frog/Qwen 两步真实 OPD 与训推一致性.

**Status:** draft — interview pending; not approved for runtime execution.

- [ ] 先获得两组对称范围的实际确认；若用户保留来源范围，本 ticket 在原文调整或明确 skipped，不假装已获执行授权。
- [ ] 完成 20 次成功 optimizer update，保留正确 teacher/student 身份、实际输入和数值观测。
- [ ] 核对 hybrid attention 所需参数、权重映射及文本推理产物完整性；最终权重确属第 20 次更新。
- [ ] 在新推理实例加载最终权重并实际生成，验证最终更新已进入推理。
- [ ] 仅在后续消费者结束后删除最终权重；其余临时产物及时消费。
