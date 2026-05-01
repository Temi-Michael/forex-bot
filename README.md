# Trading Bots Monorepo

Welcome to the Trading Bots monorepo. This repository contains multiple, independent trading bots designed for different platforms and strategies.

To ensure a clean environment, each bot is isolated into its own folder with its own setup instructions, code, and `requirements.txt`. When you want to use a specific bot, simply navigate into its folder and follow the instructions in its specific `README.md`.

## Available Bots

### 1. MT5 Forex Scalping Bot
- **Directory:** `mt5_bot/`
- **Platform:** MetaTrader 5 (Windows only)
- **Strategy:** EMA, Stochastic, and ATR based scalping
- **Description:** A fast-paced bot designed for Forex trading utilizing micro-lots.

### 2. Deriv Digit Over/Under Bot
- **Directory:** `deriv_bot/`
- **Platform:** Deriv WebSocket API (Cross-platform)
- **Strategy:** Last Digit Prediction (LDP) Median Strategy
- **Description:** An interactive bot trading Over/Under contracts on Synthetic Indices or Forex based on a moving window of recent tick digits.
