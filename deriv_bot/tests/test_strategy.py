import unittest
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
        """
        Verifies that evaluate_ldp_strategy in "auto_median" mode classifies a clear high-digit median as DIGITOVER with barrier "3".
        
        Uses five prices whose extracted last digits produce a median greater than 4.5 (digits: [6, 7, 8, 9, 5] → median 7) and asserts the returned ctype is "DIGITOVER" and barrier is "3".
        """
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

if __name__ == "__main__":
    unittest.main()
