import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Deriv API credentials
API_TOKEN = os.getenv("DERIV_API_TOKEN", "")
APP_ID = os.getenv("DERIV_APP_ID", "1089")

# Bot Configuration
SYMBOL = "R_100"               # e.g., Volatility 100 Index
STAKE_AMOUNT = 1.00            # Amount to stake per trade
TICK_WINDOW = 500              # Number of past ticks to analyze
TRADE_DURATION = 1             # Duration in ticks for the contract

# Execution Settings
MAX_RUNS = 0                   # Number of trades to execute before stopping (0 = continuous)
SLEEP_BETWEEN_TRADES = 5       # Seconds to wait after a trade finishes before looking for the next setup
