import sys
import os

# Add src directory to path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/src")

from bot.bot import TradingBot
import logging

if __name__ == "__main__":
    logging.info("Starting up...")

    # Check if we are running on Windows
    is_windows = sys.platform.startswith('win')

    # If not on Windows, force mock mode because MT5 python library is Windows-only
    use_mock = not is_windows

    if use_mock:
        logging.warning("Non-Windows OS detected or requested. Running in MOCK mode.")
    else:
        logging.info("Windows detected. Attempting to connect to live MT5 terminal.")

    bot = TradingBot(use_mock=use_mock)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()
