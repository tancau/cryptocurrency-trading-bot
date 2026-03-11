
import os
import ccxt
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
config_path = 'config/api-keys.testnet.env'
keys = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                keys[k] = v.strip()

api_key = keys.get('BINANCE_TESTNET_API_KEY')
secret = keys.get('BINANCE_TESTNET_API_SECRET')

def test_futures_connection():
    print("🚀 Testing Binance Futures Connection with provided keys...")
    
    # 1. Test Standard Futures Testnet (Manual URL)
    print("\n--- Trying Standard Futures Testnet (https://testnet.binancefuture.com) ---")
    try:
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'fetchCurrencies': False,
            }
        })
        # Manually set URLs without set_sandbox_mode
        testnet_url = 'https://testnet.binancefuture.com'
        exchange.urls['api'] = {
            'public': testnet_url + '/fapi/v1',
            'private': testnet_url + '/fapi/v1',
            'fapiPublic': testnet_url + '/fapi/v1',
            'fapiPrivate': testnet_url + '/fapi/v1',
        }
        
        # Try to fetch balance
        balance = exchange.fetch_balance()
        print("✅ Success! Found Futures Balance:")
        # Print non-zero balances
        found = False
        if 'total' in balance:
            for asset, data in balance['total'].items():
                if data > 0:
                    print(f"   {asset}: {data}")
                    found = True
        if not found:
            print("   (Balance is empty)")
                
    except Exception as e:
        print(f"❌ Failed Standard Futures Testnet: {e}")

    # 2. Test Mock Trading Futures (demo-api.binance.com)
    print("\n--- Trying Mock Trading Futures (https://demo-api.binance.com/fapi) ---")
    try:
        exchange_mock = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'fetchCurrencies': False,
            }
        })
        # Manually override URLs to point to demo-api
        mock_url = 'https://demo-api.binance.com/fapi/v1' 
        exchange_mock.urls['api'] = {
            'public': mock_url,
            'private': mock_url,
            'fapiPublic': mock_url,
            'fapiPrivate': mock_url,
        }
        
        # Try fetch balance
        balance = exchange_mock.fetch_balance()
        print("✅ Success! Found Mock Futures Balance:")
        found = False
        if 'total' in balance:
            for asset, data in balance['total'].items():
                 if data > 0:
                     print(f"   {asset}: {data}")
                     found = True
        if not found:
            print("   (Balance is empty)")
                 
    except Exception as e:
        print(f"❌ Failed Mock Futures: {e}")

if __name__ == "__main__":
    test_futures_connection()
