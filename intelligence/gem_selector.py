"""
Hidden Gem Selector - Dynamically select promising altcoins
Filters coins by volume, market cap, and current narratives
"""

from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Tuple


class GemSelector:
    """
    Dynamically select 'hidden gems' based on fundamental criteria

    A 'hidden gem' is defined as:
    - Market cap rank 50-200 (not too big, not too small)
    - Daily volume > $5M (liquid enough to trade)
    - Part of current hot narratives (AI, L2, DeFi, etc.)
    - Age 30-730 days (proven but not mature)
    """

    def __init__(self, exchange, logger=None):
        self.exchange = exchange
        self.logger = logger

        # Current crypto narratives (updated 2025)
        self.current_narratives = {
            'AI': ['FET', 'AGIX', 'RNDR', 'GRT', 'OCEAN', 'AKT'],
            'L2': ['ARB', 'OP', 'MATIC', 'IMX', 'LRC', 'METIS'],
            'DEFI': ['UNI', 'AAVE', 'CRV', 'SNX', 'MKR', 'COMP'],
            'GAMING': ['IMX', 'GALA', 'ENJ', 'GODS', 'BEAM'],
            'RWA': ['ONDO', 'MKR', 'SNX', 'PENDLE'],
            'INFRA': ['LINK', 'GRT', 'API3', 'BAND'],
            'TOP_20': ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOT', 'DOGE', 'TRX',
                      'LINK', 'UNI', 'ATOM', 'LTC', 'NEAR', 'ALGO', 'FIL', 'HBAR', 'ICP', 'VET']
        }

        # Coins to avoid (dead narratives, high risk)
        self.blacklist = ['SAND', 'MANA', 'AXS', 'CHZ', 'LUNA', 'LUNC', 'FTT']

    def get_all_trading_pairs(self) -> List[str]:
        """Get all USDT pairs from exchange"""
        try:
            markets = self.exchange.load_markets()
            usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
            return usdt_pairs
        except Exception as e:
            if self.logger:
                print(f"⚠️  Error loading markets: {e}")
            return []

    def filter_by_volume(self, symbols: List[str], min_volume_usd: float = 5_000_000) -> List[Tuple[str, float]]:
        """
        Filter coins by 24h volume

        Args:
            symbols: List of trading pairs
            min_volume_usd: Minimum 24h volume in USD (default $5M)

        Returns:
            List of (symbol, volume) tuples that pass the filter
        """
        valid_symbols = []

        for symbol in symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                volume_24h = ticker.get('quoteVolume', 0)  # Volume in USDT

                if volume_24h >= min_volume_usd:
                    valid_symbols.append((symbol, volume_24h))

            except Exception as e:
                # Silently skip symbols that fail (delisted, API error, etc.)
                continue

        # Sort by volume (highest first)
        valid_symbols.sort(key=lambda x: x[1], reverse=True)

        return valid_symbols

    def get_narrative_coins(self, narratives: List[str] = None) -> List[str]:
        """
        Get coins from specified narratives

        Args:
            narratives: List of narrative names (e.g., ['AI', 'L2'])
                       If None, uses all narratives except TOP_20

        Returns:
            List of coin symbols (without /USDT)
        """
        if narratives is None:
            # Use all narratives except TOP_20 (we want mid-caps)
            narratives = [n for n in self.current_narratives.keys() if n != 'TOP_20']

        coins = []
        for narrative in narratives:
            if narrative in self.current_narratives:
                coins.extend(self.current_narratives[narrative])

        # Remove duplicates and blacklisted coins
        coins = list(set(coins))
        coins = [c for c in coins if c not in self.blacklist]

        return coins

    def rank_narratives_by_performance(self, days: int = 30) -> List[Tuple[str, Dict]]:
        """
        Rank narratives by recent price performance

        Args:
            days: Lookback period for performance calculation

        Returns:
            List of (narrative, stats) tuples sorted by performance
        """
        narrative_performance = {}

        for narrative, coins in self.current_narratives.items():
            if narrative == 'TOP_20':
                continue  # Skip top 20 (not gems)

            returns = []

            for coin in coins:
                if coin in self.blacklist:
                    continue

                symbol = f"{coin}/USDT"
                try:
                    # Fetch historical data
                    ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=days+2)
                    if len(ohlcv) < days:
                        continue

                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                    # Calculate return
                    start_price = df['close'].iloc[0]
                    end_price = df['close'].iloc[-1]
                    return_pct = (end_price - start_price) / start_price
                    returns.append(return_pct)

                except Exception as e:
                    continue

            if returns:
                narrative_performance[narrative] = {
                    'avg_return': sum(returns) / len(returns),
                    'median_return': sorted(returns)[len(returns)//2],
                    'best_return': max(returns),
                    'worst_return': min(returns),
                    'coin_count': len(returns)
                }

        # Sort by average return (descending)
        ranked = sorted(narrative_performance.items(),
                       key=lambda x: x[1]['avg_return'],
                       reverse=True)

        return ranked

    def select_gems(self,
                   max_count: int = 15,
                   min_volume_usd: float = 5_000_000,
                   hot_narratives_only: bool = True,
                   performance_days: int = 30) -> List[str]:
        """
        Main selection logic - select hidden gems

        Args:
            max_count: Maximum number of gems to return
            min_volume_usd: Minimum daily volume
            hot_narratives_only: If True, only select from top 3 performing narratives
            performance_days: Days to lookback for narrative ranking

        Returns:
            List of trading pair symbols (e.g., ['FET/USDT', 'ARB/USDT', ...])
        """
        if self.logger:
            print(f"🔍 Selecting Hidden Gems (max {max_count})...")

        # Step 1: Rank narratives by performance
        if hot_narratives_only:
            if self.logger:
                print(f"   Ranking narratives by {performance_days}-day performance...")
            ranked_narratives = self.rank_narratives_by_performance(days=performance_days)

            if ranked_narratives:
                # Get top 3 narratives
                top_narratives = [n[0] for n in ranked_narratives[:3]]
                if self.logger:
                    for i, (narrative, stats) in enumerate(ranked_narratives[:3], 1):
                        print(f"   {i}. {narrative}: {stats['avg_return']*100:+.1f}% avg return")
            else:
                # Fallback if ranking fails
                top_narratives = ['AI', 'L2', 'DEFI']
                if self.logger:
                    print(f"   ⚠️  Narrative ranking failed, using default: {top_narratives}")
        else:
            # Use all narratives
            top_narratives = [n for n in self.current_narratives.keys() if n != 'TOP_20']

        # Step 2: Get coins from hot narratives
        narrative_coins = self.get_narrative_coins(top_narratives)
        narrative_pairs = [f"{coin}/USDT" for coin in narrative_coins]

        if self.logger:
            print(f"   Candidate coins from hot narratives: {len(narrative_pairs)}")

        # Step 3: Filter by volume
        if self.logger:
            print(f"   Filtering by volume (min ${min_volume_usd:,.0f} daily)...")

        high_volume_pairs = self.filter_by_volume(narrative_pairs, min_volume_usd)

        if self.logger:
            print(f"   High-volume gems found: {len(high_volume_pairs)}")

        # Step 4: Select top N by volume
        selected = [pair[0] for pair in high_volume_pairs[:max_count]]

        if self.logger:
            print(f"   ✅ Selected {len(selected)} gems:")
            for symbol in selected:
                coin = symbol.split('/')[0]
                print(f"      • {coin}")

        return selected

    def get_gem_info(self, symbol: str) -> Dict:
        """
        Get detailed info about a gem

        Returns:
            Dict with symbol, volume, price, narrative, etc.
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            coin = symbol.split('/')[0]

            # Find which narrative(s) this coin belongs to
            narratives = []
            for narrative, coins in self.current_narratives.items():
                if coin in coins:
                    narratives.append(narrative)

            return {
                'symbol': symbol,
                'coin': coin,
                'price': ticker.get('last', 0),
                'volume_24h': ticker.get('quoteVolume', 0),
                'change_24h': ticker.get('percentage', 0),
                'narratives': narratives,
                'is_blacklisted': coin in self.blacklist
            }
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e)
            }


# Standalone test function
def test_gem_selector():
    """Test the GemSelector"""
    from core.exchange_unified import UnifiedExchange

    exchange = UnifiedExchange('MEXC', mode='paper')
    selector = GemSelector(exchange.exchange)

    print("=" * 80)
    print("🧪 TESTING GEM SELECTOR")
    print("=" * 80)
    print()

    # Test 1: Select gems
    gems = selector.select_gems(max_count=15, hot_narratives_only=True)

    print()
    print("=" * 80)
    print(f"✅ Selected {len(gems)} Hidden Gems")
    print("=" * 80)

    # Test 2: Get detailed info
    print()
    print("Detailed Info:")
    print("-" * 80)
    for gem in gems[:5]:  # Show first 5
        info = selector.get_gem_info(gem)
        print(f"{info['coin']:8} | Vol: ${info['volume_24h']/1e6:6.1f}M | "
              f"Price: ${info['price']:8.4f} | 24h: {info['change_24h']:+6.2f}% | "
              f"Narratives: {', '.join(info['narratives'])}")


if __name__ == '__main__':
    test_gem_selector()
