# Deriv Over/Under Bot

This folder contains a custom trading bot designed to trade the **Digit Over/Under** market using the Deriv WebSocket API. The bot allows you to seamlessly switch between different asset classes, such as Synthetic Indices and Forex pairs, directly from the terminal when starting the bot.

## Strategy Logic

The bot implements a statistical Last Digit Prediction (LDP) strategy:
1. It maintains a rolling window of the last **X ticks** (e.g., 500 ticks, customizable).
2. It extracts the last digit of the price for each of these ticks.
3. It calculates the **median** of these digits.
4. **Execution:**
   - If the median is **> 4.5**, the bot opens a **DIGITOVER 2** position.
   - If the median is **< 4.5**, the bot opens a **DIGITUNDER 7** position.

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

**Synthetic Indices:**
- `R_10` (Volatility 10 Index)
- `R_25` (Volatility 25 Index)
- `R_50` (Volatility 50 Index)
- `R_75` (Volatility 75 Index)
- `R_100` (Volatility 100 Index)

**Forex Pairs:**
- `frxEURUSD` (EUR/USD)
- `frxGBPUSD` (GBP/USD)
- `frxUSDJPY` (USD/JPY)
- `frxAUDUSD` (AUD/USD)
