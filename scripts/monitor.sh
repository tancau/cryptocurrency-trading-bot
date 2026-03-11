#!/bin/bash
# ====================================================================
# Trading Monitor Dashboard 📊👁️
# 实时监控交易服务的状态、日志和警报
# ===================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/trading.log"
SERVICE_STATUS="/etc/systemd/system/trading.service"
PID_FILE="$PROJECT_DIR/runs/trading.pid"

echo "╔════════════════════════════════════════╗"
echo "║  📊 Trading Monitor Dashboard ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务状态
echo -e "${BLUE}Service Status:${NC}"
if [ -f "$SERVICE_STATUS" ]; then
    if systemctl is-active trading.service 2>/dev/null; then
        echo -e "${GREEN}✅ Trading service is RUNNING${NC}"
    else
        echo -e "${YELLOW}⚠️ Trading service is NOT running${NC}"
    fi
    
    # 显示服务状态
    systemctl status trading.service --no-pager -l 2>/dev/null | tail -5 || true
else
    echo "❌ Systemd service not found. Service may not be installed."
fi

# 检查进程
echo ""
echo -e "${BLUE}Process:${NC}"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Process $PID is alive${NC}"
        ps aux | grep "[m]ain_control.py" || true
    else
        echo -e "${RED}❌ Process $PID has died (or PID file stale)${NC}"
        # 清理旧的 PID 文件
        rm -f "$PID_FILE"
    fi
else
    echo "⚠️ No PID file found. Check if service was started."
fi

# 日志统计
echo ""
echo -e "${BLUE}Logs:${NC}"
if [ -f "$LOG_FILE" ]; then
    lines=$(wc -l < "$LOG_FILE")
    size=$(du -h "$LOG_FILE" | cut -f1)
    
    echo "• Lines: $lines"
    echo "• Size: $size"
    
    # 最近错误
    echo ""
    echo -e "${BLUE}Recent Errors:${NC}"
    grep -i "error\|exception\|failed" "$LOG_FILE" | tail -5 || echo "  No recent errors found."
else
    echo "⚠️ Log file not found. Service may not have run yet."
fi

# 运行状态（如果可用）
echo ""
echo -e "${BLUE}Running Status:${NC}"
if systemctl is-active trading.service 2>/dev/null; then
    running=$(systemctl status trading.service --no-pager -l 2>/dev/null | grep -c "Main function" || echo "0")
    
    if [ "$running" -gt 0 ]; then
        echo -e "${GREEN}Trading is actively monitoring markets${NC}"
    fi
fi

# 提示
echo ""
echo -e "${BLUE}Commands:${NC}"
echo "  • View logs: tail -f $LOG_FILE"
echo "  • Restart service: sudo systemctl restart trading.service"
echo "  • Enable service: sudo systemctl enable trading.timer"
echo "  • Disable service: sudo systemctl disable trading.timer"
echo ""
