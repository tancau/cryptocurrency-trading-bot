
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add module path
sys.path.insert(0, os.getcwd())
from modules.execution import OrderExecutor

def test_mock_trade():
    print("🚀 开始模拟交易测试 (Real Execution on Mock Trading Environment)...")
    
    # Init Executor in Testnet Mode
    config_path = 'config/api-keys.testnet.env'
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        return

    executor = OrderExecutor(config_path=config_path, mode='testnet')
    
    # 1. Check Initial Balance
    print("\n💰 检查初始余额...")
    balances = executor.get_account_balance()
    spot_b = balances.get('spot', {})
    usdt_bal = spot_b.get('USDT', 0.0)
    eth_bal = spot_b.get('ETH', 0.0)
    print(f"   USDT: {usdt_bal:.4f}")
    print(f"   ETH:  {eth_bal:.4f}")
    
    if usdt_bal < 20:
        logger.error("❌ USDT 余额不足 (<20)，无法进行测试交易。")
        return

    # 2. Place BUY Order (Market)
    symbol = 'ETH/USDT' # Standard format for CCXT usually, but our code handles replacement
    # Or just use ETHUSDT if our code expects that
    # Let's check execution.py: formatted_symbol = symbol.replace('USDT', '/USDT')
    # So if we pass 'ETHUSDT', it becomes 'ETH/USDT'. If we pass 'ETH/USDT', replace does nothing if 'USDT' is at end? 
    # 'ETH/USDT'.replace('USDT', '/USDT') -> 'ETH//USDT' -> This might be an issue in execution.py logic.
    # Let's use 'ETHUSDT' as input since that's what main_control uses.
    symbol_input = 'ETHUSDT'
    quantity = 0.01 # Approx $20 at $2000/ETH
    
    print(f"\n📈 执行买入测试: {quantity} ETH (市价单)...")
    success = executor.place_order(symbol_input, 'buy', quantity, price=None)
    
    if success:
        print("✅ 买入订单提交成功！")
        # Wait for execution and settlement
        time.sleep(5)
        
        # Check Balance Update
        balances_after = executor.get_account_balance()
        eth_new = balances_after.get('spot', {}).get('ETH', 0.0)
        print(f"   新 ETH 余额: {eth_new:.8f} (变化: {eth_new - eth_bal:+.8f})")
        
        if eth_new > eth_bal:
             print("🎉 买入成交确认！")
             
             # Calculate exact sell amount (use current balance)
             # Use 99.9% to avoid rounding issues if fees were just taken
             # Actually, if we want to sell ALL, we should use the exact balance.
             # But let's check if it's slightly less than 0.01
             sell_qty = eth_new
             
             # Manually truncate to 4 decimals (ETH precision on Binance is typically 4 or 5, safely use 4)
             import math
             sell_qty = math.floor(sell_qty * 10000) / 10000
             
             print(f"\n📉 执行卖出测试: {sell_qty:.4f} ETH (市价单)...")
             
             # Sell the exact amount we have
             success_sell = executor.place_order(symbol_input, 'sell', sell_qty, price=None)
        
             if success_sell:
                  print("✅ 卖出订单提交成功！")
                  time.sleep(5)
                  balances_final = executor.get_account_balance()
                  eth_final = balances_final.get('spot', {}).get('ETH', 0.0)
                  print(f"   最终 ETH 余额: {eth_final:.8f}")
                  
                  if eth_final < eth_new:
                       print("🎉 卖出成交确认！")
                  else:
                       print("⚠️ 余额未变化。")
             else:
                  print("❌ 卖出失败！")
        else:
             print("⚠️ 余额未变化，可能订单未完全成交或延迟。")

    else:
        print("❌ 买入失败！请检查日志。")

if __name__ == "__main__":
    test_mock_trade()
