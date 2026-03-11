#!/usr/bin/env python3
"""
Market Monitor Module 📊
Fetches real-time market data from public APIs.
"""

import logging
import requests
import time
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MarketMonitor:
    """Monitors cryptocurrency markets using public APIs."""
    
    def __init__(self, config_path: Optional[str] = None, testnet: bool = False):
        if testnet:
            # 优先从环境变量或配置文件读取 TESTNET_API_URL
            # 默认为 Binance Spot Testnet: https://testnet.binance.vision/api
            self.binance_api_url = os.getenv('TESTNET_API_URL', "https://testnet.binance.vision/api")
            logger.info(f"市场监控模块: 使用 Binance 测试网 API ({self.binance_api_url})")
        else:
            self.binance_api_url = "https://api.binance.com/api"
            
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        self.config_path = config_path
        
    def get_market_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetches current prices for a list of symbols (e.g., ['BTCUSDT', 'ETHUSDT']).
        Returns a dictionary: {'BTCUSDT': {'price': 50000.0, 'price_change_24h_pct': 2.5}, ...}
        """
        results = {}
        
        try:
            for symbol in symbols:
                # Binance Public API
                # 注意: Testnet 的 API 路径可能不同，此处假设 v3 兼容
                url = f"{self.binance_api_url}/v3/ticker/24hr?symbol={symbol}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results[symbol] = {
                        'price': float(data['lastPrice']),
                        'price_change_24h_pct': float(data['priceChangePercent']),
                        'volume': float(data['quoteVolume'])
                    }
                else:
                    logger.warning(f"无法获取 {symbol} 价格: {response.status_code}")
                    # Basic fallback
                    results[symbol] = {'price': 0.0, 'price_change_24h_pct': 0.0, 'volume': 0.0}
                    
        except Exception as e:
            logger.error(f"获取市场价格出错: {e}")
            
        return results

    def get_historical_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[List]:
        """
        获取历史 K 线数据 (OHLCV)。
        返回: [[Open time, Open, High, Low, Close, Volume, ...], ...]
        """
        try:
            # Testnet 和 Live 的 API 路径可能略有不同，但 /v3/klines 通常通用
            url = f"{self.binance_api_url}/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"无法获取 {symbol} K线数据: {response.status_code} {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"获取 K 线数据出错: {e}")
            return []

    def get_market_summary(self) -> Dict:
        """
        Fetches global market summary (e.g., total market cap) from CoinGecko.
        Note: CoinGecko Free API has rate limits (10-30 req/min).
        """
        summary = {
            'total_market_cap': 0.0,
            'total_volume': 0.0,
            'market_cap_change_percentage_24h_usd': 0.0
        }
        
        try:
            # CoinGecko /global endpoint
            url = f"{self.coingecko_api_url}/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                # Note: CoinGecko structure is slightly different
                summary['total_market_cap'] = data.get('total_market_cap', {}).get('usd', 0.0)
                summary['total_volume'] = data.get('total_volume', {}).get('usd', 0.0)
                summary['market_cap_change_percentage_24h_usd'] = data.get('market_cap_change_percentage_24h_usd', 0.0)
            elif response.status_code == 429:
                logger.warning("CoinGecko API 速率限制 (429)。跳过市场总览更新。")
            else:
                logger.warning(f"无法获取市场总览: {response.status_code}")
                
        except Exception as e:
            logger.error(f"获取市场总览出错: {e}")
            
        return summary

    def check_alert_conditions(self, prices: Dict[str, Dict]) -> List[Dict]:
        """
        Checks if any basic alert conditions are met (e.g. big price drop).
        Returns a list of alert objects.
        """
        alerts = []
        
        for symbol, data in prices.items():
            change = data.get('price_change_24h_pct', 0)
            
            # Example alert: Drop more than 5%
            if change < -5.0:
                alerts.append({
                    'type': 'price_drop',
                    'symbol': symbol,
                    'message': f"{symbol} 24小时内下跌 {abs(change):.2f}%！"
                })
            # Example alert: Pump more than 5%
            elif change > 5.0:
                alerts.append({
                    'type': 'price_pump',
                    'symbol': symbol,
                    'message': f"{symbol} 24小时内上涨 {change:.2f}%！"
                })
                
        return alerts
