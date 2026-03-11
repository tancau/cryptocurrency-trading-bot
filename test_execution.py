
import unittest
from modules.execution import OrderExecutor
import logging

# 配置日志输出以便在测试时看到结果
logging.basicConfig(level=logging.INFO)

class TestOrderExecution(unittest.TestCase):
    def setUp(self):
        # 初始化 Paper Trading 模式的执行器
        self.executor = OrderExecutor(mode='paper')
        
        # 初始余额: USDT 10000
        print("\n--- Initial Balance ---")
        self.executor._log_paper_balance()

    def test_buy_order(self):
        """测试买入操作"""
        print("\n--- Testing BUY Order ---")
        symbol = 'BTCUSDT'
        price = 50000.0
        quantity = 0.1 # Cost: 5000 USDT
        
        # 执行买入
        success = self.executor.place_order(symbol, 'buy', quantity, price)
        
        self.assertTrue(success)
        
        # 验证余额
        # USDT 应该减少 5000 -> 5000
        # BTC 应该增加 0.1 -> 0.1
        balance = self.executor.get_account_balance()
        self.assertEqual(balance['USDT'], 5000.0)
        self.assertEqual(balance['BTC'], 0.1)
        print("✅ Buy Order Executed Successfully")

    def test_sell_order(self):
        """测试卖出操作 (真实流程：先用余额买，再卖)"""
        print("\n--- Testing SELL Order (Real Flow) ---")
        
        # 1. 先买入 0.1 BTC (花费 5000)
        # 初始余额 10000
        self.executor.place_order('BTCUSDT', 'buy', 0.1, 50000.0)
        # 此时余额: USDT 5000, BTC 0.1
        
        # 2. 尝试卖出 0.1 BTC (价格涨到 60000)
        symbol = 'BTCUSDT'
        price = 60000.0 
        quantity = 0.1
        
        # 执行卖出
        success = self.executor.place_order(symbol, 'sell', quantity, price)
        
        self.assertTrue(success)
        
        # 验证余额
        # 卖出获得: 0.1 * 60000 = 6000 USDT
        # 最终 USDT: 5000 (剩余) + 6000 (卖出) = 11000
        # 最终 BTC: 0
        balance = self.executor.get_account_balance()
        self.assertEqual(balance['BTC'], 0.0)
        self.assertEqual(balance['USDT'], 11000.0)
        print("✅ Sell Order Executed Successfully (Real Flow)")
        
    def test_insufficient_funds(self):
        """测试余额不足的情况"""
        print("\n--- Testing Insufficient Funds ---")
        symbol = 'BTCUSDT'
        price = 50000.0
        quantity = 1.0 # Cost: 50000 USDT (余额只有 10000)
        
        success = self.executor.place_order(symbol, 'buy', quantity, price)
        
        self.assertFalse(success)
        print("✅ Insufficient Funds Handled Correctly")

if __name__ == '__main__':
    unittest.main()
