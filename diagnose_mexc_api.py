#!/usr/bin/env python3
"""
MEXC API Diagnostic Tool
Checks API permissions, market access, and order capabilities
"""
import os
import sys
import ccxt

print("=" * 80)
print("🔍 MEXC API DIAGNOSTIC TOOL")
print("=" * 80)

# Check for API credentials
print("\n1️⃣  Checking API Credentials...")
api_key = os.environ.get('MEXC_API_KEY') or os.environ.get('MEXC_KEY')
secret = os.environ.get('MEXC_SECRET') or os.environ.get('MEXC_SECRET_KEY')

if not api_key:
    print("❌ MEXC_API_KEY not found in environment")
    print("   Set with: export MEXC_API_KEY='your_key_here'")
    print("   OR create .env file with MEXC_API_KEY=your_key_here")
    sys.exit(1)

if not secret:
    print("❌ MEXC_SECRET not found in environment")
    print("   Set with: export MEXC_SECRET='your_secret_here'")
    sys.exit(1)

print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
print(f"✅ Secret found: {'*' * 40}")

# Initialize exchange
print("\n2️⃣  Initializing MEXC Exchange...")
try:
    mexc = ccxt.mexc({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',  # Ensure spot trading
        }
    })
    print("✅ Exchange initialized")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 1: Fetch balance
print("\n3️⃣  Testing Account Access (fetch_balance)...")
try:
    balance = mexc.fetch_balance()
    usdt = balance.get('USDT', {}).get('total', 0)
    print(f"✅ Account access works")
    print(f"   USDT Balance: ${usdt:,.2f}")

    # Show all non-zero balances
    print("\n   All balances:")
    for currency, data in balance.items():
        if isinstance(data, dict) and data.get('total', 0) > 0:
            print(f"      {currency}: {data['total']}")
except Exception as e:
    print(f"❌ Account access failed: {e}")
    sys.exit(1)

# Test 2: Check market data access
print("\n4️⃣  Testing Market Data Access...")
test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
for symbol in test_symbols:
    try:
        ticker = mexc.fetch_ticker(symbol)
        print(f"✅ {symbol:12s} Price: ${ticker['last']:>10,.2f}")
    except Exception as e:
        print(f"❌ {symbol:12s} Error: {e}")

# Test 3: Load markets and check trading permissions
print("\n5️⃣  Checking Market Trading Status...")
try:
    markets = mexc.load_markets(reload=True)

    for symbol in test_symbols:
        if symbol in markets:
            market = markets[symbol]
            print(f"\n{symbol}:")
            print(f"   Active: {market.get('active', 'N/A')}")
            print(f"   Spot: {market.get('spot', 'N/A')}")
            print(f"   Type: {market.get('type', 'N/A')}")
            print(f"   Limits - Min Amount: {market.get('limits', {}).get('amount', {}).get('min', 'N/A')}")
            print(f"   Limits - Min Cost: {market.get('limits', {}).get('cost', {}).get('min', 'N/A')}")

            # Check permissions
            permissions = market.get('permissions', market.get('permission', []))
            print(f"   Permissions: {permissions if permissions else 'Not specified'}")
        else:
            print(f"❌ {symbol} not found in markets")
except Exception as e:
    print(f"❌ Market loading failed: {e}")

# Test 4: Check open orders (requires trading permission)
print("\n6️⃣  Testing Order Query Permission...")
try:
    orders = mexc.fetch_open_orders('BTC/USDT')
    print(f"✅ Can query orders ({len(orders)} open)")
except Exception as e:
    print(f"❌ Order query failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test 5: Try to create test order (CRITICAL TEST)
print("\n7️⃣  Testing Order Creation Permission...")
print("   WARNING: This will attempt to place a REAL order!")
print("   (Don't worry - order placed WAY below market, won't fill)")

try:
    symbol = 'BTC/USDT'
    ticker = mexc.fetch_ticker(symbol)
    current_price = ticker['last']

    # Order parameters - way below market so it won't fill
    test_price = round(current_price * 0.50, 2)  # 50% below market
    test_amount = 0.0001  # Minimum BTC amount (~$4-5)

    print(f"\n   Current BTC Price: ${current_price:,.2f}")
    print(f"   Test Order: BUY {test_amount} BTC @ ${test_price:,.2f}")
    print(f"   Total Cost: ${test_price * test_amount:.2f}")
    print(f"   (Order is 50% below market - will NOT fill)")

    # Confirm before creating
    print("\n   Creating test order in 3 seconds... (Ctrl+C to abort)")
    import time
    for i in range(3, 0, -1):
        print(f"   {i}...", end='\r')
        time.sleep(1)

    # Create limit order
    order = mexc.create_limit_buy_order(
        symbol=symbol,
        amount=test_amount,
        price=test_price
    )

    print("\n✅ ORDER CREATION WORKS!")
    print(f"   Order ID: {order['id']}")
    print(f"   Status: {order['status']}")
    print(f"   Price: ${order['price']}")
    print(f"   Amount: {order['amount']} BTC")

    # Cancel immediately
    print("\n   Canceling test order...")
    mexc.cancel_order(order['id'], symbol)
    print("✅ Order canceled successfully")

    print("\n" + "=" * 80)
    print("🎉 SUCCESS! Your API keys have FULL TRADING permissions!")
    print("=" * 80)
    print("\n✅ You can trade BTC/USDT and ETH/USDT on MEXC")
    print("✅ Ready to launch live bots!")

except ccxt.InsufficientFunds as e:
    print(f"\n⚠️  Insufficient balance to place test order")
    print(f"   This is OK - it means API has trading permission!")
    print(f"   Error: {e}")

except ccxt.ExchangeError as e:
    error_msg = str(e)
    print(f"\n❌ ORDER CREATION FAILED")
    print(f"   Error: {error_msg}")

    # Diagnose specific errors
    if '10007' in error_msg or 'symbol not support' in error_msg.lower():
        print("\n🔍 ERROR 10007: Symbol not supported for API trading")
        print("   Possible causes:")
        print("   1. API key created with 'Read Only' permission")
        print("      → Solution: Create new API key with 'Spot Trading' enabled")
        print("   2. Account verification level insufficient")
        print("      → Solution: Complete KYC verification on MEXC")
        print("   3. Spot trading not enabled for your account region")
        print("      → Solution: Contact MEXC support")
        print("\n   🔧 RECOMMENDED ACTION:")
        print("   1. Go to MEXC → Account → API Management")
        print("   2. DELETE current API key")
        print("   3. CREATE NEW key with these permissions:")
        print("      ✅ Read")
        print("      ✅ Spot Trading")
        print("      ❌ Futures (not needed)")
        print("   4. Update .env file with new keys")
        print("   5. Run this diagnostic again")

    elif 'permission' in error_msg.lower() or 'unauthorized' in error_msg.lower():
        print("\n🔍 PERMISSION ERROR")
        print("   Your API key does NOT have trading permission")
        print("   → Recreate API key with 'Spot Trading' permission enabled")

    else:
        print(f"\n🔍 Unknown error - see details above")

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("📋 DIAGNOSTIC COMPLETE")
print("=" * 80)
