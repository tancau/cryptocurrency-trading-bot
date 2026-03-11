
import unittest
from modules.analysis import TechnicalAnalysis

class TestTechnicalAnalysis(unittest.TestCase):
    def setUp(self):
        self.ta = TechnicalAnalysis()

    def test_buy_signal(self):
        """测试买入信号：RSI < 30 且 MACD > 0"""
        # 构造一个下跌后反弹的数据序列
        # 价格持续下跌 -> RSI 低
        # 最后略微反弹 -> MACD 动能可能转正
        prices = [100.0] * 50
        for i in range(20):
            prices.append(100.0 - i * 2) # 100, 98, 96... 62
            
        # 此时 RSI 应该很低。
        # 伪造 K 线数据结构
        klines = [[0, 0, 0, 0, p, 0] for p in prices]
        
        # 为了精确触发条件，我们可以直接 mock calculate_rsi 和 calculate_macd 的返回值
        # 但为了测试真实逻辑，我们先测试 mock 逻辑
        
        # 场景 1: 完美买入
        # RSI = 25, MACD Hist = 0.5
        mock_rsi = 25.0
        mock_macd = {'macd': -10, 'signal': -10.5, 'hist': 0.5}
        
        # 我们需要一种方式来注入这些值，或者构造出能产生这些值的价格序列（较难）
        # 这里我们采用修改源码临时测试，或者直接调用内部逻辑
        
        # 让我们直接测试 generate_signals 的逻辑分支
        # 我们通过构造特殊的 klines 数据，虽然计算出的指标可能不准，
        # 但我们可以通过 Monkey Patching 来模拟指标计算结果
        
        original_rsi = self.ta.calculate_rsi
        original_macd = self.ta.calculate_macd
        
        try:
            self.ta.calculate_rsi = lambda x: 25.0
            self.ta.calculate_macd = lambda x: {'macd': -10, 'signal': -10.5, 'hist': 0.5}
            
            prices_dict = {'BTCUSDT': {'price': 100}}
            klines_data = {'BTCUSDT': [[0]*6]*100} # 长度足够即可
            
            signals = self.ta.generate_signals(prices_dict, klines_data)
            
            print(f"Buy Test Result: {signals['BTCUSDT']}")
            self.assertEqual(signals['BTCUSDT']['signal'], 'buy')
            self.assertEqual(signals['BTCUSDT']['reason'], 'RSI超卖 + MACD动能增强')
            
        finally:
            self.ta.calculate_rsi = original_rsi
            self.ta.calculate_macd = original_macd

    def test_sell_signal_rsi(self):
        """测试卖出信号：RSI > 70"""
        original_rsi = self.ta.calculate_rsi
        original_macd = self.ta.calculate_macd
        
        try:
            self.ta.calculate_rsi = lambda x: 75.0
            self.ta.calculate_macd = lambda x: {'macd': 10, 'signal': 10, 'hist': 0}
            
            prices_dict = {'ETHUSDT': {'price': 2000}}
            klines_data = {'ETHUSDT': [[0]*6]*100}
            
            signals = self.ta.generate_signals(prices_dict, klines_data)
            
            print(f"Sell RSI Test Result: {signals['ETHUSDT']}")
            self.assertEqual(signals['ETHUSDT']['signal'], 'sell')
            self.assertEqual(signals['ETHUSDT']['reason'], 'RSI超买')
            
        finally:
            self.ta.calculate_rsi = original_rsi
            self.ta.calculate_macd = original_macd
            
    def test_sell_signal_macd(self):
        """测试卖出信号：MACD 死叉"""
        original_rsi = self.ta.calculate_rsi
        original_macd = self.ta.calculate_macd
        
        try:
            self.ta.calculate_rsi = lambda x: 55.0 # 中性偏高
            self.ta.calculate_macd = lambda x: {'macd': 10, 'signal': 11, 'hist': -1} # 死叉
            
            prices_dict = {'BNBUSDT': {'price': 300}}
            klines_data = {'BNBUSDT': [[0]*6]*100}
            
            signals = self.ta.generate_signals(prices_dict, klines_data)
            
            print(f"Sell MACD Test Result: {signals['BNBUSDT']}")
            self.assertEqual(signals['BNBUSDT']['signal'], 'sell')
            self.assertEqual(signals['BNBUSDT']['reason'], 'MACD高位死叉')
            
        finally:
            self.ta.calculate_rsi = original_rsi
            self.ta.calculate_macd = original_macd

if __name__ == '__main__':
    unittest.main()
