import logging
import time
from typing import List, Dict, Any
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Backtest Engine for simulating trading strategies.
    """

    def __init__(self, exchange, analysis_module, symbol: str, initial_balance: float = 10000.0):
        """
        Initialize the BacktestEngine.

        Args:
            exchange: CCXT exchange instance (or compatible object with fetch_ohlcv).
            analysis_module: Analysis module instance with generate_signals method.
            symbol: Trading pair symbol (e.g., 'BTC/USDT').
            initial_balance: Initial starting capital (default 10000.0).
        """
        self.exchange = exchange
        self.analysis = analysis_module
        self.symbol = symbol
        self.initial_balance = initial_balance
        
        # Portfolio State
        self.balance = initial_balance
        self.position = 0.0  # Current asset holding amount
        self.entry_price = 0.0
        
        # History
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.data: List[List[float]] = [] # OHLCV data
        
    def load_data(self, days: int = 30):
        """
        Fetch historical data from exchange.
        
        Args:
            days: Number of days of history to backtest (excluding warmup).
        """
        logger.info(f"Loading data for backtest: {days} days (+ warmup)...")
        
        timeframe = '1h' # Use 1h to match live trading
        
        # Calculate start time (ms)
        now = int(time.time() * 1000)
        
        # We need warmup data for indicators (e.g. 200 EMA needs 200 candles)
        # 200 candles * 1h = 200 hours ~= 8.5 days
        warmup_candles = 200
        warmup_ms = warmup_candles * 60 * 60 * 1000
        
        # Total duration = Requested Days + Warmup
        target_duration_ms = days * 24 * 60 * 60 * 1000
        since = now - target_duration_ms - warmup_ms
        
        all_ohlcv = []
        limit = 1000  # Default CCXT limit
        
        try:
            while True:
                # Fetch data
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, since=since, limit=limit)
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                
                # Update 'since' to the timestamp of the last candle + 1 timeframe duration
                # 1h = 3600 * 1000 ms
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + (3600 * 1000)
                
                # If we fetched fewer than limit, we've likely reached the end
                if len(ohlcv) < limit:
                    break
                    
                # Safety break if we have gone past current time
                if last_timestamp >= now:
                    break
            
            # Sort and deduplicate just in case
            all_ohlcv.sort(key=lambda x: x[0])
            self.data = all_ohlcv
            logger.info(f"Successfully loaded {len(self.data)} candles (Warmup + Test Data).")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def run(self):
        """
        Run the backtest simulation.
        """
        if not self.data:
            logger.warning("No data loaded. Call load_data() first.")
            return

        logger.info("Starting backtest simulation...")
        
        # Warmup period for indicators (e.g. EMA200 needs 200 candles)
        # We start trading only after we have enough data
        warmup_period = 200
        if len(self.data) < warmup_period:
            logger.warning(f"Data length ({len(self.data)}) is less than warmup period ({warmup_period}). Results may be inaccurate.")
            warmup_period = 0 # Try anyway

        for i in range(warmup_period, len(self.data)):
            # 1. Prepare Data Slice
            # We simulate that we are at time 'i'. We know history up to 'i'.
            # current_candle is the one that just closed.
            current_candle = self.data[i]
            timestamp = current_candle[0]
            close_price = float(current_candle[4])
            
            # History slice for analysis (0 to i)
            history_slice = self.data[:i+1]
            
            # 2. Generate Signals
            # Analysis module expects specific format
            prices_dict = {self.symbol: {'price': close_price}}
            klines_data = {self.symbol: history_slice}
            
            signals = self.analysis.generate_signals(prices_dict, klines_data)
            signal_data = signals.get(self.symbol, {})
            signal = signal_data.get('signal', 'neutral')
            reason = signal_data.get('reason', '')
            
            # Check for Stop Loss / Take Profit if position is open
            if abs(self.position) > 0:
                # Long Position
                if self.position > 0:
                    pnl_pct = (close_price - self.entry_price) / self.entry_price * 100
                    if pnl_pct <= -2.0:
                        self._execute_trade('sell', close_price, timestamp, "Stop Loss Triggered (-2%)")
                    elif pnl_pct >= 3.0:
                        self._execute_trade('sell', close_price, timestamp, "Take Profit Triggered (+3%)")
                
                # Short Position
                elif self.position < 0:
                    # Short PnL = (Entry - Current) / Entry * 100
                    pnl_pct = (self.entry_price - close_price) / self.entry_price * 100
                    if pnl_pct <= -2.0: # Price went UP 2%
                        self._execute_trade('buy', close_price, timestamp, "Stop Loss Triggered (-2%)")
                    elif pnl_pct >= 3.0: # Price went DOWN 3%
                        self._execute_trade('buy', close_price, timestamp, "Take Profit Triggered (+3%)")
            
            # 3. Execute Trades
            # We execute at the Close price of the current candle (simplification)
            self._execute_trade(signal, close_price, timestamp, reason)
            
            # 4. Update Portfolio Value (Equity)
            current_equity = self.balance + (self.position * close_price)
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'price': close_price
            })

    def _execute_trade(self, signal: str, price: float, timestamp: int, reason: str):
        """Execute logic for simulated trades (Spot Margin Mode)."""
        
        # BUY SIGNAL
        if signal == 'buy':
            # 1. Close Short if exists (Buy to Cover)
            if self.position < 0:
                amount = abs(self.position)
                cost = amount * price
                
                # PnL for record keeping
                pnl = (self.entry_price - price) * amount
                pnl_pct = (self.entry_price - price) / self.entry_price * 100
                
                self.balance -= cost # Pay cash to buy back
                self.position = 0.0
                self._record_trade('buy_cover', price, amount, timestamp, reason, pnl, pnl_pct)
                logger.info(f"🟢 BACKTEST BUY COVER: {amount:.4f} @ ${price:.2f} (PnL: {pnl_pct:.2f}%)")
            
            # 2. Open Long if flat
            if self.position == 0:
                amount = self.balance / price
                cost = amount * price
                
                self.balance -= cost
                self.position = amount
                self.entry_price = price
                self._record_trade('buy_open', price, amount, timestamp, reason)
                logger.info(f"🟢 BACKTEST BUY: {amount:.4f} @ ${price:.2f} ({reason})")
                
        # SELL SIGNAL
        elif signal == 'sell':
            # 1. Close Long if exists (Sell to Close)
            if self.position > 0:
                amount = self.position
                revenue = amount * price
                
                # PnL for record keeping
                pnl = (price - self.entry_price) * amount
                pnl_pct = (price - self.entry_price) / self.entry_price * 100
                
                self.balance += revenue # Receive cash
                self.position = 0.0
                self._record_trade('sell_close', price, amount, timestamp, reason, pnl, pnl_pct)
                logger.info(f"🔴 BACKTEST SELL CLOSE: {amount:.4f} @ ${price:.2f} (PnL: {pnl_pct:.2f}%)")
                
            # 2. Open Short if flat (Short Sell)
            if self.position == 0:
                amount = self.balance / price
                proceeds = amount * price
                
                self.balance += proceeds # Receive cash from short sale
                self.position = -amount # Negative position
                self.entry_price = price
                self._record_trade('sell_open', price, amount, timestamp, reason)
                logger.info(f"📉 BACKTEST SHORT: {amount:.4f} @ ${price:.2f} ({reason})")

    def _record_trade(self, side: str, price: float, amount: float, timestamp: int, reason: str, pnl: float = 0.0, pnl_pct: float = 0.0):
        dt = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        # Only count PnL for closing trades
        if 'close' in side or 'cover' in side:
            self.balance_history = getattr(self, 'balance_history', [])
            self.balance_history.append(self.balance)
            
        self.trades.append({
            'datetime': dt,
            'side': side,
            'price': price,
            'amount': amount,
            'reason': reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'balance': self.balance
        })

    def generate_report(self):
        if not self.equity_curve:
            print("暂无回测数据。")
            return

        final_equity = self.equity_curve[-1]['equity']
        total_return = (final_equity - self.initial_balance) / self.initial_balance * 100
        
        # Max Drawdown
        equity_values = [x['equity'] for x in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0.0
        for val in equity_values:
            if val > peak: peak = val
            dd = (peak - val) / peak
            if dd > max_drawdown: max_drawdown = dd
        
        # Trade Stats
        closed_trades = [t for t in self.trades if 'close' in t['side'] or 'cover' in t['side']]
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        print("\n" + "="*30)
        print("   回测性能报告 (Backtest Report)   ")
        print("="*30)
        print(f"交易对 (Symbol):    {self.symbol}")
        print(f"回测周期 (Period):  {len(self.data)} 小时")
        print(f"初始资金 (Initial): ${self.initial_balance:,.2f}")
        print(f"最终权益 (Final):   ${final_equity:,.2f}")
        print("-" * 30)
        print(f"总收益率 (Return):  {total_return:+.2f}%")
        print(f"最大回撤 (Drawdown):{max_drawdown*100:.2f}%")
        print(f"胜率 (Win Rate):    {win_rate:.2f}% ({len(winning_trades)}/{len(closed_trades)})")
        print(f"盈亏比 (PF):        {profit_factor:.2f}")
        print(f"总交易次数 (Trades):{len(closed_trades)}")
        print(f"  - 盈利 (Win):     {len(winning_trades)}")
        print(f"  - 亏损 (Loss):    {len(losing_trades)}")
        print("="*30 + "\n")
