#!/usr/bin/env python3
"""
Binance Market Analysis - Find Volatile High-Volume Coins
Analyzes 48-hour price movements and trading volumes
"""
import requests
import json
from datetime import datetime
from operator import itemgetter

def analyze_binance_markets():
    """Analyze Binance markets for volatility and volume"""

    print("=" * 80)
    print("🔍 BINANCE MARKET ANALYSIS - Last 24 Hours")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("\n📊 Fetching market data from Binance...")

    try:
        # Get 24h ticker data from Binance API
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
        response.raise_for_status()
        tickers = response.json()

        # Filter for USDT pairs only
        usdt_pairs = [
            t for t in tickers
            if t['symbol'].endswith('USDT') and float(t['quoteVolume']) > 0
        ]

        print(f"✅ Found {len(usdt_pairs)} USDT trading pairs\n")

        # Prepare data for analysis
        analysis_data = []

        for ticker in usdt_pairs:
            try:
                symbol = ticker['symbol'].replace('USDT', '/USDT')
                price = float(ticker['lastPrice'])
                change_24h = float(ticker['priceChangePercent'])
                volume_usdt = float(ticker['quoteVolume'])

                if price > 0 and volume_usdt > 0:
                    analysis_data.append({
                        'symbol': symbol,
                        'price': price,
                        'change_24h': change_24h,
                        'volume_usdt': volume_usdt,
                        'volume_millions': volume_usdt / 1_000_000
                    })
            except Exception as e:
                continue

        if not analysis_data:
            print("❌ No data available")
            return

        # Sort by volume
        analysis_data.sort(key=lambda x: x['volume_usdt'], reverse=True)

        # Add rank
        for idx, item in enumerate(analysis_data, 1):
            item['volume_rank'] = idx

        print("=" * 80)
        print("📈 TOP 20 COINS BY VOLUME (24H)")
        print("=" * 80)

        top_20_volume = analysis_data[:20]
        print(f"\n{'Rank':<6} {'Symbol':<15} {'Price':<12} {'Change 24h':<12} {'Volume ($M)':<15}")
        print("-" * 80)

        for item in top_20_volume:
            change_str = f"{item['change_24h']:+.2f}%"
            print(f"{item['volume_rank']:<6} {item['symbol']:<15} ${item['price']:<11.2f} {change_str:<12} ${item['volume_millions']:<14,.2f}")

        print("\n" + "=" * 80)
        print("🎯 COINS WITH 4-10% MOVEMENT (24H) - HIGH VOLUME")
        print("=" * 80)

        # Filter for 4-10% movement (absolute value)
        volatile_coins = [
            item for item in analysis_data
            if abs(item['change_24h']) >= 4 and abs(item['change_24h']) <= 10
        ]

        if not volatile_coins:
            print("\n⚠️  No coins found with 4-10% movement in last 24h")
        else:
            print(f"\n✅ Found {len(volatile_coins)} coins with 4-10% movement\n")
            print(f"{'Symbol':<15} {'Price':<12} {'Change 24h':<12} {'Volume ($M)':<15} {'Vol Rank':<10}")
            print("-" * 80)

            for item in volatile_coins[:30]:
                change_str = f"{item['change_24h']:+.2f}%"
                vol_rank = f"#{int(item['volume_rank'])}"

                # Highlight if in top 20 volume
                marker = "⭐" if item['volume_rank'] <= 20 else "  "

                print(f"{marker} {item['symbol']:<15} ${item['price']:<11.2f} {change_str:<12} ${item['volume_millions']:<14,.2f} {vol_rank:<10}")

        # Analysis: Overlap between volatile and high volume
        print("\n" + "=" * 80)
        print("🎯 IDEAL CANDIDATES (Top 20 Volume + 4-10% Movement)")
        print("=" * 80)

        ideal_candidates = [item for item in volatile_coins if item['volume_rank'] <= 20]

        if not ideal_candidates:
            print("\n⚠️  No top-20 volume coins with 4-10% movement currently")
            print("💡 This is actually GOOD for grid bots (prefer stability)")
        else:
            print(f"\n✅ {len(ideal_candidates)} coins meet both criteria:\n")

            for item in ideal_candidates:
                change_str = f"{item['change_24h']:+.2f}%"
                print(f"⭐ {item['symbol']:<15} - Change: {change_str}, Volume: ${item['volume_millions']:.2f}M")

        # Grid Bot Candidates
        print("\n" + "=" * 80)
        print("🤖 GRID BOT CANDIDATES (Top Volume, <4% Movement = More Stable)")
        print("=" * 80)

        stable_high_volume = [
            item for item in analysis_data[:20]
            if abs(item['change_24h']) < 4
        ]

        print(f"\n✅ {len(stable_high_volume)} stable high-volume coins (better for grids):\n")

        for item in stable_high_volume[:10]:
            change_str = f"{item['change_24h']:+.2f}%"
            print(f"  {item['symbol']:<15} - Change: {change_str}, Volume: ${item['volume_millions']:.2f}M")

        # Buy-the-Dip Candidates
        print("\n" + "=" * 80)
        print("📉 BUY-THE-DIP CANDIDATES (High Volume, -4% to -10% = Dipping)")
        print("=" * 80)

        dip_candidates = [
            item for item in analysis_data[:50]
            if item['change_24h'] >= -10 and item['change_24h'] <= -4
        ]

        if not dip_candidates:
            print("\n⚠️  No significant dips in top 50 volume coins currently")
        else:
            print(f"\n✅ {len(dip_candidates)} coins dipping (good for buy-the-dip):\n")

            for item in dip_candidates[:10]:
                change_str = f"{item['change_24h']:+.2f}%"
                vol_rank = f"#{int(item['volume_rank'])}"
                print(f"  {item['symbol']:<15} - Change: {change_str}, Volume: ${item['volume_millions']:.2f}M, Rank: {vol_rank}")

        print("\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS")
        print("=" * 80)

        changes = [item['change_24h'] for item in analysis_data]
        avg_change = sum(changes) / len(changes)
        sorted_changes = sorted(changes)
        median_change = sorted_changes[len(sorted_changes) // 2]
        most_volatile = max(analysis_data, key=lambda x: abs(x['change_24h']))

        print(f"\nTotal USDT pairs analyzed: {len(analysis_data)}")
        print(f"Average 24h change: {avg_change:+.2f}%")
        print(f"Median 24h change: {median_change:+.2f}%")
        print(f"Most volatile (24h): {most_volatile['symbol']} ({abs(most_volatile['change_24h']):.2f}%)")
        print(f"Highest volume: {analysis_data[0]['symbol']} (${analysis_data[0]['volume_millions']:.2f}M)")

        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_binance_markets()
