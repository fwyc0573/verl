## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Reuse the updated benchmark's first native server/generation for reload acceptance after verified export. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 05: Frog/Qwen 第 20 次更新的导出与重载

**What to build:** 为 Qwen 完成 20 次更新、完整最终权重导出和实际重载。

**Blocked by:** 03: Frog/Qwen 两步真实 OPD 与训推一致性.

**Status:** pending — predecessor acceptance required.

Verified complete update20 HF export releases09 serving/scoring before this ticket closes. Reuse that benchmark's new native SGLang process and actual generation for the reload criterion below. The first real reload/generation can close this ticket while09 continues scoring; no separate inference job or completed baseline is required.

- [ ] 按最新“开始执行”指令落实两组对称范围，采用原始 Qwen 权重开始独立 20 步测试。
- [ ] 完成 20 次成功 optimizer update，保留正确 teacher/student 身份、实际输入和数值观测。
- [ ] 核对 hybrid attention 所需参数、权重映射及文本推理产物完整性；最终权重确属第 20 次更新。
- [ ] 在新推理实例加载最终权重并实际生成，验证最终更新已进入推理。
- [ ] 仅在后续消费者结束后删除最终权重；其余临时产物及时消费。
