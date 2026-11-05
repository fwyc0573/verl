"""CPU fault cases for the numerical qualification boundary."""

import unittest

from tests.manual.agent_opd.alignment import LIMIT_METRICS, compare_logprobs


class LogprobAlignmentTest(unittest.TestCase):
    def compare(self, **overrides):
        arguments = {
            "reference_logprobs": [-1.0, -2.0],
            "candidate_logprobs": [-1.0, -2.0],
            "reference_token_ids": [10, 20],
            "candidate_token_ids": [10, 20],
            "reference_weight_version": 3,
            "candidate_weight_version": 3,
            "ratio_bounds": [0.5, 2.0],
        }
        arguments.update(overrides)
        return compare_logprobs(**arguments)

    def test_identical_values_do_not_pass_without_calibrated_limits(self):
        result = self.compare()
        self.assertEqual(result["status"], "measured")
        self.assertEqual(result["mismatch_count"], 0)

    def test_identity_and_nonfinite_faults_are_rejected(self):
        cases = (
            {"candidate_token_ids": [10, 21]},
            {"candidate_weight_version": 4},
            {"candidate_weight_version": None},
            {"candidate_logprobs": [-1.0, float("nan")]},
            {"reference_logprobs": [float("inf"), -2.0]},
            {"candidate_logprobs": [-1.0]},
        )
        for fault in cases:
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.compare(**fault)

    def test_signed_cancellation_does_not_hide_absolute_error(self):
        result = self.compare(candidate_logprobs=[-0.5, -2.5])
        self.assertEqual(result["signed_mean_diff"], 0)
        self.assertEqual(result["mean_abs_diff"], 0.5)
        self.assertEqual(result["max_abs_diff"], 0.5)

    def test_extreme_finite_ratios_do_not_overflow(self):
        result = self.compare(candidate_logprobs=[-1001.0, -2.0])
        self.assertEqual(result["ratio_outside_count"], 1)
        self.assertEqual(result["ratio_fraction_outside"], 0.5)

    def test_explicit_zero_budget_checks_every_metric(self):
        limits = dict.fromkeys(LIMIT_METRICS, 0.0)
        self.assertEqual(self.compare(numerical_limits=limits)["status"], "pass")
        result = self.compare(candidate_logprobs=[-1.0, -2.5], numerical_limits=limits)
        self.assertEqual(result["status"], "fail")
        self.assertIn("max_abs_diff", result["failed_metrics"])

    def test_partial_or_invalid_acceptance_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            self.compare(numerical_limits={"mean_abs_diff": 0.1})
        with self.assertRaises(ValueError):
            self.compare(numerical_limits=dict.fromkeys(LIMIT_METRICS, float("nan")))


if __name__ == "__main__":
    unittest.main()
