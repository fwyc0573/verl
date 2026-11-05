"""Native single-turn OPD generation with observations on the original tokens.

Prepared source prompts are already rendered for the student tokenizer. Calling
the generic chat-template builder here would change their assistant boundary.
The native AgentLoopWorker still pads the result and computes teacher signals.
"""

import copy
import logging
from typing import Any
from uuid import uuid4

from sglang.srt.parser.reasoning_parser import ReasoningParser

from tests.manual.agent_opd.alignment import compare_logprobs
from verl.experimental.agent_loop.agent_loop import AgentLoopOutput
from verl.experimental.agent_loop.single_turn_agent_loop import SingleTurnAgentLoop
from verl.experimental.agent_loop.tool_parser import ToolParser
from verl.tools.schemas import OpenAIFunctionToolSchema
from verl.utils.profiler import simple_timer
from verl.utils.rollout_trace import rollout_trace_op

logger = logging.getLogger(__name__)

COMPLETION_CATEGORIES = {
    (False, False): "neither",
    (False, True): "control_only",
    (True, False): "thinking_only",
    (True, True): "control_and_thinking",
}


def _weight_version(extra_fields: dict) -> int | str:
    version = extra_fields.get("global_steps")
    minimum = extra_fields.get("min_global_steps")
    maximum = extra_fields.get("max_global_steps")
    if version is None or minimum is None or maximum is None:
        raise ValueError("Native global_steps/min_global_steps/max_global_steps metadata is missing")
    if minimum != version or maximum != version:
        raise ValueError("Generation or scoring spans more than one native weight version")
    return version


class PreparedTurnAgentLoop(SingleTurnAgentLoop):
    """Generate one assistant turn and observe same-student independent prefill."""

    def __init__(self, *args, reasoning_parser, tool_parser, ratio_bounds, numerical_limits=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reasoning_parser_name = reasoning_parser
        self.tool_parser = ToolParser.get_tool_parser(tool_parser, self.tokenizer)
        self.ratio_bounds = list(ratio_bounds)
        self.numerical_limits = dict(numerical_limits) if numerical_limits is not None else None

    async def _describe_completion(self, response_ids, tools, thinking_enabled):
        raw_text = self.tokenizer.decode(response_ids, skip_special_tokens=False)
        parser_text = self.tokenizer.decode(response_ids, skip_special_tokens=True)
        reasoning, body = ReasoningParser(
            model_type=self.reasoning_parser_name,
            force_reasoning=thinking_enabled if thinking_enabled is not None else "</think>" in parser_text,
        ).parse_non_stream(parser_text)
        calls = []
        parse_error = None
        try:
            tool_schemas = [OpenAIFunctionToolSchema.model_validate(tool) for tool in tools]
            content, parsed = await self.tool_parser.extract_tool_calls(response_ids, tools=tool_schemas)
            if parsed:
                _, body = ReasoningParser(
                    model_type=self.reasoning_parser_name, force_reasoning="</think>" in content
                ).parse_non_stream(content)
            calls = [
                {
                    "id": call.tool_call_id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments},
                }
                for call in parsed
            ]
        except Exception as error:
            # Token-limited XML or argument parsing never changes the sampled turn.
            parse_error = f"{type(error).__name__}: {error}"
        names = [call["function"]["name"] for call in calls]
        has_thinking, has_submit = bool(reasoning), "submit" in names
        return {
            "raw_text": raw_text,
            "reasoning_content": reasoning or "",
            "content": body or "",
            "tool_calls": calls,
            "tool_names": names,
            "tool_call_envelopes_complete": raw_text.count("<tool_call>") == raw_text.count("</tool_call>"),
            "has_thinking": has_thinking,
            "has_body": bool(body),
            "has_submit": has_submit,
            "category": COMPLETION_CATEGORIES[has_thinking, has_submit],
            "tool_parse_error": parse_error,
            "reasoning_parser": self.reasoning_parser_name,
            "tool_parser": type(self.tool_parser).__name__,
        }

    async def _rescore_student(self, prompt_ids, response_ids, decode_logprobs, generation_fields):
        observation = {
            "status": "unverified",
            "training_logprobs_replaced": False,
            "response_token_ids": response_ids,
            "decode_logprobs": decode_logprobs,
            "decode_weight_metadata": {
                key: generation_fields.get(key) for key in ("global_steps", "min_global_steps", "max_global_steps")
            },
            "independent_prefill": False,
        }
        try:
            engine_kwargs = self.rollout_config.engine_kwargs.get("sglang", {})
            if self.rollout_config.name != "sglang" or engine_kwargs.get("disable_radix_cache") is not True:
                raise ValueError("Independent prefill requires SGLang engine_kwargs.sglang.disable_radix_cache=True")
            scored = await self.server_manager.generate(
                request_id=uuid4().hex,
                prompt_ids=prompt_ids + response_ids,
                sampling_params={"max_tokens": 1, "temperature": 1.0, "prompt_logprobs": 0, "detokenize": False},
            )
            observation["independent_prefill"] = True
            fields = scored.extra_fields
            observation["prefill_weight_metadata"] = {
                key: fields.get(key) for key in ("global_steps", "min_global_steps", "max_global_steps")
            }
            start, end = len(prompt_ids) - 1, len(prompt_ids) + len(response_ids) - 1
            if len(fields["prompt_ids"]) != len(prompt_ids) + len(response_ids):
                raise ValueError("Prefill token rows do not cover the complete prompt and response")
            if len(fields["prompt_logprobs"]) != len(prompt_ids) + len(response_ids):
                raise ValueError("Prefill logprob rows do not cover the complete prompt and response")
            scored_ids = [row[0] for row in fields["prompt_ids"][start:end]]
            scores = [row[0] for row in fields["prompt_logprobs"][start:end]]
            observation["prefill_token_ids"] = scored_ids
            observation["prefill_logprobs"] = scores
            observation["decode_prefill"] = compare_logprobs(
                decode_logprobs,
                scores,
                reference_token_ids=response_ids,
                candidate_token_ids=scored_ids,
                reference_weight_version=_weight_version(generation_fields),
                candidate_weight_version=_weight_version(fields),
                ratio_bounds=self.ratio_bounds,
                numerical_limits=self.numerical_limits,
            )
            observation["status"] = observation["decode_prefill"]["status"]
        except Exception as error:
            observation.update(error_type=type(error).__name__, reason=str(error))
            logger.warning("AGENT_OPD_ALIGNMENT_UNVERIFIED %s: %s", type(error).__name__, error)
        return observation

    @rollout_trace_op
    async def run(self, sampling_params: dict[str, Any], priority: int = 0, **kwargs) -> AgentLoopOutput:
        prompt_ids = [int(token_id) for token_id in kwargs["prepared_prompt_ids"]]
        if not prompt_ids or len(prompt_ids) > self.prompt_length:
            raise ValueError("Prepared prompt must be nonempty and fit rollout.prompt_length without truncation")
        metrics = {}
        with simple_timer("generate_sequences", metrics):
            request_id = (
                f"det-{int(priority)}"
                if getattr(self.rollout_config, "full_determinism", False)
                else uuid4().hex
            )
            output = await self.server_manager.generate(
                request_id=request_id,
                prompt_ids=prompt_ids,
                sampling_params=dict(sampling_params),
                priority=int(priority),
            )
        response_ids = output.token_ids
        if len(response_ids) > self.response_length:
            raise ValueError("Native generation exceeded rollout.response_length")
        response_logprobs = output.log_probs
        if response_logprobs is not None and len(response_logprobs) != len(response_ids):
            raise ValueError("Native response logprobs do not align with the generated token IDs")
        metrics["num_preempted"] = output.num_preempted if output.num_preempted is not None else -1
        extra_fields = dict(output.extra_fields)
        try:
            completion = await self._describe_completion(response_ids, kwargs["tools"], kwargs["thinking_enabled"])
            completion["status"] = "observed"
        except Exception as error:
            # Completion parsing is auxiliary; native tokens and teacher scoring continue.
            completion = {
                "status": "unverified",
                "error_type": type(error).__name__,
                "reason": str(error),
                "category": None,
            }
            try:
                completion["raw_text"] = self.tokenizer.decode(response_ids, skip_special_tokens=False)
            except Exception as decode_error:
                completion["decode_error_type"] = type(decode_error).__name__
            logger.warning("AGENT_OPD_COMPLETION_UNVERIFIED %s: %s", type(error).__name__, error)
        completion["stop_reason"] = output.stop_reason
        extra_fields["completion"] = completion
        extra_fields["messages"] = [
            *copy.deepcopy(list(kwargs["raw_prompt"])),
            {
                "role": "assistant",
                "content": completion.get("content"),
                "reasoning_content": completion.get("reasoning_content"),
                "tool_calls": completion.get("tool_calls"),
                "raw_text": completion.get("raw_text"),
            },
        ]
        extra_fields["student_rescoring"] = await self._rescore_student(
            prompt_ids, response_ids, response_logprobs, extra_fields
        )
        source = kwargs["source"]
        extra_fields["student_rescoring"]["prompt_receipt"] = {
            "token_sha256": source["prompt_sha256"],
            "token_count": len(prompt_ids),
            "source_uid": source["uid"],
            "source_category": source["category"],
        }
        extra_fields.update(turn_scores=[], tool_rewards=[])
        return AgentLoopOutput(
            prompt_ids=prompt_ids,
            response_ids=response_ids,
            response_mask=[1] * len(response_ids),
            response_logprobs=response_logprobs,
            routed_experts=output.routed_experts,
            multi_modal_data={},
            num_turns=2,
            metrics=metrics,
            extra_fields=extra_fields,
        )
