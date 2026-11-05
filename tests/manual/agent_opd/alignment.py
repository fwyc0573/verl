"""Compare probabilities for identical student tokens and weight versions.

The adopted budget is supplied explicitly by the run settings. Only mean
absolute logprob error is gated. Tails, signed errors, ratios and both K3
expressions remain diagnostics. Every input must pass before aggregation.
"""

import math
from collections.abc import Mapping, Sequence


LIMIT_METRICS = ("mean_abs_diff",)


def validate_numerical_limits(numerical_limits):
    if numerical_limits is None:
        return None
    if set(numerical_limits) != set(LIMIT_METRICS):
        raise ValueError("numerical_limits must define only mean_abs_diff; other metrics are diagnostic")
    limits = {name: float(value) for name, value in numerical_limits.items()}
    if any(not math.isfinite(value) or value < 0 for value in limits.values()):
        raise ValueError("Numerical limits must be finite and nonnegative")
    return limits


def _k3_diagnostics(differences):
    """Report discrepancy expressions without treating them as a qualified KL."""
    forward, reverse = [], []
    overflow = 0
    for difference in differences:
        try:
            ratio = math.exp(difference)
            forward_value = math.fsum((ratio * difference, -math.expm1(difference)))
            reverse_value = math.expm1(difference) - difference
            if not all(math.isfinite(value) for value in (forward_value, reverse_value)):
                raise OverflowError
            forward.append(forward_value)
            reverse.append(reverse_value)
        except OverflowError:
            overflow += 1
    result = {
        "status": "reported" if not overflow else "overflow",
        "ratio_definition": "r=exp(candidate_logprob-reference_logprob)",
        "overflow_token_count": overflow,
        "r_log_r_minus_r_plus_one_mean": None,
        "r_minus_one_minus_log_r_mean": None,
        "acceptance_cutoff": None,
        "interpretation": "Discrepancy diagnostics; no KL qualification is inferred",
    }
    if not overflow:
        try:
            result["r_log_r_minus_r_plus_one_mean"] = math.fsum(forward) / len(differences)
            result["r_minus_one_minus_log_r_mean"] = math.fsum(reverse) / len(differences)
        except OverflowError:
            result["status"] = "overflow"
    return result


def aggregate_input_metrics(input_metrics, *, expected_input_count, numerical_limits, whole_input_packs):
    """Bound every native pack using complete, individually qualified inputs.

    For complete-input packs, A_pack/N_pack is a nonnegative token-weighted
    mean of input MAEs and cannot exceed max(input MAE). Any subsequent
    pack/time/DP arithmetic means preserve that bound. Physical backend pack
    boundaries are not observed and no measured pack mean is invented.
    """
    limits = validate_numerical_limits(numerical_limits)
    complete = len(input_metrics) == expected_input_count and expected_input_count > 0
    result = {
        "status": "unverified",
        "expected_input_count": expected_input_count,
        "observed_input_count": len(input_metrics),
        "completion_source": "current_student",
        "all_loss_eligible_tokens_before_tis": True,
        "native_pack_boundary_observed": False,
        "native_pack_mean_abs_diff": None,
        "native_pack_acceptance": "unverified",
        "whole_input_packs": whole_input_packs,
    }
    if not input_metrics:
        return result
    numerator = math.fsum(item["abs_diff_sum"] for item in input_metrics)
    denominator = sum(item["token_count"] for item in input_metrics)
    upper_bound = max(item["mean_abs_diff"] for item in input_metrics)
    result.update(
        abs_diff_sum=numerator, token_count=denominator,
        global_token_mean_abs_diff=numerator / denominator,
        per_input_mean_abs_diff=math.fsum(item["mean_abs_diff"] for item in input_metrics) / len(input_metrics),
        native_pack_mean_abs_diff_upper_bound=upper_bound,
        failed_input_count=sum(item["status"] == "fail" for item in input_metrics),
    )
    if not complete or not whole_input_packs:
        return result
    if limits is None:
        result["status"] = "measured"
        return result
    threshold = limits["mean_abs_diff"]
    passed = upper_bound <= threshold and result["global_token_mean_abs_diff"] <= threshold
    result["status"] = "pass" if passed else "fail"
    result["native_pack_acceptance"] = "proven_bounded" if upper_bound <= threshold else "unverified"
    result["numerical_limits"] = limits
    return result


def _quantile(sorted_values: list[float], fraction: float) -> float:
    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def compare_logprobs(
    reference_logprobs: Sequence[float],
    candidate_logprobs: Sequence[float],
    *,
    reference_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    reference_weight_version: int | str | None,
    candidate_weight_version: int | str | None,
    ratio_bounds: Sequence[float],
    numerical_limits: Mapping[str, float] | None = None,
) -> dict:
    """Measure candidate minus reference on the same nonempty response span.

    The ratio is ``exp(candidate_logprob - reference_logprob)``. Its coverage is
    evaluated in log space, so a large finite discrepancy cannot overflow the
    observation. Native version metadata must be present; absent versions are
    not inferred from the trainer step or replaced with a sentinel.
    """
    reference = [float(value) for value in reference_logprobs]
    candidate = [float(value) for value in candidate_logprobs]
    reference_ids = list(reference_token_ids)
    candidate_ids = list(candidate_token_ids)
    if not reference or not (len(reference) == len(candidate) == len(reference_ids) == len(candidate_ids)):
        raise ValueError("Logprob arrays and token IDs must cover the same nonempty response span")
    if reference_ids != candidate_ids:
        raise ValueError("The compared token IDs differ")
    if reference_weight_version is None or candidate_weight_version is None:
        raise ValueError("Native weight version metadata is missing")
    if reference_weight_version != candidate_weight_version:
        raise ValueError("The compared weight versions differ")
    if not all(math.isfinite(value) for value in reference + candidate):
        raise ValueError("The compared logprob arrays contain a non-finite value")
    if len(ratio_bounds) != 2:
        raise ValueError("ratio_bounds must contain a lower and an upper bound")
    ratio_lower, ratio_upper = map(float, ratio_bounds)
    if not (
        math.isfinite(ratio_lower)
        and math.isfinite(ratio_upper)
        and 0 < ratio_lower <= 1 <= ratio_upper
        and ratio_lower < ratio_upper
    ):
        raise ValueError("ratio_bounds must be finite, positive, ordered, and include one")

    differences = [candidate_value - reference_value for reference_value, candidate_value in zip(reference, candidate)]
    if not all(math.isfinite(value) for value in differences):
        raise ValueError("The logprob differences are non-finite")
    absolute = sorted(abs(value) for value in differences)
    absolute_sum = math.fsum(absolute)
    signed_mean = math.fsum(differences) / len(differences)
    lower_log, upper_log = math.log(ratio_lower), math.log(ratio_upper)
    outside = sum(value < lower_log or value > upper_log for value in differences)
    result = {
        "status": "measured",
        "token_count": len(reference),
        "token_ids_match": True,
        "versions_match": True,
        "weight_version": reference_weight_version,
        "abs_diff_sum": absolute_sum,
        "mean_abs_diff": absolute_sum / len(absolute),
        "p95_abs_diff": _quantile(absolute, 0.95),
        "p99_abs_diff": _quantile(absolute, 0.99),
        "max_abs_diff": absolute[-1],
        "signed_mean_diff": signed_mean,
        "abs_signed_mean_diff": abs(signed_mean),
        "log_ratio_min": min(differences),
        "log_ratio_max": max(differences),
        "log_ratio_p95": _quantile(sorted(differences), 0.95),
        "log_ratio_p99": _quantile(sorted(differences), 0.99),
        "ratio_bounds": [ratio_lower, ratio_upper],
        "ratio_outside_count": outside,
        "ratio_fraction_outside": outside / len(differences),
        "mismatch_count": sum(value != 0 for value in differences),
        "k3_diagnostics": _k3_diagnostics(differences),
    }
    limits = validate_numerical_limits(numerical_limits)
    if limits is not None:
        result["numerical_limits"] = limits
        result["failed_metrics"] = [name for name, limit in limits.items() if result[name] > limit]
        result["status"] = "fail" if result["failed_metrics"] else "pass"
    return result
