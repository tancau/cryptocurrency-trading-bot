# 🤖 Cryptocurrency Trading Bot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

A modular, automated cryptocurrency trading bot designed for **Binance Spot & Futures**. Built with Python, it features technical analysis indicators, risk management, and multi-mode support (Paper Trading, Testnet, Live).

> **Disclaimer**: This software is for educational purposes only. Do not risk money you cannot afford to lose.

## ✨ Features

- **Multi-Mode Support**:
  - 📝 **Paper Trading**: Simulate trades with zero risk.
  - 🧪 **Testnet**: Test strategies on Binance Futures/Spot Testnet.
  - 🚀 **Live Trading**: Execute real trades with API keys.
- **Technical Analysis**:
  - Built-in indicators: RSI, MACD, Bollinger Bands, EMA/SMA.
  - Configurable strategies via YAML files.
- **Risk Management**:
  - Position sizing, Stop-Loss, Take-Profit, and Trailing Stop logic.
  - Daily loss limits and drawdown protection.
- **Notifications**:
  - 📱 **Telegram Integration**: Real-time trade signals, risk alerts, and daily PnL reports.
- **Futures Ready**:
  - Support for Leverage and Margin Mode (Isolated/Cross).

## 📂 Project Structure

```
cryptocurrency-trading/
├── config/                  # Configuration files (strategies & API keys)
├── modules/                 # Core logic modules
│   ├── analysis.py          # Technical indicators & signals
│   ├── execution.py         # Order execution (CCXT)
│   ├── monitor.py           # Market data monitoring
│   ├── risk.py              # Risk management logic
│   └── telegram_alert.py    # Telegram notification system
├── scripts/                 # Helper scripts
│   ├── install_dependencies.sh
│   └── run-testnet.sh
├── main_control.py          # Main entry point
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/cryptocurrency-trading-bot.git
cd cryptocurrency-trading-bot

# Install dependencies using the helper script
./scripts/install_dependencies.sh
```

### 2. Configuration

**API Keys**:
Create your environment config file from the template:

```bash
cp config/example-keys.env config/api-keys.testnet.env
nano config/api-keys.testnet.env
```

**Trading Preferences**:
Customize your strategy in `config/preferences_spot.yaml` or `config/preferences_futures.yaml`:

```yaml
trading_strategy:
  risk_level: moderate
  max_position_size_pct: 10
  stop_loss_pct: 5
  take_profit_pct: 8
```

### 3. Usage

**📝 Paper Trading (Simulation)**
```bash
python3 main_control.py --mode paper
```

**🧪 Testnet (Futures)**
```bash
./scripts/run-testnet.sh
```
*Or manually:*
```bash
python3 main_control.py --mode testnet --config config/preferences_futures.yaml --env-file config/api-keys.testnet.env
```

**🚀 Live Trading**
```bash
python3 main_control.py --mode live --config config/preferences_live.yaml --env-file config/api-keys.live.env
```

## 🛠️ Development

### Adding a New Strategy
Modify `modules/analysis.py` to implement new indicators or signal logic. The `generate_signals` method is the core entry point for strategy logic.

### Running Tests
(Optional) Run unit tests to verify logic:
```bash
python3 -m unittest discover tests
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
