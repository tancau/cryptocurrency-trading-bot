
import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# Load config
config_path = 'config/api-keys.testnet.env'
keys = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                keys[k] = v.strip()

API_KEY = keys.get('BINANCE_TESTNET_API_KEY')
API_SECRET = keys.get('BINANCE_TESTNET_API_SECRET')

BASE_URL = 'https://testnet.binancefuture.com'

def get_futures_account():
    print(f"📡 Requesting Futures Account Info from {BASE_URL}...")
    endpoint = '/fapi/v2/account'
    
    timestamp = int(time.time() * 1000)
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    query_string = urlencode(params)
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Connection Successful!")
            
            # Print Assets with Balance
            print("\n💰 Futures Wallet Balance:")
            assets = data.get('assets', [])
            found = False
            for asset in assets:
                balance = float(asset.get('walletBalance', 0))
                unrealized_pnl = float(asset.get('unrealizedProfit', 0))
                if balance > 0:
                    print(f"   - {asset['asset']}: {balance:.4f} (PnL: {unrealized_pnl:.4f})")
                    found = True
            if not found:
                print("   (No assets found)")
                
            # Print Positions
            print("\n📈 Open Positions:")
            positions = data.get('positions', [])
            found_pos = False
            for pos in positions:
                amt = float(pos.get('positionAmt', 0))
                if amt != 0:
                    print(f"   - {pos['symbol']}: {amt} (Entry: {pos['entryPrice']})")
                    found_pos = True
            if not found_pos:
                print("   (No open positions)")
                
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    get_futures_account()
