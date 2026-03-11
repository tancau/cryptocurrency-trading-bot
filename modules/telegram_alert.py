#!/usr/bin/env python3
"""
Telegram Alert Receiver/Sender 📱
接收并发送交易警报通知
"""

import os
import requests
from datetime import datetime
import json

class TelegramNotifier:
    """Telegram 消息收发器"""
    
    def __init__(self, config_path=None):
        # 优先使用传入的 config_path
        self.token = None
        self.chat_id = None
        
        if config_path and os.path.exists(config_path):
             self._load_from_file(config_path)
             
        # 尝试从环境变量加载 (如果文件没加载到)
        if not self.token:
            self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.chat_id:
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # 如果还未找到，尝试默认路径
        if not self.token or not self.chat_id:
            try:
                base_dir = os.path.dirname(__file__)
                paths = [
                    os.path.join(base_dir, 'config', 'api-keys.testnet.env'),
                    os.path.join(base_dir, 'config', 'api-keys.env')
                ]
                for p in paths:
                    if os.path.exists(p):
                        self._load_from_file(p)
                        if self.token and self.chat_id:
                            break
            except Exception:
                pass
        
        # 清理
        if self.token:
             self.token = self.token.strip().strip("'").strip('"')
        if self.chat_id:
             self.chat_id = self.chat_id.strip().strip("'").strip('"')

        if not self.token or not self.chat_id:
            print("警告: Telegram 凭证未配置 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")

    def _load_from_file(self, path):
        try:
            with open(path, 'r') as f:
                for line in f:
                    if 'TELEGRAM_BOT_TOKEN=' in line:
                        val = line.split('=', 1)[1].strip()
                        # Only set if not already set (or overwrite? let's overwrite for now)
                        self.token = val.strip("'").strip('"')
                        if '#' in self.token:
                            self.token = self.token.split('#')[0].strip().strip("'").strip('"')
                    elif 'TELEGRAM_CHAT_ID=' in line:
                        val = line.split('=', 1)[1].strip()
                        self.chat_id = val.strip("'").strip('"')
                        if '#' in self.chat_id:
                            self.chat_id = self.chat_id.split('#')[0].strip().strip("'").strip('"')
        except Exception as e:
            print(f"Error loading Telegram config from {path}: {e}")
            
    def send_alert(self, message: str, alert_type: str = 'info') -> bool:
        """发送警报消息"""
        if not self.token or not self.chat_id:
            return False
            
        # Remove any whitespace or special chars from token/chat_id
        token_clean = self.token.strip()
        chat_id_clean = self.chat_id.strip()
            
        url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
        
        payload = {
            'chat_id': chat_id_clean,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        # Log payload for debugging (without full text if long)
        # print(f"DEBUG: Sending to {url} with chat_id={chat_id_clean}")
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                # 404 usually means invalid token or bot not started by user
                if response.status_code == 404:
                     # Check if it is really 404 or something else from response
                     try:
                         err_json = response.json()
                         if err_json.get('error_code') == 404:
                             print(f"Telegram 404 Error: {err_json.get('description')}")
                         else:
                             print(f"Telegram Error {response.status_code}: {response.text}")
                     except:
                         print(f"Telegram 404 Error: 请检查 Token 是否正确，或是否已在 Telegram 中启动 Bot。URL: .../bot{token_clean[:5]}.../sendMessage")
                else:
                     print(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            print(f"Exception sending alert: {e}")
            return False
    
    def generate_daily_report(self, prices: dict, summary: dict, account_info: dict = None, yesterday_balance: float = None) -> str:
        """生成日报消息"""
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now = datetime.now(beijing_tz)
        
        usdt_cny_rate = 7.2 # 估算汇率，实际应用中最好实时获取
        
        # 1. Header with distinct emoji and title
        report_lines = [
            "📑 *每日简报*",
            f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            "➖" * 12,
            ""
        ]
        
        # 账户资金概览 (如果有)
        if account_info:
            total_val = account_info.get('total_value_usdt', 0.0)
            initial_val = account_info.get('initial_capital', 0.0)
            
            # Use yesterday_balance passed from argument, or fallback to account_info if stored there
            if yesterday_balance is None:
                yesterday_balance = account_info.get('yesterday_balance', initial_val) # Default to initial if not found

            holdings = account_info.get('holdings', {})
            
            # holdings 结构可能是 {'spot': {...}, 'futures': {...}} 或者旧的扁平结构
            spot_holdings = {}
            futures_holdings = {}
            positions = []
            
            if 'spot' in holdings or 'futures' in holdings:
                spot_holdings = holdings.get('spot', {})
                futures_holdings = holdings.get('futures', {})
                positions = holdings.get('positions', [])
            else:
                spot_holdings = holdings # 假设全是现货
            
            total_val_cny = total_val * usdt_cny_rate
            
            report_lines.append("💎 *资产概览*")
            report_lines.append(f"💰 总资产: `${total_val:,.2f}` (≈¥{total_val_cny:,.0f})")
            
            # 昨日盈亏 (Day PnL)
            if yesterday_balance > 0:
                day_pnl = total_val - yesterday_balance
                day_pnl_pct = (day_pnl / yesterday_balance) * 100
                day_icon = "🟢" if day_pnl >= 0 else "🔴"
                report_lines.append(f"{day_icon} 昨日盈亏: `${day_pnl:+.2f} ({day_pnl_pct:+.2f}%)`")

            # 累计盈亏 (Total PnL)
            if initial_val > 0:
                pnl = total_val - initial_val
                pnl_pct = (pnl / initial_val) * 100
                pnl_icon = "🟢" if pnl >= 0 else "🔴"
                pnl_cny = pnl * usdt_cny_rate
                report_lines.append(f"{pnl_icon} 累计盈亏: `${pnl:+.2f} ({pnl_pct:+.2f}%)`")
            
            report_lines.append("")

            # 现货持仓详情
            if spot_holdings:
                report_lines.append("👜 *现货持仓*")
                has_spot = False
                for asset, amount in spot_holdings.items():
                    asset_val = 0.0
                    # Handle stablecoins as 1 USD
                    if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI']:
                        asset_val = amount
                    else:
                        symbol = f"{asset}USDT"
                        if symbol in prices:
                            asset_val = amount * prices[symbol]['price']
                    
                    # Only show significant holdings (> $1)
                    if asset_val > 1.0:
                         report_lines.append(f"• {asset}: `{amount:.4f}` (${asset_val:.0f})")
                         has_spot = True
                
                if not has_spot:
                    report_lines.append("• (无持仓或余额极小)")
                report_lines.append("")

            # 合约持仓详情
            if positions:
                report_lines.append("📊 *合约持仓*")
                for pos in positions:
                    sym = pos.get('symbol', 'Unknown')
                    # Format symbol: replace USDT with /USDT if not present, but usually we want clean display
                    # If sym is BTCUSDT, make it BTC/USDT
                    if 'USDT' in sym and '/' not in sym:
                         display_sym = sym.replace('USDT', '/USDT')
                    else:
                         display_sym = sym
                         
                    side = pos.get('side', '').upper()
                    amt = pos.get('amount', 0)
                    entry = pos.get('entryPrice', 0)
                    pnl = pos.get('unrealizedProfit', 0)
                    lev = pos.get('leverage', 1)
                    
                    side_icon = "🟢" if side == 'LONG' else "🔴"
                    pnl_str = f"+{pnl:.2f}" if pnl >= 0 else f"{pnl:.2f}"
                    
                    report_lines.append(f"{side_icon} *{display_sym}* {side} {lev}x")
                    report_lines.append(f"   数量: {amt} | 入场: {entry:.2f}")
                    report_lines.append(f"   未结盈亏: `${pnl_str}`")
                report_lines.append("")
        
        # 市场状态
        report_lines.append("📈 *行情监控*")
        
        for symbol, data in prices.items():
            # Filter out unwanted symbols (e.g. BNBUSDT) if user requested
            if symbol == 'BNBUSDT':
                continue
            
            # Format symbol: BTCUSDT -> BTC/USDT
            if 'USDT' in symbol and '/' not in symbol:
                display_sym = symbol.replace('USDT', '/USDT')
            elif 'USDC' in symbol and '/' not in symbol:
                display_sym = symbol.replace('USDC', '/USDC')
            else:
                display_sym = symbol
                
            pct_change = data.get('price_change_24h_pct', 0)
            status_icon = "🟩" if pct_change >= 0 else "🟥"
            
            report_lines.append(f"{status_icon} *{display_sym}*: `${data['price']:,.2f}` ({pct_change:+.2f}%)")
            
        report_lines.append("")
        report_lines.append("➖" * 12)
            
        return "\n".join(report_lines)

    def send_trade_signal(self, symbol: str, signal_type: str, price: float, reason: str, rsi: float = None, leverage: int = None):
        """发送交易信号通知"""
        
        # Distinct style for signals: Bold header, specific emojis
        signal_upper = signal_type.upper()
        
        # Format symbol for signal too
        if 'USDT' in symbol and '/' not in symbol:
            display_sym = symbol.replace('USDT', '/USDT')
        elif 'USDC' in symbol and '/' not in symbol:
             display_sym = symbol.replace('USDC', '/USDC')
        else:
             display_sym = symbol
        
        header_icon = "🔔"
        action_cn = signal_upper
        
        if "BUY" in signal_upper:
            header_icon = "🚀" 
            action_cn = "买入"
        elif "SELL" in signal_upper:
            header_icon = "🔻"
            action_cn = "卖出"
        elif "OPEN LONG" in signal_upper:
            header_icon = "📈"
            action_cn = "开多"
        elif "OPEN SHORT" in signal_upper:
            header_icon = "📉"
            action_cn = "开空"
        elif "CLOSE LONG" in signal_upper:
            header_icon = "💰"
            action_cn = "平多"
        elif "CLOSE SHORT" in signal_upper:
            header_icon = "💰"
            action_cn = "平空"

        # 使用 UTC+8 北京时间
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        
        message_lines = [
            f"{header_icon} *交易信号*",
            f"━━━━━━━━━━━━━━━━━━",
            f"📌 *{display_sym}*  ➡️  *{action_cn}*",
            f"💵 价格: `${price:,.2f}`",
        ]
        
        if leverage:
            message_lines.append(f"🔧 杠杆: `{leverage}x`")
            
        message_lines.append(f"📝 原因: _{reason}_")
        
        if rsi:
             message_lines.append(f"📊 RSI: `{rsi:.1f}`")
             
        message_lines.append(f"⏰ {now_beijing.strftime('%H:%M:%S')}")
        
        return self.send_alert("\n".join(message_lines))


if __name__ == "__main__":
    # 测试脚本
    import sys
    
    notifier = TelegramNotifier()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            message = sys.argv[2] if len(sys.argv) > 2 else "🔔 这是一条来自加密货币交易机器人的测试消息"
            print(f"正在发送测试消息: {message}")
            if notifier.send_alert(message):
                print("✅ 消息发送成功！")
            else:
                print("❌ 消息发送失败。请检查 Token 和 Chat ID。")
        elif sys.argv[1] == '--signal':
            # 测试发送交易信号模板
            print("🚀 正在发送测试交易信号...")
            success = notifier.send_trade_signal(
                symbol='BTCUSDT',
                signal_type='BUY',
                price=69500.50,
                reason='突破 EMA200 均线，RSI 低位金叉 (测试)',
                rsi=35.5,
                leverage=3
            )
            if success:
                print("✅ 交易信号模板测试已发送！")
            else:
                print("❌ 发送失败")
    else:
        print("Telegram 告警模块")
        print("="*50)
        print("使用方法:")
        print("   python telegram_alert.py --test [可选消息内容]")
        print("   python telegram_alert.py --signal  (发送测试交易信号)")
