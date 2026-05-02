# MT5 Scalping Bot

This is a fast-paced scalping bot designed for Forex trading using Python and MetaTrader 5 (MT5). It is specifically tailored for a $100 starting capital, utilizing 0.01 micro-lots and tight risk management.

## Strategy Overview

The bot uses a combination of indicators for fast entry and exit:
- **Exponential Moving Averages (EMA):** For detecting short-term trends.
- **Stochastic Oscillator:** For identifying rapid entry points (overbought/oversold conditions).
- **Average True Range (ATR):** To dynamically calculate Stop Loss (SL) and Take Profit (TP) based on current market volatility.

## Requirements

- A Windows Machine (The `MetaTrader5` Python library requires Windows and the MT5 terminal).
- MetaTrader 5 installed and logged into an account (Demo or Live).
- Python 3.9 or higher.

## Setup Instructions

1. **Install Python:** Ensure Python is installed on your Windows machine. You can download it from [python.org](https://www.python.org/). Check the box to "Add Python to PATH" during installation.
2. **Install Dependencies:** Open Command Prompt (cmd) or PowerShell, navigate to this folder, and run:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure MT5:**
   - Open your MetaTrader 5 terminal.
   - Go to `Tools` -> `Options` -> `Expert Advisors`.
   - Check "Allow algorithmic trading".
4. **Configure the Bot:**
   - Open `src/bot/config.py` (which we will create).
   - Ensure the symbol (e.g., `"EURUSD"`) and timeframe match your preference.

## Running the Bot

With MT5 open and logged in, open your Command Prompt in this folder and run:
```bash
python run.py
```
*(Make sure to test thoroughly on a Demo account first!)*
