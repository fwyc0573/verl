"""Compare probabilities for identical student tokens and weight versions.

No numerical acceptance budget is supplied by this module. A measured comparison
becomes a pass or fail only when the caller supplies every required limit from
the qualification's recorded calibration.
"""

import math
from collections.abc import Mapping, Sequence


LIMIT_METRICS = (
    "mean_abs_diff",
    "p95_abs_diff",
    "p99_abs_diff",
    "max_abs_diff",
    "abs_signed_mean_diff",
    "ratio_fraction_outside",
)


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
    signed_mean = math.fsum(differences) / len(differences)
    lower_log, upper_log = math.log(ratio_lower), math.log(ratio_upper)
    outside = sum(value < lower_log or value > upper_log for value in differences)
    result = {
        "status": "measured",
        "token_count": len(reference),
        "token_ids_match": True,
        "versions_match": True,
        "weight_version": reference_weight_version,
        "mean_abs_diff": math.fsum(absolute) / len(absolute),
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
    }
    if numerical_limits is not None:
        if set(numerical_limits) != set(LIMIT_METRICS):
            raise ValueError(f"numerical_limits must define exactly {', '.join(LIMIT_METRICS)}")
        limits = {name: float(value) for name, value in numerical_limits.items()}
        if any(not math.isfinite(value) or value < 0 for value in limits.values()):
            raise ValueError("Numerical limits must be finite and nonnegative")
        if limits["ratio_fraction_outside"] > 1:
            raise ValueError("The ratio fraction limit cannot exceed one")
        result["numerical_limits"] = limits
        result["failed_metrics"] = [name for name, limit in limits.items() if result[name] > limit]
        result["status"] = "fail" if result["failed_metrics"] else "pass"
    return result
