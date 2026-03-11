#!/usr/bin/env python3
"""
Technical Analysis Module 📈
Calculates indicators and generates trading signals.
"""

import logging
import numpy as np
from typing import List, Dict

logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """Performs technical analysis on market data."""
    
    def __init__(self):
        pass
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculates the Relative Strength Index (RSI).
        
        Args:
            prices: List of closing prices (must have at least period + 1 data points)
            period: The RSI period (default 14)
            
        Returns:
            Current RSI value (0-100), or 50.0 if insufficient data.
        """
        if len(prices) < period + 1:
            return 50.0
            
        prices = np.array(prices)
        deltas = np.diff(prices)
        
        gains = deltas.copy()
        losses = deltas.copy()
        
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate initial average gain/loss
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Smooth subsequent values (Wilder's Smoothing) if we had full history,
        # but for this simple version with snapshot data, simple avg is okay or 
        # we return the last calculated RSI.
        
        return float(rsi)

    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        计算 MACD 指标 (Moving Average Convergence Divergence).
        """
        if len(prices) < slow + signal:
            return {'macd': 0.0, 'signal': 0.0, 'hist': 0.0}
            
        prices = np.array(prices)
        
        # 计算 EMA
        def ema(data, window):
            weights = np.exp(np.linspace(-1., 0., window))
            weights /= weights.sum()
            a = np.convolve(data, weights, mode='full')[:len(data)]
            a[:window] = a[window]
            return a
            
        # 使用简单的 Pandas EMA 实现会更准确，这里手写一个简化版
        # 为了精确性，还是建议引入 pandas，但这里为了保持依赖简单，我们实现一个基本的 EMA
        def calculate_ema(data, span):
            alpha = 2 / (span + 1)
            ema_values = [data[0]]
            for price in data[1:]:
                ema_values.append(alpha * price + (1 - alpha) * ema_values[-1])
            return np.array(ema_values)

        ema_fast = calculate_ema(prices, fast)
        ema_slow = calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line[-1]),
            'signal': float(signal_line[-1]),
            'hist': float(histogram[-1])
        }

    def calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR).
        """
        if len(closes) < period + 1:
            return 0.0
            
        tr = np.zeros(len(closes))
        for i in range(1, len(closes)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
            
        # Initial ATR is simple moving average
        atr = np.mean(tr[1:period+1])
        
        # Subsequent ATR values (Smoothed)
        for i in range(period + 1, len(closes)):
            atr = (atr * (period - 1) + tr[i]) / period
            
        return float(atr)

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict:
        """
        Calculate Bollinger Bands.
        """
        if len(prices) < period:
            return {'upper': 0.0, 'middle': 0.0, 'lower': 0.0}
            
        prices_np = np.array(prices)
        
        # Simple Moving Average (Middle Band)
        sma = np.convolve(prices_np, np.ones(period)/period, mode='valid')
        
        # Standard Deviation
        # We need rolling std dev. 
        # Efficient way without pandas:
        rolling_std = []
        for i in range(period, len(prices_np) + 1):
            window = prices_np[i-period:i]
            rolling_std.append(np.std(window))
            
        rolling_std = np.array(rolling_std)
        
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        return {
            'upper': float(upper_band[-1]),
            'middle': float(sma[-1]),
            'lower': float(lower_band[-1])
        }

    def generate_signals(self, prices_dict: Dict[str, Dict], klines_data: Dict[str, List] = None) -> Dict[str, Dict]:
        """
        生成交易信号。
        如果提供了 klines_data，将使用真实技术指标。
        """
        signals = {}
        
        for symbol, data in prices_dict.items():
            result = {
                'signal': 'neutral',
                'rsi_14': 50.0,
                'macd': {}
            }
            
            # 如果有 K 线数据，进行真实分析
            if klines_data and symbol in klines_data and len(klines_data[symbol]) > 30:
                # Binance Klines: [Open time, Open, High, Low, Close, ...]
                # 我们只取收盘价 (索引 4)
                closes = [float(k[4]) for k in klines_data[symbol]]
                highs = [float(k[2]) for k in klines_data[symbol]]
                lows = [float(k[3]) for k in klines_data[symbol]]
                
                # 计算指标
                # Use numpy for calculation
                closes_np = np.array(closes)
                highs_np = np.array(highs)
                lows_np = np.array(lows)
                
                # ATR
                atr = self.calculate_atr(highs_np, lows_np, closes_np, 14)
                
                # Bollinger Bands
                bb = self.calculate_bollinger_bands(closes, 20, 2)
                
                # Trend (EMA 50 & 200)
                # Helper for EMA series
                def calculate_ema_series(data, period):
                    if len(data) < period: return np.zeros(len(data))
                    alpha = 2 / (period + 1)
                    ema = [data[0]]
                    for p in data[1:]:
                        ema.append(alpha * p + (1 - alpha) * ema[-1])
                    return np.array(ema)

                ema_50 = calculate_ema_series(closes_np, 50)[-1]
                ema_200 = calculate_ema_series(closes_np, 200)[-1]
                
                trend = "neutral"
                if closes[-1] > ema_200:
                    trend = "bullish"
                elif closes[-1] < ema_200:
                    trend = "bearish"
                
                # RSI
                deltas = np.diff(closes_np)
                gains = deltas.copy()
                losses = deltas.copy()
                gains[gains < 0] = 0
                losses[losses > 0] = 0
                losses = abs(losses)
                
                avg_gain = np.mean(gains[-14:]) # Simple MA for last 14
                avg_loss = np.mean(losses[-14:])
                
                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                # MACD (12, 26, 9)
                def calc_ema(data, span):
                    alpha = 2 / (span + 1)
                    ema = [data[0]]
                    for p in data[1:]:
                        ema.append(alpha * p + (1 - alpha) * ema[-1])
                    return np.array(ema)
                
                ema_12 = calc_ema(closes_np, 12)
                ema_26 = calc_ema(closes_np, 26)
                macd_line = ema_12[-1] - ema_26[-1]
                
                # Signal line (EMA 9 of MACD line) - simplified: we need history of macd line
                # Re-calculating full history for signal line
                macd_history = ema_12 - ema_26
                signal_line_history = calc_ema(macd_history, 9)
                signal_line = signal_line_history[-1]
                
                hist = macd_line - signal_line
                
                result['rsi_14'] = float(rsi)
                result['macd'] = {'macd': float(macd_line), 'signal': float(signal_line), 'hist': float(hist)}
                result['atr'] = atr
                result['trend'] = trend
                
                logger.info(f"📊 分析 [{symbol}]: Price=${closes[-1]:.2f} | Trend={trend.upper()} (EMA200={ema_200:.2f}) | RSI={rsi:.2f} | MACD={hist:.4f} | ATR={atr:.2f} | BB_Mid={bb['middle']:.2f}")
                
                # --- 策略逻辑 (Futures Adapted + Trend Filter + BB) ---
                
                # 1. Open Long (Buy): 
                #    - Trend is Bullish (Price > EMA 200)
                #    - RSI < 55 (Relaxed pullback)
                #    - Price < BB Middle (Pullback to mean)
                if trend == "bullish" and rsi < 55 and closes[-1] < bb['middle']:
                    result['signal'] = 'buy' # Open Long
                    result['reason'] = '多头趋势回调 (EMA200之上 + RSI<55 + <BB中轨)'
                    
                # 2. Open Short (Sell):
                #    - Trend is Bearish (Price < EMA 200)
                #    - RSI > 45 (Relaxed pullback)
                #    - Price > BB Middle (Rally to mean)
                elif trend == "bearish" and rsi > 45 and closes[-1] > bb['middle']:
                    result['signal'] = 'sell' # Open Short
                    result['reason'] = '空头趋势反弹 (EMA200之下 + RSI>45 + >BB中轨)'
                    
                # 3. Reversal / Strong Counter-Trend (Optional)
                
                elif rsi < 25 and hist > 0: # Extreme Oversold
                     result['signal'] = 'buy'
                     result['reason'] = '极度超卖反弹 (RSI<25)'
                     
                elif rsi > 75 and hist < 0: # Extreme Overbought
                     result['signal'] = 'sell'
                     result['reason'] = '极度超买回调 (RSI>75)'
                        
            else:
                # 回退到模拟逻辑 (仅供演示)
                pct_change = data.get('price_change_24h_pct', 0.0)
                rsi_value = 50.0 + (pct_change * 2.0)
                result['rsi_14'] = max(0.0, min(100.0, rsi_value))
                
                if result['rsi_14'] > 70:
                    result['signal'] = 'sell'
                elif result['rsi_14'] < 30:
                    result['signal'] = 'buy'
            
            signals[symbol] = result
                
        return signals
