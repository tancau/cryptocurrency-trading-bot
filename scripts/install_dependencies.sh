#!/bin/bash
# ====================================================================
# Install Dependencies Script 💎🚀
# 安装所有必要的 Python 依赖包
# ====================================================================

set -e

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Navigate to project root
cd "$PROJECT_ROOT" || { echo "❌ Failed to navigate to project root"; exit 1; }

echo "╔══════════════════════════════════════════╗"
echo "║  💎 Crypto Trading Dependencies Installer ║"
echo "╚══════════════════════════════════════════╝"
echo "📂 Project Root: $PROJECT_ROOT"
echo ""

# 创建虚拟环境（如果不存在）
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "✅ Virtual environment already exists."
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 升级 pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# 安装主要依赖
echo ""
echo "📦 Installing required packages..."
pip install -r requirements.txt || {
    echo "⚠️  Some packages failed to install. Running manual install..."
    pip install requests pyyaml numpy psutil telegram
}

# 验证安装
echo ""
echo "✅ Verifying installations..."
python3 -c "import requests, yaml, numpy, psutil; print('All core dependencies installed!')" || {
    echo "❌ Some dependencies are missing. Please run manually:"
    echo "   pip install requests pyyaml numpy psutil"
}

# 安装 Telegram 依赖（可选）
if [ -f "modules/telegram_alert.py" ]; then
    echo ""
    echo "📱 Installing Telegram support..."
    pip install python-telegram-bot || true
fi

# 创建 .gitkeep 文件以防目录为空
for dir in logs reports notifications config backups; do
    mkdir -p "$dir"
    touch "$dir/.gitkeep"
done

# 设置权限
echo ""
echo "🔧 Setting file permissions..."
chmod +x scripts/*.sh modules/telegram_alert.py || true

# 创建示例环境文件（安全）
if [ ! -f "config/example-keys.env" ]; then
    cat > config/example-keys.env << 'EOF'
# ============================================================
# ⚠️ 安全警告：此文件必须加密！不要提交到 Git
# 请勿将此模板文件上传到任何代码托管平台！
# ============================================================

# TODO: tancau, 请在此处填写你的交易所 API keys：
# BINANCE_API_KEY=your_binance_api_key_here
# BINANCE_API_SECRET=your_binance_secret_here

# 其他可选 API（按需添加）
# COINGECKO_API_KEY=your_coingecko_key_here

# Telegram 通知（可选）
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id
EOF
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Edit config/api-keys.env with your real API keys"
echo "  2. Run: sudo cp systemd/trading.service /etc/systemd/system/"
echo "  3. Run: sudo systemctl daemon-reload && sudo systemctl enable trading.timer"
echo ""

# 退出虚拟环境
deactivate 2>/dev/null || true
