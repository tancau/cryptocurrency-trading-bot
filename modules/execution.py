#!/usr/bin/env python3
"""
Order Execution Module 💸
Executes trades on the exchange using CCXT or Paper Trading.
"""

import logging
import os
import json
from typing import Optional, Dict
import ccxt

logger = logging.getLogger(__name__)

class PaperAccount:
    """Simulated trading account for Paper Trading."""
    def __init__(self, initial_balance=10000.0):
        self.balance = {'USDT': initial_balance}
        self.positions = {}  # {'BTC': 0.5, 'ETH': 2.0}
        self.history = []

    def get_balance(self, asset: str) -> float:
        return self.balance.get(asset, 0.0)

    def update_balance(self, asset: str, amount: float):
        self.balance[asset] = self.balance.get(asset, 0.0) + amount

class OrderExecutor:
    """Executes trading orders (Live, Testnet, or Paper)."""
    
    def __init__(self, config_path: Optional[str] = None, mode: str = 'paper'):
        self.mode = mode
        self.exchange = None
        self.exchange_futures = None # Add futures exchange instance
        self.paper_account = None
        
        logger.info(f"初始化订单执行器: {mode} 模式")
        
        if mode == 'paper':
            self.paper_account = PaperAccount()
            logger.info("模拟交易账户已初始化，初始资金 10,000 USDT")
        else:
            self._init_exchange(config_path)
            
    def _init_exchange(self, config_path):
        """Initialize CCXT exchange instance."""
        try:
            # Load keys from env file manually since we don't want to depend on python-dotenv global load
            # Assuming keys are already in os.environ or we parse them here.
            # For robustness, let's parse the file if provided.
            keys = {}
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            k, v = line.strip().split('=', 1)
                            keys[k] = v.strip() # Strip whitespace from values
            
            api_key = keys.get('BINANCE_API_KEY')
            secret = keys.get('BINANCE_API_SECRET')
            
            if self.mode == 'testnet':
                api_key = keys.get('BINANCE_TESTNET_API_KEY')
                secret = keys.get('BINANCE_TESTNET_API_SECRET')
            
            if not api_key or not secret:
                logger.error(f"缺失 API 密钥: {self.mode} 模式")
                return

            # Spot Exchange Init
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'fetchCurrencies': False,  # Disable fetchCurrencies to avoid SAPI calls
                    'fetchMarkets': ['spot'], # Explicitly only fetch spot markets
                    'warnOnFetchOpenOrdersWithoutSymbol': False,
                    'createMarketBuyOrderRequiresPrice': False,
                    # Disable Margin/Futures fetching which might trigger SAPI
                    'fetchMarginMode': False, 
                    'fetchFutureMarkets': False,
                } 
            })
            
            if self.mode == 'testnet':
                # 配置 Testnet/Mock URL
                # 优先使用配置文件中的 TESTNET_API_URL，否则默认使用 testnet.binance.vision
                testnet_url = keys.get('TESTNET_API_URL', 'https://testnet.binance.vision/api')
                
                # Ensure we have the correct version path for ccxt (it expects /v3 usually)
                if 'demo-api' in testnet_url:
                    # Demo Mode
                    # Ensure it doesn't have /v3 yet because we might need to be careful
                    ccxt_url = testnet_url
                    if not ccxt_url.endswith('/v3'):
                         ccxt_url = f"{ccxt_url}/v3"
                elif not testnet_url.endswith('/v3'):
                    ccxt_url = f"{testnet_url}/v3"
                else:
                    ccxt_url = testnet_url
                
                self.exchange.urls['api'] = {
                    'public': ccxt_url,
                    'private': ccxt_url,
                    # 添加 SAPI URL 以防止 "No URL" 错误，即使可能不工作
                    # 如果 testnet_url 是 demo-api，我们尝试使用同源的 sapi 路径
                    'sapi': testnet_url.replace('/api', '/sapi/v1'), # Assuming /api is the base
                    'sapiV1': testnet_url.replace('/api', '/sapi/v1'),
                }
                # 注意: sandbox_mode=True 在 ccxt 中通常会将 URL 切换到 testnet.binance.vision
                # 如果我们要连接 demo-api，可能需要避免 set_sandbox_mode 或者在之后覆盖
                # 这里我们显式覆盖 urls，并且如果 URL 不是 testnet.binance.vision，就不设置 sandbox_mode
                # 或者只设置 sandbox_mode=True (这通常会覆盖 urls)，然后再覆盖回来
                
                if 'testnet.binance.vision' in testnet_url:
                     self.exchange.set_sandbox_mode(True)
                else:
                     # 对于 Mock Trading (demo-api)，我们手动设置 URL
                     logger.info(f"使用自定义 Testnet/Mock URL: {testnet_url}")
                     # 确保 ccxt 不会覆盖它
                     pass

                logger.info(f"已连接 Binance Testnet/Mock ({testnet_url})")
                
                # Futures Exchange Init (Testnet Only for now)
                # Initialize separate instance for Futures Testnet (standard testnet url)
                try:
                    self.exchange_futures = ccxt.binance({
                        'apiKey': api_key,
                        'secret': secret,
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'future',
                            'fetchCurrencies': False,
                            # Use 'linear' for USDT-M Futures in recent CCXT versions, or just defaultType handles it.
                            # 'future' type string might be deprecated or incorrect for fetchMarkets option.
                            # Let's try omitting fetchMarkets option and rely on defaultType='future' + blocking SAPI via URL if needed.
                            # Or better, use ['linear'] which corresponds to USDT-M.
                            'fetchMarkets': ['linear'], 
                        }
                    })
                    # Manually override URLs to point to Futures Testnet (bypassing sandbox check)
                    # We use standard Futures Testnet URL: https://testnet.binancefuture.com
                    # Note: Mock Trading (demo-api) doesn't support fapi, so user must be on standard Testnet for Futures.
                    # UNLESS user provided TESTNET_FUTURES_API_URL
                    futures_testnet_url = keys.get('TESTNET_FUTURES_API_URL', 'https://testnet.binancefuture.com')
                    
                    if 'testnet.binancefuture.com' in futures_testnet_url:
                         # Use base url without /fapi/v1 suffix for constructing
                         pass
                    
                    # For demo-fapi.binance.com, it is usually /fapi/v1
                    # But keys might provide the base like https://demo-fapi.binance.com/fapi
                    
                    self.exchange_futures.urls['api'] = {
                        'public': futures_testnet_url + '/v1',
                        'private': futures_testnet_url + '/v1',
                        'fapiPublic': futures_testnet_url + '/v1',
                        'fapiPrivate': futures_testnet_url + '/v1',
                        # Add dummy sapi URLs to satisfy CCXT internal checks in sandbox mode
                        'sapi': futures_testnet_url + '/v1',
                        'sapiV1': futures_testnet_url + '/v1',
                        # Add V2/V3 endpoints to satisfy stricter CCXT checks
                        'fapiPrivateV2': futures_testnet_url + '/v2',
                        'fapiPrivateV3': futures_testnet_url + '/v3', # Assuming v3 follows pattern
                    }
                    logger.info(f"已初始化 Futures Testnet 连接 ({futures_testnet_url})")
                except Exception as e:
                    logger.warning(f"无法初始化 Futures Testnet: {e}")
                    
            else:
                logger.info("已连接 Binance 实盘交易")
                
        except Exception as e:
            logger.error(f"初始化交易所失败: {e}")

    def _parse_symbol(self, symbol: str) -> tuple:
        """Helper to parse symbol into base and quote assets."""
        if '/' in symbol:
            return symbol.split('/')
        
        # Common quote assets in order of length/likelihood
        for quote in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI', 'BTC', 'ETH', 'BNB']:
            if symbol.endswith(quote):
                return symbol[:-len(quote)], quote
        
        # Fallback (might be wrong for some pairs)
        return symbol.replace('USDT', ''), 'USDT'

    def get_account_balance(self) -> Dict[str, Dict]:
        """获取账户余额 (Spot & Futures) & Positions"""
        if self.mode == 'paper':
            return {'spot': self.paper_account.balance, 'futures': {}, 'positions': []}
            
        balances = {'spot': {}, 'futures': {}, 'positions': []}
        
                # 1. Fetch Spot Balance
        if self.exchange:
            try:
                # Try fetch_balance first
                balance = self.exchange.fetch_balance()
                balances['spot'] = {k: v for k, v in balance['total'].items() if v > 0}
                
            except Exception as e:
                # Only log warning if we don't have futures exchange (meaning we rely on Spot)
                # Or just debug log
                if not self.exchange_futures:
                    logger.warning(f"Fetch Spot Balance Error: {e}")
                else:
                    logger.debug(f"Fetch Spot Balance Error (ignoring as Futures active): {e}")

                # Try direct API call to /api/v3/account as fallback
                try:
                     if self.exchange.id == 'binance':
                         # If fetch_balance failed, we try private_get_account which hits /api/v3/account
                         # This endpoint returns ALL balances (free + locked)
                         account_info = self.exchange.private_get_account()
                         if 'balances' in account_info:
                             for b in account_info['balances']:
                                 total = float(b['free']) + float(b['locked'])
                                 if total > 0:
                                     balances['spot'][b['asset']] = total
                except Exception as e2:
                     if not self.exchange_futures:
                         logger.error(f"Fallback Spot Balance Error: {e2}")

        # 2. Fetch Futures Balance & Positions
        if self.exchange_futures:
            try:
                balance_fut = self.exchange_futures.fetch_balance()
                # Wallet Balance
                balances['futures'] = {k: v for k, v in balance_fut['total'].items() if v > 0}
                
                # Fetch Positions
                try:
                    positions = self.exchange_futures.fetch_positions()
                    for pos in positions:
                        # Only keep open positions
                        if float(pos.get('contracts', 0)) > 0:
                            # Parse symbol
                            symbol = pos['symbol']
                            base_asset, quote_asset = self._parse_symbol(symbol)
                            
                            # Add to positions list
                            position_info = {
                                'symbol': symbol,
                                'side': pos['side'],
                                'amount': float(pos['contracts']),
                                'entryPrice': float(pos['entryPrice']),
                                'unrealizedProfit': float(pos['unrealizedPnl'] or 0),
                                'leverage': int(pos.get('leverage', 1)),
                                'marginType': pos.get('marginType', 'cross'),
                                'notional': float(pos['notional'])
                            }
                            balances['positions'].append(position_info)

                            # Update futures balance for tracking total exposure if needed
                            # (Optional: some strategies rely on seeing the asset in 'futures' dict)
                            current_amt = balances['futures'].get(base_asset, 0.0)
                            balances['futures'][base_asset] = current_amt + float(pos['contracts'])

                except Exception as e_pos:
                    logger.warning(f"获取 Futures 持仓失败: {e_pos}")
                    # Fallback: check if positions are in balance info (less detailed)
                    if 'info' in balance_fut and 'positions' in balance_fut['info']:
                        for pos in balance_fut['info']['positions']:
                            amt = float(pos.get('positionAmt', 0))
                            if amt != 0:
                                sym = pos.get('symbol', '')
                                entry_price = float(pos.get('entryPrice', 0))
                                unrealized_pnl = float(pos.get('unrealizedProfit', 0))
                                leverage = int(pos.get('leverage', 1))
                                
                                position_info = {
                                    'symbol': sym,
                                    'side': 'long' if amt > 0 else 'short',
                                    'amount': abs(amt),
                                    'entryPrice': entry_price,
                                    'unrealizedProfit': unrealized_pnl,
                                    'leverage': leverage
                                }
                                balances['positions'].append(position_info)
                                
                                # Binace symbol format: BTCUSDT
                                base_sym, quote_sym = self._parse_symbol(sym)
                                if quote_sym in ['USDT', 'USDC', 'BUSD']:
                                    current_amt = balances['futures'].get(base_sym, 0.0)
                                    balances['futures'][base_sym] = current_amt + abs(amt)

            except Exception as e:
                logger.error(f"获取 Futures 余额失败: {e}")
        
        return balances

    def get_total_balance_value(self, current_prices: Dict[str, Dict]) -> float:
        """计算账户总价值 (USDT)"""
        balances = self.get_account_balance()
        total_value = 0.0
        
        # Spot
        for asset, amount in balances.get('spot', {}).items():
            if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI']:
                total_value += amount
            else:
                symbol = f"{asset}USDT"
                if symbol in current_prices:
                    total_value += amount * current_prices[symbol]['price']
                else:
                    pass
        
        # Futures
        for asset, amount in balances.get('futures', {}).items():
             if asset in ['USDT', 'USDC', 'BUSD']:
                total_value += amount
             # For non-stablecoin assets in futures (e.g. coin-m), we might need price conversion too
             # Assuming mainly USDT-M for now which holds USDT/USDC
                
        return total_value

    def place_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> bool:
        """
        Places an order.
        
        Args:
            symbol: Trading pair (e.g. 'BTC/USDT')
            side: 'buy' or 'sell'
            quantity: Amount to trade
            price: Limit price (None for market order). For Paper trading, required or fetched from market?
                   In this simple version, if price is None, Paper mode needs current price.
        """
        order_type = "LIMIT" if price else "MARKET"
        
        if self.mode == 'paper':
            return self._execute_paper_trade(symbol, side, quantity, price, order_type)
        elif self.exchange:
            return self._execute_exchange_trade(symbol, side, quantity, price, order_type)
        else:
            logger.error("Exchange not initialized!")
            return False

    def _execute_paper_trade(self, symbol: str, side: str, quantity: float, price: float, order_type: str) -> bool:
        """Simulate trade execution."""
        # For simplicity in Paper mode, if price is None (Market), we need a reference price.
        # Since Executor doesn't have the Monitor, we rely on the caller passing a price 
        # OR we assume price is provided for Limit, and for Market we mock it (risky).
        # Better: main_control should pass the current price for Market orders too in Paper mode.
        
        if not price:
            logger.warning("Paper Trading: Market orders require a price estimate (mocking execution price)")
            return False

        base, quote = self._parse_symbol(symbol)
        cost = quantity * price
        
        if side == 'buy':
            if self.paper_account.get_balance(quote) >= cost:
                self.paper_account.update_balance(quote, -cost)
                self.paper_account.update_balance(base, quantity)
                logger.info(f"� PAPER BUY: {quantity} {symbol} @ ${price} (Cost: ${cost:.2f})")
                self._log_paper_balance()
                return True
            else:
                logger.warning(f"Paper Trading: Insufficient funds for BUY (Need ${cost:.2f})")
                return False
        elif side == 'sell':
            if self.paper_account.get_balance(base) >= quantity:
                self.paper_account.update_balance(base, -quantity)
                self.paper_account.update_balance(quote, cost)
                logger.info(f"📝 PAPER SELL: {quantity} {symbol} @ ${price} (Gain: ${cost:.2f})")
                self._log_paper_balance()
                return True
            else:
                logger.warning(f"Paper Trading: Insufficient asset for SELL (Need {quantity} {base})")
                return False
                
        return False

    def _log_paper_balance(self):
        b = self.paper_account.balance
        logger.info(f"💰 Paper Balance: {json.dumps(b)}")

    def _execute_exchange_trade(self, symbol: str, side: str, quantity: float, price: float, order_type: str) -> bool:
        try:
            # CCXT expects symbol like 'BTC/USDT'
            if '/' not in symbol:
                base, quote = self._parse_symbol(symbol)
                formatted_symbol = f"{base}/{quote}"
            else:
                formatted_symbol = symbol
            
            # Ensure markets are loaded (using public API)
            if not self.exchange.markets:
                try:
                    self.exchange.load_markets()
                except Exception as e:
                    # In Mock/Demo mode, SAPI might be restricted or fail with 404/403
                    # This is often expected, so we just log warning and proceed with manual handling
                    logger.warning(f"load_markets failed (expected in Mock if SAPI used): {e}")

            params = {}
            # Market order
            # In some cases, create_order might try to fetch precision/limits which might fail if load_markets failed.
            # If standard create_order fails with 404 SAPI, we try direct API call.
            try:
                # If markets not loaded, create_order might fail early. 
                # We can try catch-all or check if markets loaded.
                
                if order_type == 'LIMIT':
                    order = self.exchange.create_order(formatted_symbol, 'limit', side, quantity, price, params)
                else:
                    order = self.exchange.create_order(formatted_symbol, 'market', side, quantity, None, params)
            except Exception as e_create:
                 # Catch 404 SAPI error or other SAPI related errors
                 err_str = str(e_create)
                 # Also catch if it complains about market not found (due to load_markets fail)
                 if ('404' in err_str and 'sapi' in err_str) or ('SAPI' in err_str) or ('symbol' in err_str and 'not found' in err_str):
                     logger.warning(f"create_order failed ({e_create}), trying direct private_post_order...")
                     # Manual construction for Binance Spot
                     # POST /api/v3/order
                     # symbol must be raw (e.g. ETHUSDT)
                     raw_symbol = symbol.replace('/', '')
                     
                     request_params = {
                         'symbol': raw_symbol,
                         'side': side.upper(),
                         'type': order_type.upper(),
                         # Use precision if markets loaded, else raw quantity (ensure string)
                         'quantity': self.exchange.amount_to_precision(formatted_symbol, quantity) if (self.exchange.markets and formatted_symbol in self.exchange.markets) else str(quantity),
                     }
                     if price:
                         request_params['price'] = str(price)
                         request_params['timeInForce'] = 'GTC'
                     
                     # private_post_order returns the raw response dict
                     order = self.exchange.private_post_order(request_params)
                     # Standardize order ID for logging
                     if 'orderId' in order:
                         order['id'] = str(order['orderId'])
                 else:
                     raise e_create
            
            logger.info(f"✅ Order Placed: {order.get('id', 'Unknown')} ({side} {quantity} {formatted_symbol})")
            return True
        except Exception as e:
            logger.error(f"❌ Order Failed: {e}")
            return False

    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = 'ISOLATED'):
        """
        Set leverage and margin mode for a symbol on Futures.
        """
        if not self.exchange_futures:
            logger.warning("Futures exchange not initialized.")
            return

        try:
            # 1. Set Leverage
            # binance expects symbol without slash for some endpoints, but ccxt usually handles it.
            # safe to use formatted symbol or market id.
            # exchange.set_leverage usually works for unified/swap.
            # For binance futures specifically:
            self.exchange_futures.set_leverage(leverage, symbol)
            logger.info(f"✅ Leverage set to {leverage}x for {symbol}")

            # 2. Set Margin Mode (ISOLATED / CROSSED)
            # marginType: 'ISOLATED' or 'CROSSED'
            try:
                self.exchange_futures.set_margin_mode(margin_mode, symbol)
                logger.info(f"✅ Margin mode set to {margin_mode} for {symbol}")
            except Exception as e:
                # Often fails if no change or positions exist
                logger.warning(f"⚠️ Could not set margin mode (might be already set): {e}")

        except Exception as e:
            logger.error(f"❌ Failed to set leverage/margin for {symbol}: {e}")

    def place_futures_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None, params: Dict = {}) -> bool:
        """
        Place a Futures order.
        """
        if not self.exchange_futures:
            logger.error("Futures exchange not initialized!")
            return False

        try:
            # Ensure symbol format (e.g. BTC/USDT:USDT)
            # If input is BTC/USDT, CCXT might need adjustment depending on market loading.
            # Assuming standard CCXT symbol format.
            
            type_ = 'limit' if price else 'market'
            
            # Execute
            order = self.exchange_futures.create_order(
                symbol=symbol,
                type=type_,
                side=side,
                amount=quantity,
                price=price,
                params=params
            )
            
            logger.info(f"✅ Futures Order Placed: {order.get('id')} | {side} {quantity} {symbol}")
            return True

        except Exception as e:
            logger.error(f"❌ Futures Order Failed: {e}")
            return False
