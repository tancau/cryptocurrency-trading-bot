# 🎯 获取币安 Testnet API 密钥 - 完整教程

## ⚡ 为什么使用 Testnet（测试网络）

- 💎 **零资金风险** - 使用虚拟资金练习交易
- 📊 **真实市场数据** - 与生产环境相同的行情波动
- 🧪 **完美验证策略** - 在部署前确认逻辑正确性
- 🔔 **完整 API 响应** - 体验完整的订单执行流程

---

## 📍 Step 1: 访问币安测试网络

打开浏览器，访问：  
👉 https://testnet.binancefuture.com/

或扫码进入官方页面（推荐）：

```
https://testnet.binancefuture.com/
```

---

## 🔑 Step 2: 复制 API 密钥

进入页面后，你会看到类似这样的界面：

```
+---------------------------------+
|  +------------------------+     |
|  |                        |     |
|  |      Your             |     |
|  |   Testnet API Key:    |     |
|  |   1234...abcd         |     |
|  |                        |     |
|  +------------------------+     |
|                                 |
|  +------------------------+     |
|  |                        |     |
|  |      Your             |     |
|  |   Testnet Secret Key: |     |
|  |   xyz...qrst          |     |
|  |                        |     |
|  +------------------------+     |
|                                 |
|  +------------+  +-------------+|
|  | API Address|  | Websocket   ||
|  +------------+  | Address     ||
|                  +-------------+|
+---------------------------------+
```

### ✅ 如何操作：

1. **点击 "Copy"** 按钮复制 API Key（长字符串）
2. **点击 "Copy"** 按钮复制 Secret Key（另一串长字符）
3. 打开终端，编辑配置文件：

```bash
nano /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading/config/api-keys.testnet.env
```

4. 将复制的密钥粘贴到对应位置：

```env
BINANCE_API_KEY=1234...abcd       # 👈 粘贴在这里
BINANCE_API_SECRET=xyz...qrst     # 👈 粘贴在这里
```

5. **保存并退出**（Ctrl+X → Y → Enter）

---

## 📱 Step 3: 配置 Telegram 警报（可选但推荐）

### Option A: 使用 @BotFather 创建 Bot

1. 打开 Telegram，找到 **@BotFather**
2. 发送命令：`/newbot`
3. 按提示设置 bot 名称和用户名
4. 复制获得的 token，填入配置文件：

```env
TELEGRAM_BOT_TOKEN=123456:ABC...def
```

### Option B: 使用已有 Bot（如 @PingBot）

如果你想测试现有 Bot 的 Chat ID：

1. 添加任意 Bot 为好友（如 @PingBot, @GroupHelpBot）
2. 访问：https://api.telegram.org/bot<TOKEN>/getUpdates
3. 在响应中找到你的 chat_id

示例请求：
```bash
curl -X GET "https://api.telegram.org/bot123456:ABC.../getUpdates" \
     -H "Authorization: Bot123456:ABC..."
```

然后更新配置文件：

```env
TELEGRAM_CHAT_ID=-100123456789  # 👈 从上述响应中获取
ALERT_ON_STOP_LOSS=true         # 📊 止损触发时发送警报
ALERT_ON_TAKE_PROFIT=true       # 📊 止盈达成时发送警报
```

---

## 🔧 Step 4: 验证配置

运行配置检查脚本：

```bash
cd /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading
./scripts/check_config.sh
```

预期输出示例：
```
✅ Configuration file exists: config/api-keys.testnet.env
⚠️  No Telegram bot configured (optional)
✅ All required files present
```

---

## 🚀 Step 5: 启动模拟环境

### Option A: 使用 systemd（推荐）

```bash
# 1. 复制服务文件到系统目录
sudo cp /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading/systemd/trading.service /etc/systemd/system/
sudo cp /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading/systemd/trading.timer /etc/systemd/system/

# 2. 重载 systemd 配置
sudo systemctl daemon-reload

# 3. 启用并启动服务
sudo systemctl enable trading.timer
sudo systemctl start trading.service

# 4. 查看状态
sudo systemctl status trading.timer

# 5. 实时监控
tail -f /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading/logs/trading.log
```

### Option B: 手动运行（无需 root）

```bash
cd /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading

# 设置环境变量（临时生效）
export BINANCE_API_KEY=testnet_your_api_key_here
export BINANCE_API_SECRET=testnet_your_secret_here
export BINANCE_TESTNET_MODE=true

# 运行主脚本
python3 main_control.py --testnet --manual

# 或后台运行
nohup python3 main_control.py --testnet > logs/trading.log 2>&1 &
echo $! > runs/trading.pid
```

---

## 📊 Step 6: 观察和调试

### 查看实时日志

```bash
tail -f logs/trading.log
```

预期输出示例：
```
[INFO] ✓ Connected to Binance Testnet API
[INFO] ✓ Loaded 8 trading pairs (BTC, ETH, BNB...)
[INFO] ⚡ Starting market monitoring cycle...
[INFO] 📊 BTC/USDT: Price=$64500.00 | RSI=45 | Signal=BULLISH
[INFO] 💰 Opening position: Long 0.1 BTC @ $64500
[INFO] 🎯 Risk limit: Max loss 5% | Stop-loss set
[SUCCESS] ✓ Position opened successfully (trade ID: xxx)
```

### 测试订单执行

可以手动触发测试：

```bash
# 检查当前市场状态
curl -X GET "https://testnet.binancefuture.com/api/v3/ticker/24hr" \
     -H "Authorization: Bearer testnet_your_api_key_here"

# 查看模拟账户余额
curl -X GET "https://testnet.binancefuture.com/api/v3/account" \
     -H "Authorization: Bearer testnet_your_api_key_here" \
     -H "Content-Type: application/json"
```

---

## 🛠️ Step 7: 日常维护

### 重启服务

```bash
sudo systemctl restart trading.service
```

### 查看错误日志

```bash
grep -i "error\|exception" logs/trading.log | tail -20
```

### 清理旧日志

```bash
./scripts/rotate_logs.sh
```

---

## ⚠️ 重要提醒

1. **不要将测试密钥用于生产环境**  
   Testnet 密钥不能撤销或重置，只用于学习。

2. **真实资金请使用生产 API**  
   生产密钥通过官方网页获取（不是 Testnet）。

3. **定期更新配置**  
   建议每月检查一次 API 权限设置。

4. **使用只读权限**  
   即使在生产环境，也应使用无 withdrawal 权限的 keys。

---

## 🎯 下一步：切换到生产环境

当你确认策略在 Testnet 表现良好后：

### Option A: 直接创建生产密钥

1. 访问 https://www.binance.com/en/profile
2. API Management → Create New API Key
3. 复制新的生产密钥
4. 更新配置文件，改用生产环境设置

### Option B: 保持 Testnet（继续练习）

如果你喜欢继续学习算法，Testnet 是完美选择！

---

## 📞 需要帮助？

- 查看 README.md - 完整使用说明
- 查看 DEPLOY.md - 部署指南
- 查看 logs/trading.log - 诊断问题
- 检查 systemd status - 服务状态

---

**Happy Trading (in Testnet)! 💎🚀**

*Auto-Runtime System | Binance Futures Testnet Edition*
