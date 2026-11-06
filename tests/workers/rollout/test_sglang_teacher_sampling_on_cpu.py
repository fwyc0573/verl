# Copyright 2026 Individual Contributor.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Exercise native teacher request translation with fixture SGLang responses."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sglang.srt.sampling.sampling_params import SamplingParams

from verl.experimental.teacher_loop.teacher_manager import _get_teacher_sampling_params
from verl.workers.rollout.sglang_rollout import async_sglang_server


class TeacherSamplingTest(unittest.IsolatedAsyncioTestCase):
    async def test_teacher_output_option_does_not_enter_sglang_sampling(self):
        for topk in (0, 2):
            with self.subTest(topk=topk):
                requests = []

                async def generate_request(request, _):
                    SamplingParams(**request.sampling_params)
                    requests.append(request)
                    yield {
                        "output_ids": [99],
                        "meta_info": {
                            "finish_reason": {"type": "length"},
                            "output_token_logprobs": [[-0.1, 99, None]],
                            "input_token_logprobs": [[None, 11, None], [-0.2, 12, None], [-0.3, 31, None]],
                            "input_top_logprobs": [
                                [], [[-0.2, 12, None], [-0.4, 21, None]],
                                [[-0.3, 31, None], [-0.5, 22, None]],
                            ],
                        },
                    }

                server = object.__new__(async_sglang_server.SGLangHttpServer)
                server._disaggregation_role = None
                server._pd_decode_peers = []
                server.config = SimpleNamespace(
                    max_model_len=16, prompt_length=12, response_length=4,
                    enable_rollout_routing_replay=False, mtp=None,
                )
                server.model_config = SimpleNamespace(lora_rank=0, lora={})
                server.global_steps = 0
                server.tokenizer_manager = SimpleNamespace(generate_request=generate_request)
                params = _get_teacher_sampling_params(
                    SimpleNamespace(inference=SimpleNamespace(temperature=1.0)),
                    SimpleNamespace(topk=topk, loss_settings=SimpleNamespace(use_topk=topk > 0)),
                )
                self.assertIs(params["detokenize"], False)
                with self.assertRaisesRegex(TypeError, "detokenize"):
                    SamplingParams(max_new_tokens=1, temperature=1.0, detokenize=False)
                context = SimpleNamespace(get_actor_name=lambda: "fixture")
                with patch.object(async_sglang_server.ray, "get_runtime_context", return_value=context):
                    output = await server.generate([11, 12, 31], params, "fixture")

                self.assertEqual(len(requests), 1)
                request = requests[0]
                self.assertNotIn("detokenize", request.sampling_params)
                self.assertEqual(request.sampling_params, {"max_new_tokens": 1, "temperature": 1.0})
                self.assertEqual(request.input_ids, [11, 12, 31])
                self.assertTrue(request.return_logprob)
                self.assertEqual(request.logprob_start_len, 0)
                self.assertEqual(request.top_logprobs_num, topk if topk > 0 else None)
                self.assertEqual(output.token_ids, [99])
                self.assertEqual(output.log_probs, [-0.1])
                self.assertEqual(output.extra_fields["prompt_ids"][0], [12] if topk == 0 else [12, 21])
                self.assertEqual(len(output.extra_fields["prompt_logprobs"]), 3)


if __name__ == "__main__":
    unittest.main()
