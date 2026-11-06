## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Record actual worker start and fused recipe for the current Qwen qualification. |
| 2026-11-06 | Record actual old-logprob OOM and the verified native fused configuration. |
| 2026-11-06 | Record actual qualification failure or running original benchmark evidence on resume. |
| 2026-11-06 | Submit the real qualification after complete Qwen input/configuration PASS. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 03: Frog/Qwen 两步真实 OPD 与训推一致性

**What to build:** 让 Qwen student 使用 FrogNano teacher 完成真实两步 OPD，并取得 Qwen 自己的训推一致性结果。

**Blocked by:** 01 Qwen runtime/input/config prerequisites; independent of GLM training inputs and original benchmarks.

**Status:** in-progress — current exp-1106-150433-589683 / UIDd44e6e31-fe09-47f6-8be6-5dbf0d233a6d, launcher38117. Created15:04:33HKT after8e776dcfcaf2a9b7736d2781195c0f291833027a push/remote match and exact previousFailed reread15:04:12. Actual worker started15:12:43HKT onH8000182; archived recipe confirms fusedtrue/use_ligerfalse/MTPfalse/remove_paddingtrue and unchanged input/length/batch/dynamic budgets. Training Progress0/2 at15:19:07; actual old-logprob CUDA, numerical, update and HF2 gates remain open. Same1×8H800/32CPU300GB/currentNFS/pinnedimage/input; only Qwen fused output option changes. Previous709386 failed native old-logprob logits.clone OOM with no verified update or HF2. Native configuration4/4PASS and source-compatible output hook do not prove CUDA runtime, three-way MAE, two updates, version publication or changed values.

- [ ] 实际加载两个固定模型，验证同对 tokenizer/template 兼容性和 Qwen 渲染后的真实历史/长度，不直接套用 GLM token IDs。
- [ ] 按合同覆盖 reasoning、正文和工具表达；teacher 评分 tokens、student tokens 及 loss mask 对齐。
- [ ] 实际验证 Qwen 的 hybrid attention 文本路径；dense 模型的 MoE R3 标记不适用，不声称视觉训练通过。
- [ ] 完成两次有限有效更新，并验证包含最终一次更新的实际权重发布。
- [ ] decode、独立 prefill、trainer 的同 student 对比按冻结预算逐项 PASS；不得仅使用 tokenizer 相等、梯度非零或来源两步记录。
- [ ] 记录 job/环境/业务/终态和分类统计；及时消费不再依赖的产物。
