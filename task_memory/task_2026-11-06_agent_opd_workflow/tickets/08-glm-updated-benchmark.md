## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |

# 08: 第 20 步 GLM 的评测与学习结果

**What to build:** 用精确第 20 次更新 GLM 完成同题同 seed 评测，与原始基线比较并报告学习结果。

**Blocked by:** 04: GLM 第 20 次更新的导出与重载; 06: 原始 GLM 的固定 20 题评测.

**Status:** draft — interview pending; not approved for runtime execution.

- [ ] 实际评测载入的是已验证的第 20 次更新权重；同样 20 题四 seeds 有 80 个有效 grader 结果。
- [ ] 前后环境、工具、grader 和采样合同一致；不能混合不同 sandbox 合同的结果。
- [ ] 计算两版本 avg@4、配对分数差和按题 bootstrap 区间；没有改善也如实报告，不把功能通过等同学习收益。
- [ ] 数值一致性、workflow、导出重载、评分完整性与学习效果单独给出结论。
- [ ] 比较完成后消费最终权重与全部原始评测产物，保存精简 Markdown 结论和清理证据。
