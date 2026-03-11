#!/bin/bash
# 自动运行系统 - 测试网模式 (Binance Futures)
# 自动从 Binance API 获取账户余额

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$PROJECT_ROOT"

CONFIG_FILE="${WORK_DIR}/config/api-keys.testnet.env"
LOG_DIR="${WORK_DIR}/logs"
RUNS_DIR="${WORK_DIR}/runs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 初始化变量
STARTUP_CAPITAL="1000.0"
USE_API_BALANCE="false"
BINANCE_API_KEY=""
BINANCE_API_SECRET=""
BASE_URL="https://testnet.binancefuture.com/api/v3"

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}   自动运行系统 - Binance 测试网版${NC}"
echo -e "${BLUE}================================================${NC}"
echo "📂 Working Directory: $WORK_DIR"
echo ""

# 检查是否以 root 运行 (避免 sudo)
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}⚠️ 错误: 请不要以 root 身份运行!${NC}"
    exit 1
fi

# 创建必要目录
mkdir -p "${LOG_DIR}" "${RUNS_DIR}" /tmp/claw

# 加载配置文件 (允许失败)
source "${CONFIG_FILE}" 2>/dev/null || true

echo "📋 系统配置:"
echo "   交易所:        ${BINANCE_EXCHANGE:-Binance}"
echo "   测试网模式:    ${BINANCE_TESTNET_MODE:-false}"
echo "   启用交易:      ${TRADING_ENABLED:-true}"
echo ""

# 💰 从 API 获取账户余额 (如果启用)
echo -e "${GREEN}💰 正在从 Binance 测试网 API 获取账户余额...${NC}"
echo ""

# 导出配置变量
export $(grep -v '^#' "${CONFIG_FILE}" | xargs) 2>/dev/null || true

USE_API_BALANCE="${USE_API_BALANCE:-false}"
STARTUP_CAPITAL="${STARTUP_CAPITAL:-1000.0}"
BINANCE_API_KEY="${BINANCE_API_KEY:-}"
BINANCE_API_SECRET="${BINANCE_API_SECRET:-}"

# 检查 API 凭证是否设置
if [ -z "$BINANCE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  未找到 Binance API 密钥。${NC}"
    echo ""
    echo "要启用 API 余额获取:"
    echo "1. 添加到 config/api-keys.testnet.env:"
    echo "   BINANCE_API_KEY='your-api-key'"
    echo "   BINANCE_API_SECRET='your-api-secret'"
    echo ""
else
    # 获取账户信息并计算总余额
    echo "  🔄 正在连接 Binance 测试网 API..."
    
    ACCOUNT_RESPONSE=$(curl -s -X POST "${BASE_URL}/account" \
      -d "apiKey=${BINANCE_API_KEY}" \
      -H "X-MBX-APIKEY: ${BINANCE_API_KEY}")

    if [ -n "$ACCOUNT_RESPONSE" ] && echo "$ACCOUNT_RESPONSE" | grep -q '"balances"'; then
        # 解析 JSON 并计算 USDT 总余额
        TOTAL_BALANCE=$(echo "$ACCOUNT_RESPONSE" | python3 -c "import sys, json; 
            try:
                data = json.load(sys.stdin); 
                balances = data.get('balances', []); 
                total = sum(float(b['free']) * {'usdt': 1, 'btc': 45000, 'eth': 2500}.get(b['asset'], 1) for b in balances if float(b['free']) > 0); 
                print(f'{total:.2f}')
            except Exception as e:
                print('Error')")
        
        if [ -n "$TOTAL_BALANCE" ] && [ "$(echo "$TOTAL_BALANCE" | head -c1)" != "Error" ]; then
            echo ""
            echo -e "${GREEN}  ✅ 余额获取成功:${NC}"
            echo -e "     • 账户可用: \$${TOTAL_BALANCE} USDT"
            echo -e "  🎯 初始资金设置为: \$$TOTAL_BALANCE USDT"
            # 导出实际余额供 main_control.py 使用
            export STARTUP_CAPITAL="$TOTAL_BALANCE"
        else
            echo ""
            echo -e "${YELLOW}  ⚠️ 解析余额响应出错。${NC}"
            echo "  🔄 回退到默认配置: \$$STARTUP_CAPITAL USDT"
        fi
    else
        echo ""
        echo -e "${YELLOW}  ⚠️ API 调用失败或未找到余额。${NC}"
        echo "  🔄 使用默认初始资金: \$$STARTUP_CAPITAL USDT"
    fi
    
    echo ""
fi

# 显示最终资金金额
echo -e "${BLUE}📊 最终配置:${NC}"
echo -e "   初始资金: \$$STARTUP_CAPITAL USDT"
echo ""

# 检查交易是否启用
if [ "$TRADING_ENABLED" = "true" ]; then
    echo -e "${GREEN}✅ 交易已启用${NC}"
else
    echo -e "${YELLOW}⚠️  交易已禁用 (仅测试网模式)${NC}"
fi

echo ""
# 生成报告
echo "正在生成日报..."
cd "${WORK_DIR}" || exit

# 确保 python3 在 PATH 中
export PYTHONPATH="${PYTHONPATH}:${WORK_DIR}" 2>/dev/null || true
pythonpath=$(dirname "$0")
export PYTHONPATH="${PYTHONPATH}:${pythonpath}" 2>/dev/null || true

# 启动交易循环
# 使用虚拟环境的 python 如果存在
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD main_control.py --start 2>&1 | tee -a logs/trading.log || {
    echo ""
    echo "⚠️ 主控制程序失败。检查日志以获取错误:"
    tail -50 logs/trading.log 2>/dev/null || true
}

echo ""
echo "🎉 系统就绪! 正在监控..."
echo "日志位置: ${LOG_DIR}/trading.log"
echo "状态位置: ${WORK_DIR}/STATUS.md"
