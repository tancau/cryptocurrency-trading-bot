# 🤖 Cryptocurrency Trading Bot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

[English](#-cryptocurrency-trading-bot) | [中文](#-加密货币交易机器人)

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

---

# 🤖 加密货币交易机器人

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

[English](#-cryptocurrency-trading-bot) | [中文](#-加密货币交易机器人)

一个专为 **Binance 现货与合约** 设计的模块化自动加密货币交易机器人。基于 Python 构建，集成了技术分析指标、风险管理以及多模式支持（模拟交易、测试网、实盘）。

> **免责声明**：本软件仅供教育用途。请勿使用您无法承受损失的资金进行风险交易。

## ✨ 功能特性

- **多模式支持**:
  - 📝 **模拟交易 (Paper Trading)**: 零风险模拟策略运行。
  - 🧪 **测试网 (Testnet)**: 在 Binance Futures/Spot 测试网上验证策略。
  - 🚀 **实盘交易 (Live Trading)**: 使用 API 密钥执行真实交易。
- **技术分析**:
  - 内置指标: RSI, MACD, 布林带 (Bollinger Bands), EMA/SMA。
  - 通过 YAML 配置文件灵活调整策略参数。
- **风险管理**:
  - 支持仓位管理、止损 (Stop-Loss)、止盈 (Take-Profit) 和移动止损 (Trailing Stop)。
  - 每日亏损限额和最大回撤保护。
- **消息通知**:
  - 📱 **Telegram 集成**: 实时推送交易信号、风险预警和每日盈亏日报。
- **合约支持**:
  - 支持调整杠杆倍数和保证金模式（逐仓/全仓）。

## 📂 项目结构

```
cryptocurrency-trading/
├── config/                  # 配置文件 (策略参数 & API 密钥)
├── modules/                 # 核心逻辑模块
│   ├── analysis.py          # 技术指标与信号分析
│   ├── execution.py         # 订单执行 (基于 CCXT)
│   ├── monitor.py           # 市场数据监控
│   ├── risk.py              # 风险管理逻辑
│   └── telegram_alert.py    # Telegram 通知系统
├── scripts/                 # 辅助脚本
│   ├── install_dependencies.sh
│   └── run-testnet.sh
├── main_control.py          # 程序主入口
└── requirements.txt         # Python 依赖包
```

## 🚀 快速开始

### 1. 安装

克隆仓库并安装依赖：

```bash
git clone https://github.com/YOUR_USERNAME/cryptocurrency-trading-bot.git
cd cryptocurrency-trading-bot

# 使用辅助脚本一键安装依赖
./scripts/install_dependencies.sh
```

### 2. 配置

**API 密钥**:
根据模板创建你的环境配置文件：

```bash
cp config/example-keys.env config/api-keys.testnet.env
nano config/api-keys.testnet.env
```

**交易偏好**:
在 `config/preferences_spot.yaml` 或 `config/preferences_futures.yaml` 中自定义你的策略：

```yaml
trading_strategy:
  risk_level: moderate       # 风险等级
  max_position_size_pct: 10  # 最大仓位占比
  stop_loss_pct: 5           # 止损百分比
  take_profit_pct: 8         # 止盈百分比
```

### 3. 使用方法

**📝 模拟交易 (仿真模式)**
```bash
python3 main_control.py --mode paper
```

**🧪 测试网 (合约模式)**
```bash
./scripts/run-testnet.sh
```
*或者手动运行：*
```bash
python3 main_control.py --mode testnet --config config/preferences_futures.yaml --env-file config/api-keys.testnet.env
```

**🚀 实盘交易**
```bash
python3 main_control.py --mode live --config config/preferences_live.yaml --env-file config/api-keys.live.env
```

## 🛠️ 开发指南

### 添加新策略
修改 `modules/analysis.py` 以实现新的指标或信号逻辑。`generate_signals` 方法是策略逻辑的核心入口。

### 运行测试
(可选) 运行单元测试以验证逻辑：
```bash
python3 -m unittest discover tests
```

## 🤝 贡献代码

欢迎提交代码！请随时发起 Pull Request。

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件。
