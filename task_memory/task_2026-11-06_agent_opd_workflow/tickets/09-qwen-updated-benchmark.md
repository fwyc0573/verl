## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Allow updated scoring after export; require baseline completion only for the final comparison. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 09: 第 20 步 Qwen 的评测与学习结果

**What to build:** 在确认的对称范围内完成 Qwen 更新后评测和前后比较，取得第二组独立的完整测试结论。

**Blocked by:** 05 verified complete update20 HF export for serving/scoring. This benchmark's first new native server/generation supplies05 reload evidence. Completed07 is required only for final before/after comparison, not for launching updated-model scoring.

**Status:** pending — predecessor acceptance required.

- [ ] 载入真实第 20 次更新权重，完成同一 20 题四 seeds 的 80 个有效原生 grader 结果。
- [ ] 与原始 Qwen 的工具、环境、grader、采样和分母一致，报告配对 avg@4 差及按题 bootstrap 区间。
- [ ] 分别报告数值资格、最终权重重载、评测完整性和学习效果，不借用 GLM 的通过结论。
- [ ] 输出消费结束即删除本组临时权重、轨迹、原始日志和结果文件，仅保留所需 Markdown 结论。
