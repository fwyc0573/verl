## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Reuse the updated benchmark's first native server/generation for reload acceptance after verified export. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 04: GLM 第 20 次更新的导出与重载

**What to build:** 执行已通过资格检查的 GLM 学习测试，取得可在新推理实例实际使用的精确第 20 次更新权重。

**Blocked by:** 02: GLM 两步真实 OPD 与训推一致性.

**Status:** pending — predecessor acceptance required.

Verified complete update20 HF export releases08 serving/scoring before this ticket closes. Reuse that benchmark's new native SGLang process and actual generation for the reload criterion below. The first real reload/generation can close this ticket while08 continues scoring; no separate inference job or completed baseline is required.

- [ ] 在确认的实验范围内完成 20 次成功 optimizer update，逐步记录版本和有效数值；原先两步资格是否另起运行由合同明确。
- [ ] 保持已通过的一致性配置，检查运行期间版本、tokens、routes 和误差观测；异常按原生故障与观测缺失分别处理。
- [ ] 导出最终推理所需的完整权重、index/config/tokenizer，并核对结构及第 20 次更新身份。
- [ ] 新推理实例实际重载最终权重，验证模型身份并生成；文件存在不替代重载。
- [ ] 最终权重保留到更新后 benchmark 消费完成，其余无依赖中间 checkpoint/缓存及时删除。
