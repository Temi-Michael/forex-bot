import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from strategy import extract_last_digit, evaluate_ldp_strategy

class TestStrategy(unittest.TestCase):
    def test_extract_last_digit(self):
        # Default pip_size = 4
        self.assertEqual(extract_last_digit(123.4567, 4), 7)
        self.assertEqual(extract_last_digit(123.456, 4), 0)  # 123.4560 -> 0
        self.assertEqual(extract_last_digit(123.4, 4), 0)    # 123.4000 -> 0
        self.assertEqual(extract_last_digit(1000.00, 4), 0)  # 1000.0000 -> 0

        # Explicit pip_size = 2
        self.assertEqual(extract_last_digit(123.45, 2), 5)
        self.assertEqual(extract_last_digit(123.4, 2), 0)    # 123.40 -> 0

    def test_evaluate_ldp_strategy_over(self):
        # Auto Median Mode: Low median (< 4.5) triggers UNDER 6
        # wait, the logic currently says:
        # if median_val > 4.5: return "DIGITOVER", "3"
        # if median_val < 4.5: return "DIGITUNDER", "6"

        # Median > 4.5
        # Digits: [6, 7, 8, 9, 5] -> Sorted: [5, 6, 7, 8, 9] -> Median: 7
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_evaluate_ldp_strategy_under(self):
        # Median < 4.5
        # Digits: [1, 2, 3, 4, 0] -> Sorted: [0, 1, 2, 3, 4] -> Median: 2
        prices = [10.1231, 10.1232, 10.1233, 10.1234, 10.1230]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertEqual(barrier, "6")

    def test_strict_over_mode(self):
        # Strict OVER 3 mode triggers on streaks of low digits (<= 3)
        # Digits: [1, 2, 1, 2, 3] -> 4 out of last 4 are low
        prices = [10.1231, 10.1232, 10.1231, 10.1232, 10.1233]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_strict_under_mode(self):
        # Strict UNDER 6 mode triggers on streaks of high digits (>= 6)
        # Digits: [7, 8, 7, 8, 6] -> 4 out of last 4 are high
        prices = [10.1237, 10.1238, 10.1237, 10.1238, 10.1236]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertEqual(barrier, "6")

    def test_evaluate_ldp_strategy_exact_median(self):
        # Digits: [4, 5] -> Median: 4.5
        prices = [10.1234, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices)
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_evaluate_empty_list(self):
        ctype, barrier = evaluate_ldp_strategy([])
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    # --- New tests for PR changes ---

    def test_evaluate_fewer_than_5_prices_returns_none(self):
        # PR introduced len(prices) < 5 guard; 4 prices must return (None, None)
        prices = [10.1231, 10.1232, 10.1233, 10.1234]
        ctype, barrier = evaluate_ldp_strategy(prices)
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_evaluate_single_price_returns_none(self):
        ctype, barrier = evaluate_ldp_strategy([10.1235])
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_auto_median_is_default_mode(self):
        # Calling without mode arg defaults to 'auto_median' behavior
        # Digits: [6, 7, 8, 9, 5] -> Median: 7 -> DIGITOVER 3
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices)
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_auto_median_exactly_45_no_signal(self):
        # Median == 4.5 should return no signal in auto_median mode
        # Digits: [4, 5, 4, 5, 4] -> Sorted: [4, 4, 4, 5, 5] -> Median: 4
        # Need even count for 4.5: Digits [4, 5] with len 2 but need >= 5
        # Digits: [4, 5, 4, 5, 4, 5] -> Median: 4.5
        prices = [10.1234, 10.1235, 10.1234, 10.1235, 10.1234, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_auto_median_large_price_list(self):
        # Verify strategy works correctly on a large price list (e.g., 500 ticks)
        # All digits high (9): median = 9 > 4.5 -> DIGITOVER 3
        prices = [10.1239] * 500
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_strict_over_boundary_exactly_3_of_4_low_triggers(self):
        # Exactly 3 out of last 4 digits are <= 3 -> should trigger DIGITOVER 3
        # Last 4 digits: [3, 1, 2, 5] -> 3 low (3, 1, 2) and 1 high (5) -> triggers
        prices = [10.1235, 10.1233, 10.1231, 10.1232, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_strict_over_only_2_of_4_low_no_trigger(self):
        # Only 2 out of last 4 digits are <= 3 -> should NOT trigger
        # Digits: [5, 1, 2, 5, 5] -> last 4: [1, 2, 5, 5] -> 2 low
        prices = [10.1235, 10.1231, 10.1232, 10.1235, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_strict_over_uses_only_last_4_ticks(self):
        # Early digits are all low but last 4 are high -> should NOT trigger
        # First 5 prices: digits [1, 1, 1, 7, 8, 9, 6] -> last 4: [7, 8, 9, 6] -> 0 low
        prices = [10.1231, 10.1231, 10.1231, 10.1237, 10.1238, 10.1239, 10.1236]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_strict_over_digit_boundary_value_3_counts_as_low(self):
        # Digit exactly equal to 3 must be counted as low (<= 3)
        # Last 4 digits: [3, 3, 3, 7] -> 3 low (all 3s) -> triggers
        prices = [10.1235, 10.1233, 10.1233, 10.1233, 10.1237]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "3")

    def test_strict_over_digit_boundary_value_4_does_not_count_as_low(self):
        # Digit 4 is NOT <= 3, so should not count toward low streak
        # Last 4 digits: [4, 1, 2, 4] -> only 2 low (1, 2) -> no trigger
        prices = [10.1235, 10.1234, 10.1231, 10.1232, 10.1234]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_over")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_strict_under_boundary_exactly_3_of_4_high_triggers(self):
        # Exactly 3 out of last 4 digits are >= 6 -> should trigger DIGITUNDER 6
        # Last 4 digits: [7, 8, 6, 2] -> 3 high (7, 8, 6) -> triggers
        prices = [10.1235, 10.1237, 10.1238, 10.1236, 10.1232]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertEqual(barrier, "6")

    def test_strict_under_only_2_of_4_high_no_trigger(self):
        # Only 2 out of last 4 digits are >= 6 -> should NOT trigger
        # Last 4 digits: [7, 8, 3, 2] -> only 2 high -> no trigger
        prices = [10.1235, 10.1237, 10.1238, 10.1233, 10.1232]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_strict_under_uses_only_last_4_ticks(self):
        # Early digits are all high but last 4 are low -> should NOT trigger
        # Digits: [9, 9, 9, 1, 2, 3, 4] -> last 4: [1, 2, 3, 4] -> 0 high
        prices = [10.1239, 10.1239, 10.1239, 10.1231, 10.1232, 10.1233, 10.1234]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_strict_under_digit_boundary_value_6_counts_as_high(self):
        # Digit exactly equal to 6 must be counted as high (>= 6)
        # Last 4 digits: [6, 6, 6, 1] -> 3 high (all 6s) -> triggers
        prices = [10.1235, 10.1236, 10.1236, 10.1236, 10.1231]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertEqual(barrier, "6")

    def test_strict_under_digit_boundary_value_5_does_not_count_as_high(self):
        # Digit 5 is NOT >= 6, so should not count toward high streak
        # Last 4 digits: [5, 7, 8, 5] -> only 2 high (7, 8) -> no trigger
        prices = [10.1235, 10.1235, 10.1237, 10.1238, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="strict_under")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_unknown_mode_returns_none(self):
        # An unrecognized mode should fall through to return (None, None)
        prices = [10.1231, 10.1232, 10.1233, 10.1234, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="nonexistent_mode")
        self.assertIsNone(ctype)
        self.assertIsNone(barrier)

    def test_return_type_is_tuple(self):
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        result = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_barrier_is_string_not_int(self):
        # Barriers must be strings ("3" and "6"), not integers
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        _, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertIsInstance(barrier, str)

    def test_auto_median_over_barrier_is_3_not_2(self):
        # PR changed barrier from "2" to "3" for DIGITOVER
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertEqual(ctype, "DIGITOVER")
        self.assertNotEqual(barrier, "2")
        self.assertEqual(barrier, "3")

    def test_auto_median_under_barrier_is_6_not_7(self):
        # PR changed barrier from "7" to "6" for DIGITUNDER
        prices = [10.1231, 10.1232, 10.1233, 10.1234, 10.1230]
        ctype, barrier = evaluate_ldp_strategy(prices, mode="auto_median")
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertNotEqual(barrier, "7")
        self.assertEqual(barrier, "6")


if __name__ == "__main__":
    unittest.main()
