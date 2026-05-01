# Deriv Over/Under Bot

This folder contains a custom trading bot designed to trade the **Digit Over/Under** market on Deriv's Synthetic Indices using the Deriv WebSocket API.

## Strategy Logic

The bot uses a statistical Last Digit Prediction (LDP) strategy:
1. It maintains a rolling window of the last **500 ticks**.
2. It extracts the last digit of the price for each of these ticks.
3. It calculates the **median** of these 500 digits.
4. **Execution:**
   - If the median is **> 4.5**, the bot opens a **DIGITOVER 2** position.
   - If the median is **< 4.5**, the bot opens a **DIGITUNDER 7** position.

By using the standard Python `websockets` library rather than a heavy wrapper, the bot is optimized for the lowest possible latency during trade execution.

## Requirements

- Python 3.9+
- `websockets`
- `python-dotenv`

## Setup

1. Copy `.env.example` to a new file named `.env` inside this folder.
2. Add your **Deriv API Token** and **App ID** to the `.env` file. You can generate an API Token from your Deriv account security settings.
3. Edit `config.py` to adjust parameters like symbol (e.g., `R_100` for Volatility 100 Index), stake amount, or execution limits.

## Running the Bot

Run the bot from the root repository directory:

```bash
python -m deriv_bots.main
```
