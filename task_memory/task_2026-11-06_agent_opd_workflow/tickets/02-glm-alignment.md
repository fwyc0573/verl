## Modification History

| Date | Change |
| --- | --- |
| 2026-11-06 | Keep numerical failure separate from native memory failure and prepare the next qualification. |
| 2026-11-06 | Record fourth actual GLM qualification after the pushed shared SGLang fix. |
| 2026-11-06 | Record actual qualification failure or running original benchmark evidence on resume. |
| 2026-11-06 | Create the source-grounded planning draft; execution decisions remain open. |
| 2026-11-06 | Start execution on user instruction; record active scope and verified stage evidence. |

# 02: GLM 两步真实 OPD 与训推一致性

**What to build:** 让 GLM student 在真实 agent 输入上生成新 completion，由固定 Coder teacher 评分，完成两次有效更新，并通过约定的同 student 训推数值验收。

**Blocked by:** 01 GLM runtime/input/config prerequisites; independent of Qwen training inputs and benchmark preparation.

**Status:** in-progress — last exp-1106-144604-954702 / UID731dd5f3-f5db-485b-a8e3-ba8879043933 Failed15:12:38HKT. Step1 has actual global MAE FAIL in all three comparisons; one native update call failed with no verified successful update and optimizer effect unknown. Ray memory used reached629140910080B of629145600000B and killed two AgentLoopWorkers; this is not CUDA OOM, and their PID/actor IDs differ from the failed update RPC actor. Next original-weight qualification pending push: existing SGLang FP32 head + Megatron fused head precision hypothesis, and normal1000000Mi memory per replica; same2×8H800/48CPU/input/R3/CP1/standard. Four native composed2/20config casesPASS. Actual CUDA, capacity, all MAE, two updates, versions and HF2 values remain to be verified.

- [ ] 使用冻结的真实数据与交互边界，teacher 实际评分的 token IDs 与当前 student 采样一致。
- [ ] thinking、正文和工具信号的源字段、tokens、mask、实际生成覆盖分别可核验；MoE routes 按约定真实录制并 replay。
- [ ] 两次实际更新具有有限 loss/梯度和有效权重变化；初始及更新后 rollout 对应正确 student 权重，最终更新也发布并验证。
- [ ] 在相同 tokens、权重、概率定义上比较 decode、独立 prefill 和 trainer，按冻结预算逐项 PASS；缺失或超限不得以 TIS 掩盖。
- [ ] 记录真实硬件、代码/环境身份、job/replica 和业务/终态证据；消费不再依赖的临时产物。
