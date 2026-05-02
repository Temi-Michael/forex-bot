# Trading Bots Monorepo

Welcome to the Trading Bots monorepo. This repository contains multiple, highly optimized, and independent trading bots designed for different platforms and trading strategies.

## Monorepo Architecture

To ensure a clean development and execution environment, **each bot is fully isolated into its own dedicated folder**. This means:
- No dependency conflicts between different bots.
- No shared entry points or messy global configurations.
- You can treat each folder as its own standalone project.

**How to use any bot in this repository:**
1. Navigate into the specific bot's directory: `cd <bot_folder>`
2. Install its isolated dependencies: `pip install -r requirements.txt`
3. Read the bot's local `README.md` for specific setup steps (like setting up `.env` files).
4. Run the bot directly from inside its folder.

---

## Available Bots

### 1. MT5 Forex Scalping Bot
- **Directory:** `mt5_bot/`
- **Platform:** MetaTrader 5 (Requires Windows Environment)
- **Strategy:** EMA, Stochastic, and ATR-based scalping
- **Description:** A fast-paced algorithmic trading bot designed specifically for Forex trading utilizing micro-lots (0.01) and tight risk management. It dynamically calculates Stop Loss and Take Profit based on current market volatility (ATR) and uses Stochastics for rapid entries.

### 2. Deriv Digit Over/Under Bot
- **Directory:** `deriv_bot/`
- **Platform:** Deriv WebSocket API (Cross-platform Python)
- **Strategy:** Last Digit Prediction (LDP) Median Strategy
- **Description:** A low-latency bot trading Over/Under contracts on Synthetic Indices (e.g., Volatility 100) or Forex. It uses a moving window of recent tick digits (e.g., last 500 ticks), strictly formatting based on symbol pip sizes to find the median. It also features a fully interactive terminal setup on startup and an optional Martingale recovery system.
