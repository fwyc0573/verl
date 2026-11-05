## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |

# 01: 冻结并验证两组 workflow 合同

**What to build:** 将来源任务和 verl 原生入口落实为两个可复现、可验证的运行合同，消除范围、数据、工具交互和数值验收歧义。

**Blocked by:** None (planning can proceed; runtime work waits for the interview outcome).

**Status:** draft — interview pending; not approved for runtime execution.

- [ ] 记录访谈实际答复，确认两个模型组合各自的更新次数、benchmark 范围及训练中是否真实执行工具；推荐值与决定分开。
- [ ] 固定模型 revision、tokenizer/template、真实输入及训练/评测排除关系；按各模型 tokenizer 验证长度和四种来源类别，超长样本不静默截断。
- [ ] 确定有依据的同 student 数值误差预算、reference 和独立校准方法，在资格测试前冻结；覆盖原始权重及更新后权重。
- [ ] 复用原生 OPD、Agent Loop、teacher scoring、路由记录、导出及 native grader；验证真实配置可以构建，明确目标模型支持缺口。
- [ ] 冻结 GPU 数量和训练/rollout/teacher 拓扑、精度、backend、loss、采样及版本；复用已存在的机制，记录确需修改的最小范围。
- [ ] 若 benchmark 被确认，固定 20 个题目、四个 seeds、完整分母和原生评分合同；不得在看到结果后换题。
- [ ] 明确本任务运行身份、临时目录和产物依赖；完成相关 CPU/preflight 检查及精确命令记录后才标记 done。
