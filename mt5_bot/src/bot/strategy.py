import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import StochasticOscillator
from ta.volatility import AverageTrueRange
import logging

class Strategy:
    def __init__(self, config):
        self.config = config

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds EMA, Stochastic, and ATR indicators to the dataframe.
        """
        if df.empty or len(df) < max(self.config.EMA_SLOW, self.config.ATR_PERIOD) + 5:
            logging.warning("Not enough data to calculate indicators.")
            return df

        # EMAs
        ema_fast = EMAIndicator(close=df['close'], window=self.config.EMA_FAST)
        ema_slow = EMAIndicator(close=df['close'], window=self.config.EMA_SLOW)
        df['ema_fast'] = ema_fast.ema_indicator()
        df['ema_slow'] = ema_slow.ema_indicator()

        # Stochastic Oscillator
        stoch = StochasticOscillator(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=self.config.STOCH_K,
            smooth_window=self.config.STOCH_D
        )
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()

        # ATR for dynamic SL/TP
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=self.config.ATR_PERIOD)
        df['atr'] = atr.average_true_range()

        # Drop NaN values created by window periods
        df.dropna(inplace=True)
        return df

    def get_signal(self, df: pd.DataFrame):
        """
        Analyzes the latest completed candles to determine buy/sell signals.
        Returns: 'BUY', 'SELL', or None
        """
        if df.empty or len(df) < 2:
            return None

        # Look at the last closed candle (index -2) and the one before it (index -3)
        # df.iloc[-1] is the current forming candle in MT5, so we avoid it to prevent repainting.
        last_closed = df.iloc[-2]
        prev_closed = df.iloc[-3]

        # BUY CONDITIONS
        # 1. Fast EMA is above Slow EMA (Uptrend)
        # 2. Stochastic was Oversold and K line crossed above D line
        buy_trend = last_closed['ema_fast'] > last_closed['ema_slow']
        buy_stoch_cross = (prev_closed['stoch_k'] < prev_closed['stoch_d']) and (last_closed['stoch_k'] > last_closed['stoch_d'])
        buy_stoch_oversold = last_closed['stoch_k'] < self.config.STOCH_OVERSOLD

        if buy_trend and buy_stoch_cross and buy_stoch_oversold:
            return 'BUY'

        # SELL CONDITIONS
        # 1. Fast EMA is below Slow EMA (Downtrend)
        # 2. Stochastic was Overbought and K line crossed below D line
        sell_trend = last_closed['ema_fast'] < last_closed['ema_slow']
        sell_stoch_cross = (prev_closed['stoch_k'] > prev_closed['stoch_d']) and (last_closed['stoch_k'] < last_closed['stoch_d'])
        sell_stoch_overbought = last_closed['stoch_k'] > self.config.STOCH_OVERBOUGHT

        if sell_trend and sell_stoch_cross and sell_stoch_overbought:
            return 'SELL'

        return None

    def calculate_sl_tp(self, signal, current_price, atr_value):
        """
        Calculates exact Stop Loss and Take Profit prices based on ATR.
        """
        sl_dist = atr_value * self.config.ATR_MULTIPLIER_SL
        tp_dist = atr_value * self.config.ATR_MULTIPLIER_TP

        if signal == 'BUY':
            sl = current_price - sl_dist
            tp = current_price + tp_dist
            return sl, tp
        elif signal == 'SELL':
            sl = current_price + sl_dist
            tp = current_price - tp_dist
            return sl, tp

        return None, None
