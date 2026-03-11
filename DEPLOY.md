# 🚀 Deployment Guide - Auto-Runtime Trading System

## ✅ 已完成的工作（我为你准备好的）

### 📁 文件结构

```
cryptocurrency-trading/
├── config/                    # 配置文件目录
│   ├── api-keys.env          # ⚠️ API keys 配置（需要填写真实密钥）
│   ├── example-keys.env      # 模板文件（安全示例）
│   └── telegram.env          # Telegram 通知配置（可选）
│
├── modules/                   # 功能模块目录
│   ├── monitor.py            # 📊 市场监控模块
│   ├── analysis.py           # 🔮 技术分析模块
│   ├── risk.py               # ⚠️ 风险管理模块
│   ├── execution.py          # 💰 订单执行模块
│   └── telegram_alert.py     # 📱 Telegram 通知模块
│
├── scripts/                   # 管理脚本目录
│   ├── monitor.sh            # 📊 监控脚本
│   ├── rotate_logs.sh        # 📝 日志轮转脚本
│   ├── install_dependencies.sh # 📦 依赖安装脚本
│   └── run-testnet.sh        # ▶️ 测试网启动脚本
│
├── systemd/                   # systemd 服务文件（可选）
│   ├── trading.service       # 🔧 系统服务配置
│   └── trading.timer         # ⏰ 定时器配置
│
├── logs/                      # 📝 日志目录（自动创建）
│   └── .gitkeep              # 保持目录存在
│
├── reports/                   # 📊 日报输出目录（自动创建）
│   └── .gitkeep
│
├── runs/                      # 📋 PID 文件目录（自动创建）
│   └── .gitkeep
│
├── main_control.py           # 🤖 主控制脚本（Python）
├── SKILL.md                  # 📘 技能文档
├── metadata.json             # 📋 技能元数据
├── README.md                 # 📘 说明文档
├── DEPLOY.md                 # 📋 本部署指南
└── startup_guide.md          # 🚀 启动指南
```

---

## ⚡ Quick Start（5 步完成部署）

### Step 1: 安装依赖包

```bash
cd /home/tancau/.openclaw/workspace/skills/cryptocurrency-trading
./scripts/install_dependencies.sh
```

这会安装：
- requests, pyyaml, numpy, psutil
- python-telegram-bot（用于通知）

### Step 2: 配置 API Keys

编辑配置文件：

```bash
nano config/api-keys.env
```

填入你的 Binance API keys：

```env
BINANCE_API_KEY=your_real_binance_key_here
BINANCE_API_SECRET=your_real_binance_secret_here
```

**重要安全提示：**
- ✅ 使用只读权限的密钥（无 withdrawal）
- ❌ 不要将占位符 `your_binance_api_key_here` 保留
- 🔒 设置权限：`chmod 600 config/api-keys.env`

### Step 3: 启动系统服务

```bash
# 复制 systemd 文件到系统目录
sudo cp systemd/trading.service /etc/systemd/system/
sudo cp systemd/trading.timer /etc/systemd/system/

# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable trading.timer
sudo systemctl start trading.service

# 检查状态
sudo systemctl status trading.timer
```

### Step 4: 验证运行

```bash
# 查看监控脚本
./scripts/monitor.sh

# 或查看日志
tail -f logs/trading.log
```

预期输出示例：
```
✅ Service Status: RUNNING
✅ Process is alive
✅ Trading is actively monitoring markets
```

### Step 5: 配置警报（可选）

如果你想要 Telegram 通知，运行：

```bash
# 1. 创建 Bot 并获取 token
# https://t.me/BotFather

# 2. 获取 Chat ID
curl -X POST "https://api.telegram.org/bot<TOKEN>/getUpdates" \
     -H "Authorization: Bot<TOKEN>" \
     | jq '.result[0].chat.id'
```

然后设置环境变量：

```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

---

## 🔍 监控和维护

### 查看日志

```bash
# 实时日志
tail -f logs/trading.log

# 最近错误
grep -i "error\|exception" logs/trading.log | tail -20
```

### 运行状态检查

```bash
./scripts/monitor.sh
```

输出示例：
```
Service Status: ✅ Trading service is RUNNING
Process: ✅ Process 12345 is alive
Logs:
• Lines: 5284
• Size: 3.2M
Recent Errors: No recent errors found.
Running Status: Trading is actively monitoring markets
```

### 重启服务

```bash
sudo systemctl restart trading.service
```

### 禁用服务

```bash
sudo systemctl stop trading.service
sudo systemctl disable trading.timer
```

### 日志轮转（定期清理）

```bash
./scripts/rotate_logs.sh
```

---

## 🐛 Troubleshooting（故障排除）

### Issue: "No module named 'requests'"

解决方案：

```bash
pip install requests pyyaml numpy psutil python-telegram-bot
```

### Issue: "API keys not configured"

原因：配置文件中仍是占位符。

解决方法：

```bash
nano config/api-keys.env
# 填入真实密钥后保存退出
```

然后重启服务：

```bash
sudo systemctl restart trading.service
```

### Issue: "Service stopped automatically"

可能原因：
1. API key 无效或权限不足
2. 内存使用过高
3. 文件系统满

排查步骤：

```bash
# 检查日志
journalctl -u trading.service -n 50 --no-pager

# 检查磁盘空间
df -h

# 检查内存
free -m
```

### Issue: "Telegram alerts not working"

确保环境变量已设置：

```bash
echo "TELEGRAM_BOT_TOKEN=your_token" >> ~/.bashrc
echo "TELEGRAM_CHAT_ID=your_chat_id" >> ~/.bashrc
source ~/.bashrc
```

---

## 📋 Security Checklist（安全检查清单）

- [ ] API keys 已替换为真实值（非占位符）
- [ ] 配置文件权限正确：`chmod 600 config/api-keys.env`
- [ ] 使用只读 API keys（无 withdrawal 权限）
- [ ] systemd 服务文件配置了安全限制
- [ ] 日志轮转已启用（定期清理旧日志）
- [ ] 系统定期重启检查（`journalctl -u trading.service`）

---

## 🎯 Next Steps（后续步骤）

### 1. 每日报告（可选）

主脚本会自动生成日报并保存到 `reports/` 目录：

```bash
# 查看今天报告
cat reports/$(date +%Y-%m-%d).txt
```

### 2. Telegram 通知（推荐）

配置后，你会收到：
- ⚠️ 风险警告（止损触发、市场波动）
- 📊 每日市场报告
- 🔔 系统异常警报

### 3. 自定义策略

编辑 `main_control.py` 中的：
- `strategies` 列表（添加你的交易策略）
- `risk_limits` 配置（调整止盈止损）
- `markets` 列表（添加更多币种）

---

## 💡 Pro Tips（高级技巧）

### 优化内存使用

编辑 `/etc/systemd/system/trading.service`：

```ini
[Service]
MemoryLimit=256M      # 降低限制以适应低配服务器
CPUQuota=50%          # CPU 限制到 50%
```

### 配置多个交易所

复制并修改主脚本中的配置：

```python
# main_control.py
self.markets = {
    'binance': {
        'exchange': 'Binance',
        # ...
    },
    'coinbase': {
        'exchange': 'Coinbase',  # 添加 Coinbase
        # ...
    }
}
```

### Webhook 集成（进阶）

可以将警报发送到 Slack/Discord：

```python
# telegram_alert.py
def send_slack_alert(self, message: str):
    import requests
    url = f"https://hooks.slack.com/services/YOUR/WEBHOOK_URL"
    payload = {
        "text": message
    }
    requests.post(url, json=payload)
```

---

## 📞 Support（支持）

- **查看 README.md** - 使用说明文档
- **查看 startup_guide.md** - 详细启动步骤
- **查看 logs/trading.log** - 诊断问题
- **检查 systemd status** - 服务状态

---

## ⚠️ Important Reminders

1. **定期轮换 API keys**（建议每月或每季度）
2. **使用只读权限的密钥**（避免意外 withdrawal）
3. **启用日志轮转**（防止磁盘满）
4. **配置警报通知**（及时发现异常）
5. **定期检查系统健康**（内存、CPU、网络）

---

**Happy Trading! 💎🚀**

*Auto-Runtime System | OpenClaw Skills Project*
