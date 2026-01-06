#!/usr/bin/env python3
"""
Quick API Key Permission Test
Tests if new API key can place orders on BTC/USDT
"""
import os
import sys
import ccxt

print("=" * 70)
print("🔑 TESTING NEW API KEY")
print("=" * 70)

# Load from .env manually
env_vars = {}
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()
else:
    print("❌ .env file not found!")
    print("   Create it with your new API keys")
    sys.exit(1)

api_key = env_vars.get('MEXC_API_KEY')
secret = env_vars.get('MEXC_SECRET')

if not api_key or not secret:
    print("❌ MEXC_API_KEY or MEXC_SECRET not found in .env")
    sys.exit(1)

print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"Secret: {'*' * 20}")

# Initialize exchange
print("\n1️⃣  Initializing MEXC...")
try:
    mexc = ccxt.mexc({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    print("✅ Connected")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Check balance
print("\n2️⃣  Checking balance...")
try:
    balance = mexc.fetch_balance()
    usdt = balance.get('USDT', {}).get('total', 0)
    print(f"✅ Balance: ${usdt:,.2f} USDT")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Check BTC/USDT market status
print("\n3️⃣  Checking BTC/USDT market...")
try:
    markets = mexc.load_markets(reload=True)
    btc_market = markets.get('BTC/USDT', {})

    print(f"   Active: {btc_market.get('active', 'N/A')}")
    print(f"   Spot: {btc_market.get('spot', 'N/A')}")
    print(f"   Type: {btc_market.get('type', 'N/A')}")

    if not btc_market.get('active'):
        print("\n⚠️  Still showing Active: False")
        print("   This might be OK - let's try placing an order anyway...")
    else:
        print("\n✅ Market shows as ACTIVE!")

except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# THE CRITICAL TEST: Try to place an order
print("\n4️⃣  CRITICAL TEST: Attempting order placement...")
print("   (Test order WAY below market - won't fill)")

try:
    symbol = 'BTC/USDT'
    ticker = mexc.fetch_ticker(symbol)
    current_price = ticker['last']

    # Order 50% below market (safe - won't fill)
    test_price = round(current_price * 0.50, 2)
    test_amount = 0.0001  # Minimum

    print(f"\n   Current BTC: ${current_price:,.2f}")
    print(f"   Test Order: BUY {test_amount} BTC @ ${test_price:,.2f}")
    print(f"   Total Cost: ${test_price * test_amount:.2f}")
    print(f"   (50% below market - will NOT fill)")

    print("\n   Placing order in 3 seconds... (Ctrl+C to abort)")
    import time
    for i in range(3, 0, -1):
        print(f"   {i}...", end='\r', flush=True)
        time.sleep(1)

    # CREATE ORDER
    print("\n   Creating order...")
    order = mexc.create_limit_buy_order(
        symbol=symbol,
        amount=test_amount,
        price=test_price
    )

    print("\n" + "=" * 70)
    print("🎉 SUCCESS! ORDER PLACED!")
    print("=" * 70)
    print(f"Order ID: {order['id']}")
    print(f"Status: {order['status']}")
    print(f"Symbol: {order['symbol']}")
    print(f"Price: ${order['price']:,.2f}")
    print(f"Amount: {order['amount']} BTC")

    # Cancel it
    print("\nCanceling test order...")
    mexc.cancel_order(order['id'], symbol)
    print("✅ Order canceled")

    print("\n" + "=" * 70)
    print("✅ API KEY WORKS PERFECTLY!")
    print("=" * 70)
    print("\n🚀 READY TO LAUNCH LIVE BTC/ETH GRID BOTS!")
    print("\nNext step:")
    print("   python3 run_bot_mexc_SAFE_LIVE.py")
    print("=" * 70)

except ccxt.ExchangeError as e:
    error_msg = str(e)
    print("\n" + "=" * 70)
    print("❌ ORDER PLACEMENT FAILED")
    print("=" * 70)
    print(f"Error: {error_msg}")

    if '10007' in error_msg or 'symbol not support' in error_msg.lower():
        print("\n🔴 STILL GETTING ERROR 10007")
        print("\nPossible causes:")
        print("1. API key created with wrong permissions")
        print("   → Go back and check 'Spot & Margin Trading' is ENABLED")
        print("\n2. Account verification level too low")
        print("   → Complete full KYC verification on MEXC")
        print("\n3. MEXC regional restriction for API trading")
        print("   → Contact MEXC support")
        print("\n📞 Contact MEXC Support:")
        print("   Live Chat: https://www.mexc.com/support")
        print("   Email: support@mexc.com")
        print("   Ask: 'Why can't I trade BTC/USDT via API when manual trading works?'")

    sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
