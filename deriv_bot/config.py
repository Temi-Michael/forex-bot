import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Deriv API credentials
API_TOKEN = os.getenv("DERIV_API_TOKEN", "")
APP_ID = os.getenv("DERIV_APP_ID", "1089")

# ==========================================
# Default Bot Configuration
# These values act as fallbacks if interactive
# mode is skipped.
# ==========================================

# Sample Synthetic Indices Symbols:
# "R_10"   -> Volatility 10 Index
# "R_25"   -> Volatility 25 Index
# "R_50"   -> Volatility 50 Index
# "R_75"   -> Volatility 75 Index
# "R_100"  -> Volatility 100 Index

# Sample Forex Symbols:
# "frxEURUSD" -> EUR/USD
# "frxGBPUSD" -> GBP/USD
# "frxUSDJPY" -> USD/JPY
# "frxAUDUSD" -> AUD/USD

SYMBOL = "R_100"               # Default symbol
STAKE_AMOUNT = 1.00            # Amount to stake per trade
TICK_WINDOW = 500              # Number of past ticks to analyze
TRADE_DURATION = 1             # Duration in ticks for the contract

# Execution Settings
MAX_RUNS = 0                   # Number of trades to execute before stopping (0 = continuous)
SLEEP_BETWEEN_TRADES = 5       # Seconds to wait after a trade finishes before looking for the next setup
