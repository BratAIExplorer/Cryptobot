#!/usr/bin/env python3
"""
Phase 1: Binance PAPER API Verification
Uses paper/testnet keys for safe testing
"""
import os
import sys
import ccxt
from datetime import datetime

print("=" * 80)
print("🔍 BINANCE PAPER API VERIFICATION")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load paper API credentials
print("Step 1: Loading PAPER API credentials...")
print("-" * 80)

env_file = '.env.binance.paper'
if not os.path.exists(env_file):
    print(f"❌ {env_file} not found!")
    print("   Run: nano .env.binance.paper")
    print("   Add your Binance PAPER/TESTNET API keys")
    sys.exit(1)

env_vars = {}
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value.strip()

api_key = env_vars.get('BINANCE_API_KEY')
secret = env_vars.get('BINANCE_SECRET')

if not api_key or api_key == 'your_paper_api_key_here':
    print("❌ BINANCE_API_KEY not set")
    print("   Edit .env.binance.paper and add your PAPER API key")
    sys.exit(1)

if not secret or secret == 'your_paper_secret_here':
    print("❌ BINANCE_SECRET not set")
    sys.exit(1)

print(f"✅ Paper API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"✅ Secret: {'*' * 40}")
print()

# Initialize Binance (testnet for paper trading)
print("Step 2: Connecting to Binance Testnet...")
print("-" * 80)

try:
    # Use testnet for paper trading
    binance = ccxt.binance({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'adjustForTimeDifference': True,
        },
        # Testnet URLs for paper trading
        'urls': {
            'api': {
                'public': 'https://testnet.binance.vision/api/v3',
                'private': 'https://testnet.binance.vision/api/v3',
            }
        }
    })
    print("✅ Connected to Binance Testnet (Paper Trading)")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print()

# Test 1: Read account balance
print("Test 1: Testnet Account Balance")
print("-" * 80)

try:
    balance = binance.fetch_balance()
    usdt = balance.get('USDT', {}).get('total', 0)
    print(f"✅ Can read testnet balance")
    print(f"   USDT Balance: ${usdt:,.2f} (testnet/fake money)")

    # Show balances
    print("\n   Testnet balances:")
    for currency in ['USDT', 'BTC', 'ETH', 'BNB']:
        bal = balance.get(currency, {}).get('total', 0)
        if bal > 0:
            print(f"      {currency}: {bal:,.8f}")

    if usdt == 0:
        print("\n   ⚠️  Testnet account empty - you may need to fund it")
        print("      Visit: https://testnet.binance.vision/")
        print("      Get testnet funds to test with")

except Exception as e:
    print(f"❌ Balance check failed: {e}")
    sys.exit(1)

print()

# Test 2: Check BTC/USDT market
print("Test 2: BTC/USDT Market Access (Testnet)")
print("-" * 80)

try:
    markets = binance.load_markets(reload=True)

    if 'BTC/USDT' not in markets:
        print("❌ BTC/USDT not found on testnet")
        sys.exit(1)

    btc_market = markets['BTC/USDT']
    ticker = binance.fetch_ticker('BTC/USDT')

    print("✅ BTC/USDT accessible on testnet")
    print(f"   Testnet Price: ${ticker['last']:,.2f}")
    print(f"   Active: {btc_market.get('active', 'N/A')}")
    print(f"   Spot: {btc_market.get('spot', 'N/A')}")

    if not btc_market.get('active'):
        print("   ❌ Market INACTIVE on testnet")
        sys.exit(1)

except Exception as e:
    print(f"❌ BTC/USDT check failed: {e}")
    sys.exit(1)

print()

# Test 3: Check ETH/USDT market
print("Test 3: ETH/USDT Market Access (Testnet)")
print("-" * 80)

try:
    if 'ETH/USDT' not in markets:
        print("❌ ETH/USDT not found on testnet")
        sys.exit(1)

    eth_market = markets['ETH/USDT']
    ticker = binance.fetch_ticker('ETH/USDT')

    print("✅ ETH/USDT accessible on testnet")
    print(f"   Testnet Price: ${ticker['last']:,.2f}")
    print(f"   Active: {eth_market.get('active', 'N/A')}")

    if not eth_market.get('active'):
        print("   ❌ Market INACTIVE on testnet")
        sys.exit(1)

except Exception as e:
    print(f"❌ ETH/USDT check failed: {e}")
    sys.exit(1)

print()

# Test 4: Try testnet order
print("Test 4: Testnet Order Placement")
print("-" * 80)
print("⚠️  This will place a testnet order (fake money, safe to test)")
print()

try:
    symbol = 'BTC/USDT'
    ticker = binance.fetch_ticker(symbol)
    current_price = ticker['last']

    # Order below market
    test_price = round(current_price * 0.95, 2)
    test_amount = 0.001  # Small testnet amount

    print(f"Testnet BTC Price: ${current_price:,.2f}")
    print(f"Test Order: BUY {test_amount} BTC @ ${test_price:,.2f}")
    print(f"(Testnet money - not real!)")
    print()

    # Create testnet order
    order = binance.create_limit_buy_order(symbol, test_amount, test_price)

    print("=" * 80)
    print("🎉 TESTNET ORDER WORKS!")
    print("=" * 80)
    print(f"Order ID: {order['id']}")
    print(f"Status: {order['status']}")
    print()

    # Cancel it
    binance.cancel_order(order['id'], symbol)
    print("✅ Order canceled")
    print()

    print("=" * 80)
    print("✅ BINANCE PAPER API VERIFICATION COMPLETE!")
    print("=" * 80)
    print()
    print("Results:")
    print("  ✅ Testnet API works")
    print("  ✅ BTC/USDT ACTIVE on testnet")
    print("  ✅ ETH/USDT ACTIVE on testnet")
    print("  ✅ Can place/cancel testnet orders")
    print()
    print("🚀 READY FOR PHASE 2: Code Adaptation")
    print()
    print("=" * 80)

except ccxt.InsufficientFunds:
    print("⚠️  Insufficient testnet funds")
    print("   Visit: https://testnet.binance.vision/")
    print("   Get testnet USDT to continue testing")
    print()
    print("   (This is OK - API has permission, just needs testnet funds)")

except Exception as e:
    print(f"❌ Testnet order failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
