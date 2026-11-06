## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record actual qualification failure or running original benchmark evidence on resume. |
| 2026-11-06 | Submit the real qualification after complete Qwen input/configuration PASS. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 03: Frog/Qwen 两步真实 OPD 与训推一致性

**What to build:** 让 Qwen student 使用 FrogNano teacher 完成真实两步 OPD，并取得 Qwen 自己的训推一致性结果。

**Blocked by:** 01 Qwen runtime/input/config prerequisites; independent of GLM training inputs and original benchmarks.

**Status:** in-progress — exp-1106-140853-397005 / UID f400952c-ee74-4b55-8f2b-26828705a417 failed at14:22:07HKT after primary student generation returned, before any update. Native task reward dispatch rejected data_source=qwen; an earlier unsupported detokenize prefill parameter was correctly isolated as an auxiliary unverified observation. The scoped task-loop repair supplies zero task reward under the existing use_task_rewards=false contract and removes that unsupported prefill key. Native CPU dispatch regression and pinned API checks pass; another GPU qualification is required. Teacher scoring, valid generated token population, MAE, two updates, versions and HF2 weight changes remain unverified.

- [ ] 实际加载两个固定模型，验证同对 tokenizer/template 兼容性和 Qwen 渲染后的真实历史/长度，不直接套用 GLM token IDs。
- [ ] 按合同覆盖 reasoning、正文和工具表达；teacher 评分 tokens、student tokens 及 loss mask 对齐。
- [ ] 实际验证 Qwen 的 hybrid attention 文本路径；dense 模型的 MoE R3 标记不适用，不声称视觉训练通过。
- [ ] 完成两次有限有效更新，并验证包含最终一次更新的实际权重发布。
- [ ] decode、独立 prefill、trainer 的同 student 对比按冻结预算逐项 PASS；不得仅使用 tokenizer 相等、梯度非零或来源两步记录。
- [ ] 记录 job/环境/业务/终态和分类统计；及时消费不再依赖的产物。
