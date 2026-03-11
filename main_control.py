#!/usr/bin/env python3
"""
Cryptocurrency Trading Auto-Runtime Controller 🤖
自动化交易控制主程序 - 你只需提供 API keys 即可！
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import yaml

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.monitor import MarketMonitor
from modules.analysis import TechnicalAnalysis
from modules.risk import RiskManager
from modules.execution import OrderExecutor
from modules.telegram_alert import TelegramNotifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingController:
    """交易控制主程序"""
    
    def __init__(self, mode='paper', config_path='config/preferences.yaml', env_path=None):
        self.mode = mode
        
        # Determine unique state file per mode/config
        # This prevents Spot and Futures overwriting each other's balance history
        config_name = os.path.basename(config_path).replace('.yaml', '')
        self.state_file = f"data/state_{mode}_{config_name}.json"
        
        # Set config file path
        self.preferences_path = config_path
        
        # Set environment file path (API Keys)
        if env_path:
            self.config_path = env_path
        elif self.mode == 'testnet':
            self.config_path = 'config/api-keys.testnet.env'
        else:
            self.config_path = 'config/api-keys.env'
            
        # Load env vars from config file to os.environ so other modules can use them
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            k, v = line.strip().split('=', 1)
                            os.environ[k.strip()] = v.strip()
            except Exception as e:
                logger.error(f"Failed to load env vars from {self.config_path}: {e}")
                
        # Also load from config/api-keys.env if we are in testnet mode, to get Telegram keys if they are missing
        if self.mode == 'testnet' and not os.environ.get('TELEGRAM_BOT_TOKEN'):
             live_config = 'config/api-keys.env'
             if os.path.exists(live_config):
                try:
                    with open(live_config, 'r') as f:
                        for line in f:
                            if 'TELEGRAM_BOT_TOKEN=' in line and 'TELEGRAM_BOT_TOKEN' not in os.environ:
                                k, v = line.strip().split('=', 1)
                                os.environ[k.strip()] = v.strip()
                            elif 'TELEGRAM_CHAT_ID=' in line and 'TELEGRAM_CHAT_ID' not in os.environ:
                                k, v = line.strip().split('=', 1)
                                os.environ[k.strip()] = v.strip()
                except Exception:
                    pass
        
        logger.info(f"正在初始化交易控制器，模式: {self.mode.upper()}")
        
        # 初始化各个模块
        # Monitor: 在 testnet 模式下可能需要使用 testnet 价格源
        self.monitor = MarketMonitor(self.config_path, testnet=(mode=='testnet'))
        self.analysis = TechnicalAnalysis()
        self.risk = RiskManager()
        # Executor: 传入交易模式
        self.executor = OrderExecutor(self.config_path, mode=self.mode)
        # 显式传递配置路径给 Telegram Notifier
        self.telegram = TelegramNotifier(config_path=self.config_path)
        
        # Initialize default config to avoid AttributeError if load_configuration isn't called
        self.strategy = {'risk_level': 'default'}
        self.initial_capital = 0.0
        self.monitor_config = {}
        self.analysis_config = {}
        self.execution_config = {}
        self.risk_config = {}
        
        self.report_interval_hours = 1 # 默认1小时
        
        self.running = False
        self.last_alert_time = datetime.now() - timedelta(hours=1)
        self.last_report_time = datetime.now()
        
        # Track daily balance
        self.yesterday_balance = 0.0
        self.last_day_check = datetime.now().day
        
        # Load persisted state
        self.load_state()

    def load_state(self):
        """Load persisted state from file"""
        if os.path.exists(self.state_file):
            try:
                import json
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.yesterday_balance = state.get('yesterday_balance', 0.0)
                    self.last_day_check = state.get('last_day_check', datetime.now().day)
                    # Also load initial_capital if available to preserve total PnL
                    if 'initial_capital' in state:
                         self.initial_capital = state['initial_capital']
                         
                    logger.info(f"Loaded state from {self.state_file}: yesterday_balance={self.yesterday_balance}, initial_capital={self.initial_capital}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def save_state(self):
        """Save state to file"""
        try:
            import json
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            state = {
                'yesterday_balance': self.yesterday_balance,
                'last_day_check': self.last_day_check,
                'initial_capital': self.initial_capital, # Save initial capital
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
        
    def check_api_keys_configured(self) -> bool:
        """检查 API keys 是否已配置（根据模式）"""
        if self.mode == 'paper':
            return True # Paper mode doesn't strictly need API keys
            
        if not os.path.exists(self.config_path):
            logger.warning("未找到 API 密钥文件。")
            return False
            
        with open(self.config_path, 'r') as f:
            content = f.read()
            
        if self.mode == 'live':
            if 'BINANCE_API_KEY=' not in content or 'your_binance_api_key_here' in content:
                logger.warning("Live API 密钥未配置。")
                return False
        elif self.mode == 'testnet':
            if 'BINANCE_TESTNET_API_KEY=' not in content:
                logger.warning("Testnet API 密钥未配置。")
                return False
                
        return True
    
    def load_configuration(self):
        """加载交易策略配置"""
        try:
            with open(self.preferences_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # 从配置文件读取策略参数
            self.strategy = self.config['trading_strategy']
            self.monitor_config = self.config['monitoring']
            self.report_interval_hours = self.monitor_config.get('report_interval_hours', 1)
            self.analysis_config = self.config['analysis']
            self.execution_config = self.config['execution']
            self.risk_config = self.config['risk_management']
            
            logger.info(f"策略已加载: {self.strategy['risk_level']}")
            
        except Exception as e:
            logger.error(f"加载配置出错: {e}")
            
    def run_monitoring_cycle(self) -> Dict:
        """运行监控周期"""
        cycle_start = datetime.now()
        logger.info(f"🔄 开始新的监控周期: {cycle_start.strftime('%H:%M:%S')}")

        if not self.monitor:
            return {'status': 'error', 'message': '监控器未初始化'}
            
        # 获取价格
        prices = self.monitor.get_market_prices(['BTCUSDT', 'ETHUSDT', 'BTCUSDC', 'ETHUSDC'])
        
        # 获取总览 (仅每 5 分钟或更长时间获取一次，避免 429)
        # 这里简单起见，我们暂时在监控循环中跳过 CoinGecko 调用，
        # 或者使用缓存的 summary (如果 TradingController 保存了它)
        # 为简化，这里暂不调用，summary 由日报生成时调用
        summary = {} 
        
        # 获取历史K线数据用于真实技术分析
        klines_data = {}
        for symbol in prices.keys():
            # 获取最近 100 根 1小时 K线
            klines = self.monitor.get_historical_klines(symbol, interval='1h', limit=100)
            if klines:
                klines_data[symbol] = klines
        
        # 分析市场 (传入 K线数据)
        signals = self.analysis.generate_signals(prices, klines_data)
        
        # 风险检查
        health_report = {}
        for symbol, price_data in prices.items():
            current_price = price_data['price']
            initial_price = 45000  # BTC 参考价（简化）
            health_report[symbol] = self.risk.check_portfolio_health(current_price, initial_price)
        
        # 检查警报条件
        alerts = self.monitor.check_alert_conditions(prices)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'prices': prices,
            'summary': summary,
            'signals': signals,
            'health': health_report,
            'alerts': alerts
        }
    
    def process_signals(self, data: Dict) -> List[str]:
        """处理分析信号并执行交易（在 API keys 配置后）"""
        actions = []
        
        if not self.monitor or not self.executor:
            return actions
            
        # 检查是否有警报需要处理
        for alert in data.get('alerts', []):
            logger.warning(f"告警: {alert['message']}")
            actions.append(f"⚠️ 触发告警: {alert['message']}")
            self.telegram.send_risk_warning(alert['message'])
            
        # 如果有配置好的 API keys，根据信号执行交易
        if self.check_api_keys_configured():
            enable_futures = self.strategy.get('enable_futures', False)
            leverage = self.strategy.get('leverage', 1)
            
            # 获取当前持仓 (Futures)
            positions = []
            total_balance = 0.0
            
            try:
                # 获取账户余额和持仓
                # 注意: get_total_balance_value 会再次调用 get_account_balance，这里优化一下或者直接调用
                balances = self.executor.get_account_balance()
                positions = balances.get('positions', [])
                
                # 计算总资产 (用于仓位管理)
                # 这里简单估算 USDT 余额 + 持仓价值，或者直接用可用余额
                # 为了简单起见，使用 total_balance_value
                total_balance = self.executor.get_total_balance_value(data.get('prices', {}))
                
            except Exception as e:
                logger.error(f"获取账户信息失败: {e}")

            for symbol, price_data in data.get('prices', {}).items():
                current_price = price_data['price']
                signal_info = data.get('signals', {}).get(symbol, {})
                
                signal_type = signal_info.get('signal')
                reason = signal_info.get('reason', '未知原因')
                rsi = signal_info.get('rsi_14')
                trend = signal_info.get('trend', 'neutral')
                
                # 查找当前 symbol 的持仓
                current_pos = next((p for p in positions if p['symbol'] == symbol or p['symbol'] == f"{symbol}:USDT"), None)
                pos_amt = current_pos['amount'] if current_pos else 0
                pos_side = current_pos['side'] if current_pos else None # 'long' or 'short'
                
                if signal_type == 'buy':
                    trend_icon = "📈" if trend == "bullish" else "📉" if trend == "bearish" else "➡️"
                    logger.info(f"🟢 {symbol} 出现买入信号 @ ${current_price:.2f} ({reason}) | 趋势: {trend_icon}")
                    
                    if enable_futures:
                        # Futures Logic
                        action_taken = False
                        
                        # 1. Close Short if exists
                        if pos_side == 'short' and pos_amt > 0:
                            logger.info(f"Closing SHORT for {symbol}")
                            # Buy to Cover
                            success = self.executor.place_futures_order(symbol, 'buy', pos_amt, current_price, params={'reduceOnly': True})
                            if success:
                                actions.append(f"📉 {symbol} 平空仓 (Close Short) - {reason}")
                                self.telegram.send_trade_signal(symbol, 'CLOSE SHORT', current_price, reason, rsi, leverage=current_pos.get('leverage', leverage))
                                action_taken = True
                            
                        # 2. Open Long if no position (or after closing short)
                        # Re-check position or assume closed? safe to just check if we want to open long.
                        # Usually strategies flip: close short then open long.
                        # Check if we already have a long position?
                        # If we just closed short, pos_amt is 0 (effectively).
                        # If we had long, we might add to it or hold. Here we assume "Open if no position".
                        
                        if not action_taken and (pos_side != 'long' or pos_amt == 0):
                            # Calculate quantity
                            # 10% of total balance * leverage / price
                            # quantity = (total_balance * 0.1 * leverage) / current_price
                            # Safety check for balance
                            trade_val = total_balance * 0.1
                            qty = (trade_val * leverage) / current_price
                            
                            # Ensure min qty (simplified)
                            if qty * current_price > 5: # Min 5 USDT
                                logger.info(f"Opening LONG for {symbol} (Qty: {qty:.4f})")
                                success = self.executor.place_futures_order(symbol, 'buy', qty, current_price)
                                if success:
                                    actions.append(f"📈 {symbol} 开多仓 (Open Long) - {reason}")
                                    self.telegram.send_trade_signal(symbol, 'OPEN LONG', current_price, reason, rsi, leverage=leverage)
                            else:
                                logger.warning(f"资金不足或数量太小，忽略开多: {qty}")

                    else:
                        # Spot Logic (Existing)
                        actions.append(f"📈 {symbol} 买入信号 - {reason}")
                        self.telegram.send_trade_signal(symbol, 'BUY', current_price, reason, rsi)
                        # 执行买入
                        success = self.executor.place_order(symbol, 'buy', 0.001, current_price)
                        if success:
                            self.telegram.send_alert(f"✅ *交易执行成功*\n已买入 {symbol} @ ${current_price:.2f}", alert_type='success')
                        else:
                            self.telegram.send_alert(f"❌ *交易执行失败*\n买入 {symbol} 失败，请检查日志", alert_type='error')
                    
                elif signal_type == 'sell':
                    trend_icon = "📈" if trend == "bullish" else "📉" if trend == "bearish" else "➡️"
                    logger.info(f"🔴 {symbol} 出现卖出信号 @ ${current_price:.2f} ({reason}) | 趋势: {trend_icon}")
                    
                    if enable_futures:
                        # Futures Logic
                        action_taken = False
                        
                        # 1. Close Long if exists
                        if pos_side == 'long' and pos_amt > 0:
                            logger.info(f"Closing LONG for {symbol}")
                            # Sell to Close
                            success = self.executor.place_futures_order(symbol, 'sell', pos_amt, current_price, params={'reduceOnly': True})
                            if success:
                                actions.append(f"📈 {symbol} 平多仓 (Close Long) - {reason}")
                                self.telegram.send_trade_signal(symbol, 'CLOSE LONG', current_price, reason, rsi, leverage=current_pos.get('leverage', leverage))
                                action_taken = True
                                
                        # 2. Open Short if no position
                        if not action_taken and (pos_side != 'short' or pos_amt == 0):
                             # Calculate quantity
                            trade_val = total_balance * 0.1
                            qty = (trade_val * leverage) / current_price
                            
                            if qty * current_price > 5:
                                logger.info(f"Opening SHORT for {symbol} (Qty: {qty:.4f})")
                                success = self.executor.place_futures_order(symbol, 'sell', qty, current_price)
                                if success:
                                    actions.append(f"📉 {symbol} 开空仓 (Open Short) - {reason}")
                                    self.telegram.send_trade_signal(symbol, 'OPEN SHORT', current_price, reason, rsi, leverage=leverage)
                            else:
                                logger.warning(f"资金不足或数量太小，忽略开空: {qty}")
                                
                    else:
                        # Spot Logic (Existing)
                        actions.append(f"📉 {symbol} 卖出信号 - {reason}")
                        self.telegram.send_trade_signal(symbol, 'SELL', current_price, reason, rsi)
                        # 执行卖出
                        success = self.executor.place_order(symbol, 'sell', 0.001, current_price)
                        if success:
                            self.telegram.send_alert(f"✅ *交易执行成功*\n已卖出 {symbol} @ ${current_price:.2f}", alert_type='success')
                        else:
                            self.telegram.send_alert(f"❌ *交易执行失败*\n卖出 {symbol} 失败，请检查日志", alert_type='error')
                else:
                    logger.info(f"⚪ {symbol} 无交易信号 (RSI: {rsi:.2f})")
                        
        return actions
    
    def run_daily_report(self):
        """生成日报"""
        logger.info("正在生成日报...")
        
        prices = self.monitor.get_market_prices(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'BTCUSDC', 'ETHUSDC'])
        
        # 获取账户资金
        # get_total_balance_value internally calls get_account_balance
        # We need breakdown for the report
        balances = self.executor.get_account_balance()
        total_val = self.executor.get_total_balance_value(prices)
        
        if self.initial_capital == 0 and total_val > 0:
            self.initial_capital = total_val
            # Save state immediately to lock in initial capital
            self.save_state()
            
            # If starting fresh, yesterday is same as initial
            if self.yesterday_balance == 0:
                self.yesterday_balance = total_val
            
        account_info = {
            'total_value_usdt': total_val,
            'initial_capital': self.initial_capital,
            'holdings': balances # Pass raw holdings {asset: amount}
        }
        
        # Update daily balance tracking if day changed
        current_day = datetime.now().day
        if current_day != self.last_day_check:
            # Day changed, update yesterday balance to what we had at last report (or now)
            # Ideally this logic should run exactly at 00:00 UTC, but here it runs on report interval.
            # We'll just use the current total_val as the new "yesterday" for tomorrow.
            # Wait, actually we need the value from *yesterday* to show in *today's* report.
            # So we should update self.yesterday_balance AFTER generating the report.
            pass

        # 生成并发送 Telegram 日报
        # 在生成日报时，才调用 CoinGecko 获取一次市场总览
        summary = self.monitor.get_market_summary()
        report_text = self.telegram.generate_daily_report(prices, summary, account_info, yesterday_balance=self.yesterday_balance)
        self.telegram.send_alert(report_text)
        
        # Update for next day
        if current_day != self.last_day_check:
             self.yesterday_balance = total_val
             self.last_day_check = current_day
             self.save_state() # Save new day state
        else:
             # Regular save just in case (e.g. initial set)
             self.save_state()
        
        # 保存日报到文件
        os.makedirs('reports', exist_ok=True)
        with open(f'reports/{datetime.now().strftime("%Y-%m-%d")}.txt', 'w') as f:
            f.write(report_text)
            
        logger.info("日报已保存至 reports/ 目录并发送至 Telegram")
        
        return report_text
    
    def check_system_health(self) -> bool:
        """检查系统健康状态"""
        try:
            # 检查进程是否正常运行
            import psutil
            process = psutil.Process()
            
            # 检查内存使用
            memory_pct = process.memory_percent()
            if memory_pct > 80:
                logger.warning(f"内存占用过高: {memory_pct}%")
                
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def shutdown(self):
        """优雅关闭"""
        self.running = False
        logger.info("交易控制器正在优雅关闭...")
        
    def run(self):
        """主运行循环"""
        try:
            # 检查配置
            if not self.check_api_keys_configured():
                logger.critical("API 密钥未配置。程序退出。")
                return
                
            self.load_configuration()
            
            # Setup Futures leverage if enabled
            if self.strategy.get('enable_futures', False):
                logger.info("Initializing Futures settings...")
                leverage = self.strategy.get('leverage', 1)
                margin_mode = self.strategy.get('margin_mode', 'ISOLATED')
                # Iterate monitored symbols (hardcoded for now as per run_monitoring_cycle)
                for symbol in ['BTCUSDT', 'ETHUSDT', 'BTCUSDC', 'ETHUSDC']:
                    try:
                        self.executor.set_leverage(symbol, leverage, margin_mode)
                    except Exception as e:
                        # Some pairs might not support futures or leverage
                        logger.warning(f"Failed to set leverage for {symbol}: {e}")

            self.running = True
            logger.info("交易控制器启动成功！")
            logger.info("正在监控市场并等待信号...")
            
            # 启动时先发送一次状态报告
            self.run_daily_report()
            self.last_report_time = datetime.now()
            
            # 主循环
            while self.running:
                # 运行监控周期
                data = self.run_monitoring_cycle()
                
                if data and 'prices' in data:
                    price_info = ", ".join([f"{s}: ${d['price']:.2f}" for s, d in data['prices'].items()])
                    logger.info(f"市场监控中... [{price_info}]")

                # 处理信号
                actions = self.process_signals(data)
                
                # 打印或记录 action
                for action in actions:
                    logger.info(action)
                    
                # 检查是否需要发送定时报告 (每天早上 9:00 北京时间 = UTC 1:00)
                # 使用 datetime.now() (系统时间，通常是 UTC 或本地)
                # 我们假设系统时间是 UTC，或者我们显式转换
                # 为了简单起见，我们每小时检查一次，如果当前时间是 9:00 (UTC+8) 且今天还没发过
                # 或者保持简单的间隔逻辑 (每 report_interval_hours 小时)
                
                # 实现逻辑：每天 09:00 发送
                now = datetime.now()
                # 转换为北京时间 (简单加8小时判断)
                now_beijing = now + timedelta(hours=8)
                
                if now_beijing.hour == 9 and now_beijing.minute == 0:
                     # 避免一分钟内重复发送: 检查 last_report_time 是否是今天
                     last_report_beijing = self.last_report_time + timedelta(hours=8)
                     if last_report_beijing.day != now_beijing.day:
                         logger.info(f"发送每日早报 (09:00)...")
                         self.run_daily_report()
                         self.last_report_time = now
                
                # 运行健康检查
                if not self.check_system_health():
                    logger.error("系统健康检查失败。正在重启...")
                    self.running = False
                
                # 定时检查（根据配置）
                sleep_time = self.monitor_config.get('refresh_interval_seconds', 30)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号。正在关闭...")
            self.shutdown()
        except Exception as e:
            logger.error(f"发生意外错误: {e}")
            self.running = False
            
    def manual_run(self):
        """手动运行一次（用于测试）"""
        if not self.check_api_keys_configured():
            print("❌ 请先配置 API 密钥！")
            return
            
        self.run_monitoring_cycle()
        self.run_daily_report()

def run_backtest(args):
    """运行回测模式"""
    try:
        import ccxt
        from modules.backtest import BacktestEngine
        # AnalysisModule 已经在顶部导入为 TechnicalAnalysis
        
        # 格式化 symbol，CCXT 需要 BTC/USDT 格式
        symbol = args.symbol
        if '/' not in symbol and symbol.endswith('USDT'):
            symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            
        print(f"🚀 正在启动回测: {symbol}, 周期: {args.days} 天")
        logger.info(f"Starting Backtest for {symbol} over {args.days} days...")

        # 初始化 CCXT
        # Use spot data for simplicity as it's often more accessible without API keys and close enough for backtesting
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # 初始化 AnalysisModule
        analysis = TechnicalAnalysis()
        
        # 初始化 BacktestEngine
        engine = BacktestEngine(exchange, analysis, symbol)
        
        # 加载数据
        print("📥 正在加载历史数据...")
        engine.load_data(days=args.days)
        
        # 运行回测
        print("⚙️ 正在执行策略回测...")
        engine.run()
        
        # 生成报告
        engine.generate_report()
        
    except ImportError:
        print("❌ 缺少必要的库: ccxt。请先安装: pip install ccxt")
        logger.error("Missing ccxt library for backtest.")
    except Exception as e:
        print(f"❌ 回测运行失败: {e}")
        logger.error(f"Backtest failed: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Crypto Trading Controller')
    parser.add_argument('--manual', action='store_true', help='Run single cycle')
    parser.add_argument('--mode', choices=['live', 'testnet', 'paper'], default='paper', help='Trading mode')
    
    # Backtest arguments
    parser.add_argument('--backtest', action='store_true', help='Run backtest mode')
    parser.add_argument('--days', type=int, default=30, help='Days of history for backtest (default: 30)')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Symbol to backtest (default: BTCUSDT)')
    
    # Custom config arguments
    parser.add_argument('--config', type=str, default='config/preferences.yaml', help='Path to trading preferences file')
    parser.add_argument('--env-file', type=str, default=None, help='Path to API keys env file (optional)')
    
    args = parser.parse_args()

    if args.backtest:
        run_backtest(args)
    else:
        # 创建控制器实例
        controller = TradingController(mode=args.mode, config_path=args.config, env_path=args.env_file)
        
        # 判断是否手动运行或自动循环
        if args.manual:
            print(f"正在运行单次循环 ({args.mode} 模式)...")
            controller.manual_run()
        else:
            # 默认：持续监控模式
            try:
                controller.run()
            except Exception as e:
                logger.error(f"致命错误: {e}")
                print(f"\n运行交易控制器时出错: {e}\n请检查日志并确保 API 密钥已配置。")
