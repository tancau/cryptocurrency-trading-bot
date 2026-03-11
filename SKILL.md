---
name: cryptocurrency-trading
description: Automated cryptocurrency trading bot for Binance Spot and Futures with technical analysis and risk management.
---

# Cryptocurrency Trading Bot

A modular, automated trading system designed for Binance (Spot & Futures). It features technical analysis indicators (RSI, MACD, BB), risk management, and multi-mode support (Paper, Testnet, Live).

## Quick Reference

| Action | Command |
| :--- | :--- |
| **Install** | `./scripts/install_dependencies.sh` |
| **Run (Spot Testnet)** | `python3 main_control.py --mode testnet --config config/preferences_spot.yaml` |
| **Run (Futures Testnet)** | `python3 main_control.py --mode testnet --config config/preferences_futures.yaml` |
| **Run (Paper)** | `python3 main_control.py --mode paper` |
| **Monitor** | `tail -f logs/trading.log` |

## Prerequisites

- Python 3.10+
- Binance Account (for Testnet/Live API Keys)

## Configuration

### 1. API Keys
Create an environment file (e.g., `config/api-keys.testnet.env`) based on `config/example-keys.env`:

```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
# Optional: Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. Trading Preferences
Adjust strategies in `config/preferences_spot.yaml` or `config/preferences_futures.yaml`:
- **Risk**: `risk_level`, `max_position_size_pct`, `stop_loss_pct`
- **Analysis**: `timeframe`, `indicators`
- **Execution**: `leverage`, `margin_mode`

## Usage

### 1. Paper Trading (Simulation)
Safe mode for testing strategies without real API keys.
```bash
python3 main_control.py --mode paper
```

### 2. Testnet (Binance Futures/Spot Testnet)
Uses Binance Testnet environment.
```bash
# Spot
python3 main_control.py --mode testnet --config config/preferences_spot.yaml --env-file config/api-keys.testnet.spot.env

# Futures
python3 main_control.py --mode testnet --config config/preferences_futures.yaml --env-file config/api-keys.testnet.futures.env
```

### 3. Live Trading (Real Money)
⚠️ **Use with caution.**
```bash
python3 main_control.py --mode live --config config/preferences_live.yaml --env-file config/api-keys.live.env
```

## Modules Structure

- **`main_control.py`**: Entry point and orchestration.
- **`modules/analysis.py`**: Technical indicators (RSI, MACD, EMA, Bollinger Bands).
- **`modules/execution.py`**: Order execution via `ccxt` (supports Spot/Futures).
- **`modules/risk.py`**: Position sizing, stop-loss, and take-profit logic.
- **`modules/monitor.py`**: Market data fetching and loop management.
