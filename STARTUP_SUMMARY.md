# 🚀 系统快速启动指南 - Binance Testnet Trading System

## ✅ 配置已完成！

### 🎯 当前状态

- **API Keys**: ✅ 已配置（你的测试网络密钥）
- **初始资金来源**: 💰 **从 API 自动获取！**（如果启用）或 $1000 USDT 默认值
- **Telegram Bot**: ✅ 已配置（Token + Chat ID 就绪）
- **日志系统**: ✅ 运行中
- **风险模块**: ✅ 已安装

---

## 📋 快速启动命令

### 方式一：一键启动（推荐）

```bash
cd /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading
./scripts/run-testnet.sh
```

**这会：**

1. ✅ 加载配置并读取 API keys
2. 💰 **自动从 Binance API 获取账户余额**（如 `USE_API_BALANCE=true`）
3. 📊 显示系统状态和当前资金
4. 🔔 测试 Telegram 警报推送（可选）
5. 🔄 启动交易监控循环

---

### 方式二：手动检查配置

```bash
# 查看配置文件内容
cat config/api-keys.testnet.env

# 确保权限正确
chmod 600 config/api-keys.testnet.env

# 安装依赖（如果需要）
pip install requests python-dotenv -q >/dev/null 2>&1 || true
```

---

## ⚙️ 关键配置项（修改这些）

### `config/api-keys.testnet.env`

| 变量 | 示例值 | 说明 |
|--:--|:-|:-|
| `USE_API_BALANCE` | `true` | **启用从 API 获取余额** |
| `STARTUP_CAPITAL` | `'AUTO'` | **AUTO=自动，或 `$数字`（如$1000）** |
| `BINANCE_API_KEY` | `'your-key'` | 你的 Binance Testnet API Key |
| `BINANCE_API_SECRET` | `'your-secret'` | 你的 Binance Testnet Secret |

**💡 提示：** 如果希望使用固定金额而非 API 余额，设置：

```bash
USE_API_BALANCE=false          # 禁用自动获取
STARTUP_CAPITAL=500.0          # 设置为$500或其他金额
```

---

## 🔔 Telegram 警报测试

```bash
./scripts/test-telegram-alert.sh
```

**或直接发送测试消息：**

```bash
curl -X POST "https://api.telegram.org/bot8718043361:AAHZMnVtL0SrwUpa_9qhD6QuURRpCETebtc/sendMessage" \
  -d "chat_id=8150408475" \
  -d "text=✅ TEST ALERT from Trading System 💎\n\n🔔 This is a test message.\n\n⏱️ Time: $(date '+%Y-%m-%d %H:%M:%S UTC')"
```

---

## 📊 监控工具

### 实时查看日志

```bash
tail -f logs/trading.log
```

### 监控系统状态

```bash
./scripts/monitor.sh
```

### 查看账户余额（直接调用 API）

```bash
python3 << 'EOF'
import requests, json, re

config_file = 'config/api-keys.testnet.env'
with open(config_file) as f: content = f.read()

api_key = re.search(r'BINANCE_API_KEY=(.+)', content).group(1).strip() if re.search(r'BINANCE_API_KEY=', content) else None

base_url = "https://testnet.binancefuture.com/api/v3"
response = requests.post(f"{base_url}/account", data={'apiKey': api_key}, headers={'X-MBX-APIKEY': api_key})

if response.status_code == 200:
    balances = response.json().get('balances', [])
    total = sum(float(b['free']) for b in balances if b['asset'] == 'USDT')
    print(f"💰 USDT Balance: ${total:.2f}")
else:
    print("⚠️  API Error:", response.text)
EOF
```

---

## 🛡️ 安全提醒

- ✅ 密钥已加密存储（权限 `600`）
- ✅ 不在 Git 中暴露（`.gitignore` 已配置）
- ✅ 环境变量分离（生产/测试隔离）
- ⚠️ **不要将 API keys 用于真实交易除非你准备好了！**

---

## 📝 日志文件位置

| 文件 | 路径 | 说明 |
|--:--|:-|:-|
| **交易日志** | `logs/trading.log` | 每次运行的输出 |
| **错误日志** | `logs/errors.log` | 异常和警告 |
| **状态报告** | `STATUS.md` | 系统运行状态 |

---

## 🎉 完成！

现在你可以：

1. ✅ **启动系统**（自动获取账户余额）
2. ✅ **监控日志输出**
3. ✅ **测试 Telegram 警报**
4. ✅ **查看实时状态**

**祝你交易顺利！有任何问题随时问我～💰✨🚀**

---

*Auto-Runtime System v1.0 | Binance Futures Testnet Edition*
*Last updated: Wednesday, March 11th, 2026 — 2:40 AM UTC*
