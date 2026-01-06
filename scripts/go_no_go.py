import os
import sys
import ccxt
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_keys():
    """Check if API keys are present"""
    key = os.environ.get('BINANCE_API_KEY')
    secret = os.environ.get('BINANCE_SECRET_KEY')
    if key and secret:
        print("✅ API Keys Found")
        return True, key, secret
    else:
        print("❌ API Keys MISSING in Environment!")
        return False, None, None

def check_connectivity(key, secret):
    """Check Exchange Connectivity"""
    try:
        exchange = ccxt.binance({'apiKey': key, 'secret': secret})
        exchange.load_markets()
        print("✅ Binance Connection Successful")
        return True, exchange
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False, None

def check_balance(exchange, required=250):
    """Check USDT Balance"""
    try:
        bal = exchange.fetch_balance()
        usdt = bal['total'].get('USDT', 0)
        print(f"💰 Wallet Balance: ${usdt:.2f}")
        
        if usdt < required:
            print(f"⚠️  Balance Low! Recommended: ${required}")
            return False
        return True
    except Exception as e:
        print(f"❌ Failed to fetch balance: {e}")
        return False

def validate_config():
    """Validate internal config logic"""
    # Grid Config Logic
    budget = 250
    trade_size = 25
    max_trades = budget / trade_size
    
    print(f"📊 Strategy Config Check:")
    print(f"   - Budget: ${budget}")
    print(f"   - Trade Size: ${trade_size}")
    print(f"   - Max Active Grids: {int(max_trades)}")
    
    if max_trades < 5:
        print("❌ CRITICAL: Budget too small for strategy! Need at least 5-10 trades buffer.")
        return False
        
    print("✅ Configuration Logic Check Passed")
    return True

def main():
    print("🚀 STARTING GO/NO-GO PRE-FLIGHT CHECK...")
    print("========================================")
    
    all_passed = True
    
    # 1. Config
    if not validate_config(): all_passed = False
    
    # 2. Keys
    has_keys, k, s = check_keys()
    if not has_keys: all_passed = False
    
    # 3. Connection (Only if keys exist)
    if has_keys:
        connected, ex = check_connectivity(k, s)
        if not connected: 
            all_passed = False
        else:
            # 4. Balance
            # We warn but don't fail hard if balance is low (user might deposit later)
            check_balance(ex) 
            
    print("========================================")
    if all_passed:
        print("✅ GO! System is Ready for Launch.")
        sys.exit(0)
    else:
        print("🛑 NO-GO! Fix errors before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
