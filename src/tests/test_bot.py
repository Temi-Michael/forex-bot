import unittest
import pandas as pd
import numpy as np
from bot.strategy import Strategy
from bot.bot import TradingBot
import bot.config as config

class TestTradingBot(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy(config)
        self.bot = TradingBot(use_mock=True)
        # Initialize the mock bot so the mock environment is set up
        self.bot.mt5.initialize()

    def test_indicator_calculation(self):
        # Create dummy data
        data = {
            'time': pd.date_range(start='1/1/2023', periods=100, freq='min'),
            'open': np.random.uniform(1.0, 1.1, 100),
            'high': np.random.uniform(1.1, 1.2, 100),
            'low': np.random.uniform(0.9, 1.0, 100),
            'close': np.random.uniform(1.0, 1.1, 100)
        }
        df = pd.DataFrame(data)

        # Calculate indicators
        result_df = self.strategy.calculate_indicators(df)

        # Check if columns were added
        self.assertIn('ema_fast', result_df.columns)
        self.assertIn('ema_slow', result_df.columns)
        self.assertIn('stoch_k', result_df.columns)
        self.assertIn('atr', result_df.columns)

        # Check if rows were dropped due to NaN (e.g. from EMA 21 period)
        self.assertLess(len(result_df), 100)

    def test_signal_generation_buy(self):
        # Force a BUY signal condition
        # 1. Fast EMA > Slow EMA
        # 2. Stoch K crossed above Stoch D, and K < 20

        data = {
            'ema_fast': [1.05, 1.05, 1.05, 1.05],
            'ema_slow': [1.00, 1.00, 1.00, 1.00],
            'stoch_k': [10, 15, 19, 20],  # -3 was 15, -2 now 19 (Oversold), -1 is forming
            'stoch_d': [19, 18, 17, 18]   # -3 K below D, -2 K above D (Cross up)
        }
        df = pd.DataFrame(data)

        signal = self.strategy.get_signal(df)
        self.assertEqual(signal, 'BUY')

    def test_signal_generation_sell(self):
        # Force a SELL signal condition
        # 1. Fast EMA < Slow EMA
        # 2. Stoch K crossed below Stoch D, and K > 80

        data = {
            'ema_fast': [1.00, 1.00, 1.00, 1.00],
            'ema_slow': [1.05, 1.05, 1.05, 1.05],
            'stoch_k': [90, 85, 81, 80],  # -3 was 85, -2 now 81 (Overbought)
            'stoch_d': [81, 82, 83, 82]   # -3 K above D, -2 K below D (Cross down)
        }
        df = pd.DataFrame(data)

        signal = self.strategy.get_signal(df)
        self.assertEqual(signal, 'SELL')

    def test_sl_tp_calculation(self):
        current_price = 1.1000
        atr_value = 0.0010

        # Test BUY
        sl, tp = self.strategy.calculate_sl_tp('BUY', current_price, atr_value)
        # SL = 1.1000 - (0.0010 * 1.0) = 1.0990
        # TP = 1.1000 + (0.0010 * 1.5) = 1.1015
        self.assertAlmostEqual(sl, 1.0990)
        self.assertAlmostEqual(tp, 1.1015)

        # Test SELL
        sl, tp = self.strategy.calculate_sl_tp('SELL', current_price, atr_value)
        # SL = 1.1000 + (0.0010 * 1.0) = 1.1010
        # TP = 1.1000 - (0.0010 * 1.5) = 1.0985
        self.assertAlmostEqual(sl, 1.1010)
        self.assertAlmostEqual(tp, 1.0985)

    def test_bot_single_trade_execution_mock(self):
        # Ensure positions are empty
        self.bot.mt5.mt5._simulate_market_movement()

        # Manually create a dataframe that triggers a BUY
        data = {
            'time': pd.date_range(start='1/1/2023', periods=50, freq='min'),
            'open': [1.1000] * 50,
            'high': [1.1000] * 50,
            'low': [1.1000] * 50,
            'close': [1.1000] * 50,
            'ema_fast': [1.05] * 50,
            'ema_slow': [1.00] * 50,
            'stoch_k': [15] * 48 + [19, 20],
            'stoch_d': [18] * 48 + [17, 18],
            'atr': [0.0010] * 50
        }
        df = pd.DataFrame(data)

        # Override the MT5 mock get_historical_data to return our forced df
        # and skip calculate_indicators
        self.bot.mt5.get_historical_data = lambda *args: df
        self.bot.strategy.calculate_indicators = lambda x: x

        # Process a tick
        self.bot.process_tick()

        # Verify a trade was opened
        positions = self.bot.mt5.get_open_positions(config.SYMBOL)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].type, self.bot.mt5.mt5.ORDER_TYPE_BUY)

        # Process another tick. No new trade should be opened because of risk management
        self.bot.process_tick()
        positions = self.bot.mt5.get_open_positions(config.SYMBOL)
        self.assertEqual(len(positions), 1)

if __name__ == '__main__':
    unittest.main()
