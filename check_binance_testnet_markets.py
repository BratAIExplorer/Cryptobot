#!/usr/bin/env python3
"""
Check available markets on Binance Testnet for Grid Trading
"""
import os
import ccxt
from dotenv import load_dotenv

load_dotenv('.env.binance.paper')

print("=" * 80)
print("🔍 BINANCE TESTNET MARKET ANALYSIS")
print("=" * 80)

binance = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'enableRateLimit': True,
})

# Enable testnet
binance.set_sandbox_mode(True)

print("\n📊 Loading markets...")
markets = binance.load_markets()

print(f"✅ Total markets: {len(markets)}")

# Filter for USDT spot pairs
usdt_pairs = [
    symbol for symbol, market in markets.items()
    if symbol.endswith('/USDT') and market.get('spot') and market.get('active')
]

print(f"\n💰 Active USDT Spot Pairs on Testnet: {len(usdt_pairs)}")
print("\nTop candidates for Grid Trading:")
print("-" * 80)

# Get tickers for volume/price analysis
candidates = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
              'ADA/USDT', 'DOGE/USDT', 'MATIC/USDT', 'DOT/USDT', 'AVAX/USDT']

for symbol in candidates:
    if symbol in usdt_pairs:
        try:
            ticker = binance.fetch_ticker(symbol)
            price = ticker['last']
            volume_24h = ticker.get('quoteVolume', 0)

            # Get market info
            market = markets[symbol]
            min_amount = market['limits']['amount']['min']
            min_cost = market['limits']['cost']['min']

            print(f"\n{symbol}")
            print(f"  Price: ${price:,.2f}")
            print(f"  24h Volume: ${volume_24h:,.0f}")
            print(f"  Min Order: {min_amount} {symbol.split('/')[0]}")
            print(f"  Min Cost: ${min_cost}")
            print(f"  Active: {market.get('active')}")
        except Exception as e:
            print(f"\n{symbol}: ❌ {e}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS FOR GRID TRADING")
print("=" * 80)

recommendations = """
Based on Grid Trading criteria (range-bound, liquid, moderate volatility):

TOP TIER (Best for Grid):
1. BTC/USDT  - ✅ Already active, stable, high liquidity
2. ETH/USDT  - ✅ Already active, good liquidity
3. BNB/USDT  - Native Binance token, good for grid

MID TIER (Consider for diversification):
4. SOL/USDT  - High volatility, good for wider grids
5. XRP/USDT  - Often range-bound, good candidate
6. ADA/USDT  - Lower price, more grid opportunities

AVOID FOR GRID (Too volatile or low liquidity):
- DOGE/USDT - Meme coin, unpredictable
- Low-cap alts - Insufficient liquidity on testnet

RECOMMENDATION FOR PHASE 3 PAPER TESTING:
- Keep: BTC/USDT ($80), ETH/USDT ($60)
- Add: BNB/USDT ($40) - test with remaining capital
- Reserve: $38.08

This gives you:
- Large cap (BTC)
- Smart contract platform (ETH)
- Exchange token (BNB)
- Good diversification for testing
"""

print(recommendations)
