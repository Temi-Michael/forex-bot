import unittest
from strategy import extract_last_digit, evaluate_ldp_strategy

class TestStrategy(unittest.TestCase):
    def test_extract_last_digit(self):
        self.assertEqual(extract_last_digit(123.456), 6)
        self.assertEqual(extract_last_digit(123.4560), 6)  # Trailing zeros stripped by logic
        self.assertEqual(extract_last_digit(123.4), 4)
        self.assertEqual(extract_last_digit(123.0), 3)     # Strips trailing .0 to 123 => last digit 3
        # However, Deriv ticks are usually strings or floats, if we do have something like 1000.00
        # `f"{1000.00:.4f}".rstrip('0').rstrip('.')` -> "1000" => 0.
        self.assertEqual(extract_last_digit(1000.00), 0)

    def test_evaluate_ldp_strategy_over(self):
        # Median > 4.5
        # Digits: [6, 7, 8, 9, 5] -> Sorted: [5, 6, 7, 8, 9] -> Median: 7
        prices = [10.1236, 10.1237, 10.1238, 10.1239, 10.1235]
        ctype, barrier = evaluate_ldp_strategy(prices)
        self.assertEqual(ctype, "DIGITOVER")
        self.assertEqual(barrier, "2")

    def test_evaluate_ldp_strategy_under(self):
        # Median < 4.5
        # Digits: [1, 2, 3, 4, 0] -> Sorted: [0, 1, 2, 3, 4] -> Median: 2
        prices = [10.1231, 10.1232, 10.1233, 10.1234, 10.1230]
        ctype, barrier = evaluate_ldp_strategy(prices)
        self.assertEqual(ctype, "DIGITUNDER")
        self.assertEqual(barrier, "7")

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
