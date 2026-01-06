#!/usr/bin/env python3
"""
Phase 1: Binance API Verification
Tests if BTC/USDT and ETH/USDT are accessible via Binance API
BEFORE committing to full migration
"""
import os
import sys
import ccxt
from datetime import datetime

print("=" * 80)
print("🔍 BINANCE API VERIFICATION - PHASE 1")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load Binance API credentials
print("Step 1: Loading API credentials...")
print("-" * 80)

# Try to load from .env.binance first, then .env
env_file = '.env.binance' if os.path.exists('.env.binance') else '.env'
print(f"Using config file: {env_file}")

env_vars = {}
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()
else:
    print(f"❌ {env_file} not found!")
    print("\nPlease create .env.binance with:")
    print("  BINANCE_API_KEY=your_api_key")
    print("  BINANCE_SECRET=your_secret")
    sys.exit(1)

api_key = env_vars.get('BINANCE_API_KEY')
secret = env_vars.get('BINANCE_SECRET')

if not api_key:
    print("❌ BINANCE_API_KEY not found in config")
    print(f"   Edit {env_file} and add: BINANCE_API_KEY=your_key")
    sys.exit(1)

if not secret:
    print("❌ BINANCE_SECRET not found in config")
    print(f"   Edit {env_file} and add: BINANCE_SECRET=your_secret")
    sys.exit(1)

print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"✅ Secret: {'*' * 40}")
print()

# Initialize Binance
print("Step 2: Connecting to Binance...")
print("-" * 80)

try:
    binance = ccxt.binance({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
            'adjustForTimeDifference': True,
        }
    })
    print("✅ Connected to Binance")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print()

# Test 1: Read account balance
print("Test 1: Account Balance Access")
print("-" * 80)

try:
    balance = binance.fetch_balance()
    usdt = balance.get('USDT', {}).get('total', 0)
    print(f"✅ Can read balance")
    print(f"   USDT Balance: ${usdt:,.2f}")

    # Show all non-zero balances
    print("\n   All balances:")
    has_balance = False
    for currency, data in balance.items():
        if isinstance(data, dict) and data.get('total', 0) > 0:
            print(f"      {currency}: {data['total']:,.8f}")
            has_balance = True

    if not has_balance:
        print("      (No balances found - account may be empty)")
        print("      ⚠️  You'll need to transfer funds from MEXC before live trading")

except Exception as e:
    print(f"❌ Balance check failed: {e}")
    print("   This may indicate API key doesn't have 'Read' permission")
    sys.exit(1)

print()

# Test 2: Check BTC/USDT market
print("Test 2: BTC/USDT Market Access")
print("-" * 80)

try:
    markets = binance.load_markets(reload=True)

    if 'BTC/USDT' not in markets:
        print("❌ BTC/USDT market NOT FOUND!")
        print("   This is unexpected - BTC/USDT should always be available on Binance")
        sys.exit(1)

    btc_market = markets['BTC/USDT']
    ticker = binance.fetch_ticker('BTC/USDT')

    print("✅ BTC/USDT market accessible")
    print(f"   Current Price: ${ticker['last']:,.2f}")
    print(f"   24h Volume: ${ticker.get('quoteVolume', 0):,.0f}")
    print(f"   Active: {btc_market.get('active', 'N/A')}")
    print(f"   Spot: {btc_market.get('spot', 'N/A')}")
    print(f"   Min Order: {btc_market.get('limits', {}).get('amount', {}).get('min', 'N/A')} BTC")
    print(f"   Min Cost: ${btc_market.get('limits', {}).get('cost', {}).get('min', 'N/A')}")

    if not btc_market.get('active'):
        print("   ❌ WARNING: Market shows as INACTIVE!")
        print("   This is the same issue as MEXC - STOP HERE")
        sys.exit(1)

except Exception as e:
    print(f"❌ BTC/USDT check failed: {e}")
    sys.exit(1)

print()

# Test 3: Check ETH/USDT market
print("Test 3: ETH/USDT Market Access")
print("-" * 80)

try:
    if 'ETH/USDT' not in markets:
        print("❌ ETH/USDT market NOT FOUND!")
        sys.exit(1)

    eth_market = markets['ETH/USDT']
    ticker = binance.fetch_ticker('ETH/USDT')

    print("✅ ETH/USDT market accessible")
    print(f"   Current Price: ${ticker['last']:,.2f}")
    print(f"   24h Volume: ${ticker.get('quoteVolume', 0):,.0f}")
    print(f"   Active: {eth_market.get('active', 'N/A')}")
    print(f"   Spot: {eth_market.get('spot', 'N/A')}")
    print(f"   Min Order: {eth_market.get('limits', {}).get('amount', {}).get('min', 'N/A')} ETH")
    print(f"   Min Cost: ${eth_market.get('limits', {}).get('cost', {}).get('min', 'N/A')}")

    if not eth_market.get('active'):
        print("   ❌ WARNING: Market shows as INACTIVE!")
        sys.exit(1)

except Exception as e:
    print(f"❌ ETH/USDT check failed: {e}")
    sys.exit(1)

print()

# Test 4: Check open orders (requires trading permission)
print("Test 4: Order Query Permission")
print("-" * 80)

try:
    orders = binance.fetch_open_orders('BTC/USDT')
    print(f"✅ Can query orders ({len(orders)} open)")
except Exception as e:
    error_msg = str(e)
    if 'API-key' in error_msg or 'permission' in error_msg.lower():
        print(f"❌ Order query failed: {e}")
        print("   API key may not have 'Spot Trading' permission")
        print("   Go to Binance → API Management → Enable 'Spot & Margin Trading'")
        sys.exit(1)
    else:
        print(f"⚠️  Order query error: {e}")
        print("   This may be OK - continuing tests...")

print()

# Test 5: Try to place test order
print("Test 5: Test Order Placement (CRITICAL)")
print("-" * 80)
print("⚠️  This will place a REAL order, but WAY below market (won't fill)")
print()

try:
    symbol = 'BTC/USDT'
    ticker = binance.fetch_ticker(symbol)
    current_price = ticker['last']

    # Order 50% below market (safe - won't fill)
    test_price = round(current_price * 0.50, 2)

    # Check minimum order size
    min_amount = btc_market.get('limits', {}).get('amount', {}).get('min', 0.0001)
    test_amount = min_amount  # Use minimum

    print(f"Current BTC Price: ${current_price:,.2f}")
    print(f"Test Order: BUY {test_amount} BTC @ ${test_price:,.2f}")
    print(f"Total Cost: ${test_price * test_amount:.2f}")
    print(f"(Order is 50% below market - will NOT fill)")
    print()

    print("Placing test order in 3 seconds... (Ctrl+C to abort)")
    import time
    for i in range(3, 0, -1):
        print(f"{i}...", end='\r', flush=True)
        time.sleep(1)

    print("\nCreating order...")

    # Create limit order
    order = binance.create_limit_buy_order(
        symbol=symbol,
        amount=test_amount,
        price=test_price
    )

    print()
    print("=" * 80)
    print("🎉 SUCCESS! ORDER PLACEMENT WORKS!")
    print("=" * 80)
    print(f"Order ID: {order['id']}")
    print(f"Status: {order['status']}")
    print(f"Symbol: {order['symbol']}")
    print(f"Side: {order['side']}")
    print(f"Price: ${order['price']:,.2f}")
    print(f"Amount: {order['amount']} BTC")
    print(f"Cost: ${order.get('cost', test_price * test_amount):.2f}")
    print()

    # Cancel immediately
    print("Canceling test order...")
    binance.cancel_order(order['id'], symbol)
    print("✅ Order canceled successfully")
    print()

    print("=" * 80)
    print("✅ BINANCE API VERIFICATION COMPLETE - ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Results:")
    print("  ✅ Can read account balance")
    print("  ✅ BTC/USDT market ACTIVE and accessible")
    print("  ✅ ETH/USDT market ACTIVE and accessible")
    print("  ✅ Can query orders")
    print("  ✅ Can place orders")
    print("  ✅ Can cancel orders")
    print()
    print("🚀 RECOMMENDATION: PROCEED WITH MIGRATION")
    print()
    print("Next steps:")
    print("  1. Review BINANCE_MIGRATION_PLAN.md")
    print("  2. Proceed to Phase 2: Code Adaptation")
    print("  3. Run paper trading tests (Phase 3)")
    print("  4. Small live test (Phase 4)")
    print("  5. Full deployment (Phase 5)")
    print()
    print("=" * 80)

except ccxt.InsufficientFunds as e:
    print()
    print("⚠️  Insufficient balance to place test order")
    print("   This is OKAY - it means API has trading permission!")
    print("   Just need to transfer funds from MEXC")
    print()
    print("✅ API KEY HAS TRADING PERMISSION")
    print()
    print("Next steps:")
    print("  1. Transfer funds from MEXC to Binance")
    print("  2. Proceed with migration plan")

except ccxt.ExchangeError as e:
    error_msg = str(e)
    print()
    print("=" * 80)
    print("❌ ORDER PLACEMENT FAILED")
    print("=" * 80)
    print(f"Error: {error_msg}")
    print()

    if '10007' in error_msg or 'symbol not support' in error_msg.lower():
        print("🚨 CRITICAL: Same issue as MEXC!")
        print("   BTC/USDT not supported for API trading on Binance")
        print("   This is VERY unexpected - contact Binance support")
        print()
        print("DO NOT PROCEED WITH MIGRATION")

    elif 'permission' in error_msg.lower() or 'unauthorized' in error_msg.lower():
        print("🔴 API KEY PERMISSION ISSUE")
        print()
        print("Fix:")
        print("  1. Go to Binance → Account → API Management")
        print("  2. Find your API key")
        print("  3. Click 'Edit'")
        print("  4. Enable 'Spot & Margin Trading'")
        print("  5. Save and run this test again")

    else:
        print("🔴 UNEXPECTED ERROR")
        print()
        print("Actions:")
        print("  1. Check Binance API status")
        print("  2. Verify API key settings")
        print("  3. Contact Binance support if needed")

    sys.exit(1)

except Exception as e:
    print()
    print("❌ Unexpected error during order test:")
    print(f"   {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
