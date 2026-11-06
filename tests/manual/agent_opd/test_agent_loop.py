"""CPU regression for native dispatch after single-turn OPD generation.

Generation and teacher responses are fixtures. These tests verify dispatch and
token preservation, not GPU generation, numerical agreement or model updates.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np

from tests.manual.agent_opd.agent_loop import PreparedTurnAgentLoop
from verl.experimental.agent_loop.agent_loop import AgentLoopWorker
from verl.utils.reward_score import default_compute_score


class TaskRewardDispatchTest(unittest.IsolatedAsyncioTestCase):
    async def test_no_task_reward_preserves_native_teacher_dispatch(self):
        for pair in ("glm", "qwen"):
            with self.subTest(pair=pair):
                with self.assertRaisesRegex(NotImplementedError, "Reward function is not implemented"):
                    default_compute_score(data_source=np.str_(pair), solution_str="", ground_truth="")

                response_ids, logprobs = [31, 32], [-0.4, -0.5]
                routes = np.array([[[1]], [[2]], [[3]]], dtype=np.int16)
                generation = SimpleNamespace(
                    token_ids=response_ids, log_probs=logprobs, routed_experts=routes,
                    num_preempted=0, stop_reason="length",
                    extra_fields={"global_steps": 0, "min_global_steps": 0, "max_global_steps": 0},
                )
                loop = SimpleNamespace(
                    prompt_length=8, response_length=4,
                    rollout_config=SimpleNamespace(full_determinism=False),
                    server_manager=SimpleNamespace(generate=AsyncMock(return_value=generation)),
                    _describe_completion=AsyncMock(return_value={"content": "fixture"}),
                    _rescore_student=AsyncMock(return_value={"status": "fixture_only"}),
                )
                output = await PreparedTurnAgentLoop.run(
                    loop, {"temperature": 1.0}, prepared_prompt_ids=[11, 12], tools=[],
                    thinking_enabled=False, raw_prompt=[{"role": "user", "content": "fixture"}],
                    source={"prompt_sha256": "fixture", "uid": "fixture", "category": "neither"},
                )
                self.assertEqual(output.prompt_ids, [11, 12])
                self.assertEqual(output.response_ids, response_ids)
                self.assertEqual(output.response_logprobs, logprobs)
                self.assertEqual(output.response_mask, [1, 1])
                np.testing.assert_array_equal(output.routed_experts, routes)
                self.assertEqual(output.reward_score, 0.0)

                def forbidden_score_inputs(*args, **kwargs):
                    self.fail("A no-task-reward output entered native task reward computation")

                teacher = SimpleNamespace(
                    compute_teacher_logprobs_single=AsyncMock(return_value=([31, 32], [-0.3, -0.2]))
                )
                worker = SimpleNamespace(
                    reward_loop_worker_handles=[object()], _compute_multi_modal_inputs=forbidden_score_inputs,
                    distillation_enabled=True, teacher_key="teacher", teacher_server_manager=teacher,
                )
                await AgentLoopWorker._compute_score(worker, [output], kwargs={})
                await AgentLoopWorker._compute_teacher_logprobs(
                    worker, output, output.prompt_ids, output.response_ids, validate=False,
                    sample_kwargs={"teacher": np.str_("teacher_model")},
                )
                teacher.compute_teacher_logprobs_single.assert_awaited_once()
                call = teacher.compute_teacher_logprobs_single.await_args.kwargs
                self.assertEqual(call["sequence_ids"], [11, 12, 31, 32])
                self.assertEqual(call["routing_key"], "teacher_model")
                self.assertEqual(output.extra_fields["teacher_ids"], [31, 32])
                self.assertEqual(output.extra_fields["teacher_logprobs"], [-0.3, -0.2])


if __name__ == "__main__":
    unittest.main()
