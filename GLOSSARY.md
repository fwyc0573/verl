# Agent On-Policy Distillation

Terms used to distinguish training, inference agreement, and agent evaluation.

## Language

**Teacher–student pair**:
A fixed teacher that supplies probability targets and a student whose parameters are optimized. An arrow between their names denotes teacher to student.

**On-policy completion**:
A new completion sampled from the current student policy for the current training input. A saved completion from another policy is historical source material, not an on-policy sample.

**Source turn**:
An assistant turn and its preceding conversation from the original dataset. Its provenance and signal category remain distinct from those of a newly sampled student completion.

**Training–inference agreement**:
Agreement within a stated numerical budget between the same student's training and inference probability calculations on identical tokens and the same weights.
_Avoid_: Teacher–student equality.

**Rollout routing replay (R3)**:
Reuse during training of the mixture-of-experts routing decisions recorded during student generation.

**Truncated importance sampling (TIS)**:
A correction that limits the influence of differences between sampling and training probabilities. Its use alone does not establish training–inference agreement.

**Agent episode**:
A sequence of model turns and environment interactions for one task, ending in a terminal outcome or a stated limit.

**avg@4**:
The average of four valid graded attempts per question, averaged over the fixed question set. Missing infrastructure results are outside the valid denominator.
_Avoid_: pass@4.

**Successful optimizer update**:
A completed parameter update with valid numerical outputs. A loop iteration or checkpoint directory name alone does not establish an update.

**Task-owned disposable artifact**:
An output or cache created for this test whose downstream consumers have finished. Shared model assets and original datasets are not disposable artifacts of this task.
