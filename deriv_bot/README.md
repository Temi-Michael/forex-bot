# Deriv Over/Under Bot

This folder contains a custom trading bot designed to trade the **Digit Over/Under** market using the Deriv WebSocket API. The bot allows you to seamlessly switch between different asset classes, such as Synthetic Indices and Forex pairs, directly from the terminal when starting the bot.

## Features & Strategy Logic

### 1. Selectable Strategy Modes
Because Deriv ticks are pseudorandom (each digit 0-9 has a 10% probability), predicting digits relies on mean reversion rather than pure direction. The bot now offers three interactive modes using **Over 3** (wins 60%) and **Under 6** (wins 60%):

1. **Auto Median Mode:** Maintains a rolling window of the last X ticks. If the median is high (> 4.5), it follows the momentum/trend and trades **Over 3**. If the median is low (< 4.5), it follows the trend downward and trades **Under 6**.
2. **Strict OVER 3 Mode:** Tracks the very last few ticks. If a streak of low digits occurs (e.g., three digits under 3 in a row), it executes a **DIGITOVER 3** expecting a mean reversion.
3. **Strict UNDER 6 Mode:** Similar to above, if a streak of high digits occurs (e.g., three digits over 6 in a row), it executes a **DIGITUNDER 6**.

### 2. Take Profit & Risk Management
When starting the bot, you are prompted to enter a **Target Take Profit**. The bot continuously monitors your session P/L and will automatically stop trading once this profit target is reached.

### 3. Martingale Recovery System
You can optionally enable a Martingale system to recover from losses.
- Because Over 3 / Under 6 has a safer **60% win rate**, the payout is naturally lower than a 50/50 trade. To recover losses mathematically, the default Martingale multiplier is set higher to **2.5**.
- If a trade loses, the bot multiplies the previous stake by this multiplier. To avoid Deriv "Invalid Price" API errors, stakes are automatically rounded to 2 decimal places.
- If it wins, the stake resets back to the initial amount.
- There is a maximum consecutive loss threshold (`MAX_MARTINGALE_LEVEL`) to protect your account. If this level is reached, the stake resets to the initial amount to prevent blowing the account.

### 4. Session Logging
Every time you run the bot, all terminal output is simultaneously saved to a `deriv_bot.log` file inside this folder. The file rotates automatically when it reaches 5MB, keeping a history of your past 3 sessions for review.

### 4. Graceful Shutdown
You can stop the bot at any time by pressing `Ctrl+C` in the terminal. The bot will catch the interrupt, suppress errors, cleanly close the WebSocket connection, and exit safely.

By using the standard Python `websockets` library rather than a heavy wrapper, the bot is optimized for the lowest possible latency during trade execution.

## Folder Structure

```
deriv_bot/
├── __init__.py           # Makes the directory a Python package
├── README.md             # This comprehensive setup guide
├── .env.example          # Template for your Deriv API credentials
├── config.py             # Default configuration and sample symbols
├── main.py               # The main entry point (includes interactive prompts)
├── strategy.py           # The mathematical logic for the LDP strategy
├── ws_client.py          # The low-latency WebSocket connection client
└── tests/                # Unit tests for the strategy logic
```

## Requirements & Installation

1. **Python 3.9+** must be installed on your system.
2. Navigate into the `deriv_bot` folder and install the necessary Python dependencies using pip:

```bash
cd deriv_bot
pip install -r requirements.txt
```

*Note: The primary dependencies for this bot are `websockets` and `python-dotenv`.*

## Setup Configuration (.env)

Before running the bot, you must authenticate it with your Deriv account.

1. While inside the `deriv_bot` directory, copy the example environment file to create your active `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your **Deriv API Token** and **App ID**.
   - You can generate an API Token from your Deriv account's Security & API settings (ensure it has Read and Trade scopes).
   - You can register an App ID on the Deriv Developers portal, or use a default one like `1089`.

## Running the Bot

Run the bot directly from inside the `deriv_bot` folder:

```bash
python main.py
```

### Interactive Prompts

When you run the bot, you will be prompted in the terminal. You no longer need to edit the code every time you want to change a setup!

1. **Use Interactive Setup:** It will ask if you want to use the default settings in `config.py` or configure them interactively.
2. **Asset Type:** You can choose between Synthetic Indices or Forex.
3. **Symbol:** You can choose the specific pair (e.g., Volatility 100 Index, EUR/USD).
4. **Tick Window:** You can specify how many past ticks the bot should analyze (e.g., 500).

### Sample Symbols

Here are common symbols you might use (these are also listed as comments in `config.py`):

**Synthetic Indices (Best Time: 24/7):**
Synthetic indices are simulated markets completely unaffected by real-world news or trading hours. They are available 24/7.
- `R_10` (Volatility 10 Index)
- `R_25` (Volatility 25 Index)
- `R_50` (Volatility 50 Index)
- `R_75` (Volatility 75 Index)
- `R_100` (Volatility 100 Index)
- `1HZ10V` (Volatility 10 (1s) Index)
- `1HZ100V` (Volatility 100 (1s) Index)

**Forex Pairs (Best Time: Session Overlaps):**
Forex pairs rely on real-world market volume. The best times to trade Forex digit strategies are during high-volume overlaps (e.g., London & New York overlap from 13:00 to 17:00 GMT).
- `frxEURUSD` (EUR/USD)
- `frxGBPUSD` (GBP/USD)
- `frxUSDJPY` (USD/JPY)
- `frxAUDUSD` (AUD/USD)
