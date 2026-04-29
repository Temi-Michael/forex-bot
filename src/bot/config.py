# Configuration for the Scalping Bot

SYMBOL = "EURUSD"
TIMEFRAME_MINUTES = 1 # We use 1-minute chart for ultra-fast scalping
TRADE_VOLUME = 0.01 # 0.01 micro-lots for $100 capital
MAGIC_NUMBER = 777777 # Unique ID for bot's trades

# Strategy Parameters
EMA_FAST = 9
EMA_SLOW = 21

# Stochastic Parameters
STOCH_K = 14
STOCH_D = 3
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# Risk Management Parameters
ATR_PERIOD = 14
# How many times the ATR to use for Stop Loss and Take Profit
# E.g. 1.5 means TP is 1.5x the current candle's average volatility
ATR_MULTIPLIER_SL = 1.0
ATR_MULTIPLIER_TP = 1.5 # 1:1.5 Risk-Reward Ratio
