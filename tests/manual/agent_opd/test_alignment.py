"""CPU fault cases for the numerical qualification boundary."""

import json
import unittest

from tests.manual.agent_opd.alignment import aggregate_input_metrics, compare_logprobs


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

    def test_identical_values_do_not_pass_without_explicit_limits(self):
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

    def test_explicit_zero_budget_checks_only_mean_absolute_error(self):
        limits = {"mean_abs_diff": 0.0}
        self.assertEqual(self.compare(numerical_limits=limits)["status"], "pass")
        result = self.compare(candidate_logprobs=[-1.0, -2.5], numerical_limits=limits)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["failed_metrics"], ["mean_abs_diff"])

    def test_tail_and_k3_diagnostics_do_not_add_acceptance_thresholds(self):
        result = self.compare(
            reference_logprobs=[-10.0] * 1000,
            candidate_logprobs=[-10.0] * 999 + [0.0],
            reference_token_ids=list(range(1000)), candidate_token_ids=list(range(1000)),
            numerical_limits={"mean_abs_diff": 0.03},
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["mean_abs_diff"], 0.01)
        self.assertEqual(result["max_abs_diff"], 10)
        self.assertGreater(result["k3_diagnostics"]["r_log_r_minus_r_plus_one_mean"], 1)
        self.assertIsNone(result["k3_diagnostics"]["acceptance_cutoff"])

    def test_invalid_or_extra_acceptance_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            self.compare(numerical_limits={"mean_abs_diff": 0.03, "max_abs_diff": 0.03})
        with self.assertRaises(ValueError):
            self.compare(numerical_limits={"mean_abs_diff": float("nan")})
        with self.assertRaises(ValueError):
            self.compare(numerical_limits={"mean_abs_diff": -1})

    def test_k3_overflow_is_diagnostic_and_json_safe(self):
        result = self.compare(reference_logprobs=[-1001, -2], candidate_logprobs=[-1, -2])
        self.assertEqual(result["status"], "measured")
        self.assertEqual(result["k3_diagnostics"]["status"], "overflow")
        self.assertIsNone(result["k3_diagnostics"]["r_log_r_minus_r_plus_one_mean"])
        json.dumps(result, allow_nan=False)

    def input_metrics(self, error, count):
        return self.compare(
            reference_logprobs=[0] * count, candidate_logprobs=[-error] * count,
            reference_token_ids=list(range(count)), candidate_token_ids=list(range(count)),
            numerical_limits={"mean_abs_diff": 0.03},
        )

    def aggregate(self, inputs, **overrides):
        arguments = dict(expected_input_count=len(inputs), numerical_limits={"mean_abs_diff": 0.03},
                         whole_input_packs=True)
        arguments.update(overrides)
        return aggregate_input_metrics(inputs, **arguments)

    def test_global_mean_cannot_hide_a_failing_short_input(self):
        result = self.aggregate([self.input_metrics(0.04, 1), self.input_metrics(0, 99)])
        self.assertLess(result["global_token_mean_abs_diff"], 0.03)
        self.assertEqual(result["native_pack_mean_abs_diff_upper_bound"], 0.04)
        self.assertEqual(result["failed_input_count"], 1)
        self.assertEqual(result["status"], "fail")

    def test_complete_inputs_prove_the_pack_bound_without_inventing_boundaries(self):
        result = self.aggregate([self.input_metrics(0.03, 1), self.input_metrics(0.01, 9)])
        self.assertAlmostEqual(result["abs_diff_sum"], 0.12)
        self.assertEqual(result["token_count"], 10)
        self.assertAlmostEqual(result["global_token_mean_abs_diff"], 0.012)
        self.assertEqual(result["native_pack_acceptance"], "proven_bounded")
        self.assertFalse(result["native_pack_boundary_observed"])
        self.assertIsNone(result["native_pack_mean_abs_diff"])
        self.assertEqual(result["status"], "pass")

    def test_missing_input_or_unproven_pack_layout_cannot_pass(self):
        inputs = [self.input_metrics(0.01, 2)]
        self.assertEqual(self.aggregate(inputs, expected_input_count=2)["status"], "unverified")
        self.assertEqual(self.aggregate(inputs, whole_input_packs=False)["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
