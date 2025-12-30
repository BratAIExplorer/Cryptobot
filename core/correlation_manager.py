"""
Correlation Manager - Prevent Over-Concentration in Correlated Assets
Ensures portfolio diversification by blocking buys when too many correlated positions exist
"""

from decimal import Decimal
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class CorrelationManager:
    """
    Manages portfolio correlation to prevent fake diversification

    Example: If you have BTC, ETH, and BNB positions (all L1s, correlation ~0.8),
    this manager will block buying SOL or AVAX to avoid concentration risk.
    """

    def __init__(self, correlation_window: int = 30, correlation_threshold: float = 0.7):
        """
        Args:
            correlation_window: Days of price history to calculate correlation (default 30)
            correlation_threshold: Correlation coefficient threshold (default 0.7)
        """
        self.correlation_window = correlation_window
        self.correlation_threshold = correlation_threshold
        self.correlation_matrix = {}  # Cache correlation calculations
        self.last_update = None

    def calculate_correlation(self, df1: pd.DataFrame, df2: pd.DataFrame) -> float:
        """
        Calculate correlation between two price series

        Args:
            df1: OHLCV DataFrame for asset 1
            df2: OHLCV DataFrame for asset 2

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(df1) < self.correlation_window or len(df2) < self.correlation_window:
            return 0.0  # Not enough data, assume uncorrelated

        # Use last N days
        df1_recent = df1.tail(self.correlation_window).copy()
        df2_recent = df2.tail(self.correlation_window).copy()

        # Calculate returns
        returns1 = df1_recent['close'].pct_change().dropna()
        returns2 = df2_recent['close'].pct_change().dropna()

        # Ensure same length
        min_length = min(len(returns1), len(returns2))
        if min_length < 10:
            return 0.0  # Need at least 10 data points

        returns1 = returns1.tail(min_length)
        returns2 = returns2.tail(min_length)

        # Calculate Pearson correlation
        correlation = returns1.corr(returns2)

        return float(correlation) if not np.isnan(correlation) else 0.0

    def build_correlation_matrix(self, symbols: List[str], fetch_ohlcv_func) -> Dict[Tuple[str, str], float]:
        """
        Build correlation matrix for all symbol pairs

        Args:
            symbols: List of trading symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
            fetch_ohlcv_func: Function to fetch OHLCV data for a symbol

        Returns:
            Dictionary mapping (symbol1, symbol2) -> correlation coefficient
        """
        correlation_dict = {}

        # Fetch OHLCV for all symbols
        ohlcv_data = {}
        for symbol in symbols:
            try:
                df = fetch_ohlcv_func(symbol, timeframe='1d', limit=self.correlation_window + 10)
                if df is not None and len(df) >= self.correlation_window:
                    ohlcv_data[symbol] = df
            except Exception as e:
                print(f"⚠️  Failed to fetch OHLCV for {symbol}: {e}")
                continue

        # Calculate pairwise correlations
        symbols_with_data = list(ohlcv_data.keys())

        for i, sym1 in enumerate(symbols_with_data):
            for sym2 in symbols_with_data[i+1:]:
                try:
                    corr = self.calculate_correlation(ohlcv_data[sym1], ohlcv_data[sym2])
                    correlation_dict[(sym1, sym2)] = corr
                    correlation_dict[(sym2, sym1)] = corr  # Symmetric
                except Exception as e:
                    print(f"⚠️  Failed to calculate correlation for {sym1} vs {sym2}: {e}")
                    continue

        self.correlation_matrix = correlation_dict
        self.last_update = datetime.utcnow()

        return correlation_dict

    def get_correlated_symbols(self, target_symbol: str, open_positions: List[Dict]) -> List[Dict]:
        """
        Find which open positions are highly correlated with target symbol

        Args:
            target_symbol: Symbol being considered for entry (e.g., 'SOL/USDT')
            open_positions: List of open position dicts with 'symbol' key

        Returns:
            List of dicts with {'symbol': str, 'correlation': float}
        """
        correlated = []

        for position in open_positions:
            pos_symbol = position.get('symbol')

            if pos_symbol == target_symbol:
                continue  # Skip self

            # Get correlation from matrix
            corr_key = (target_symbol, pos_symbol)
            correlation = self.correlation_matrix.get(corr_key, 0.0)

            # Check if highly correlated
            if abs(correlation) >= self.correlation_threshold:
                correlated.append({
                    'symbol': pos_symbol,
                    'correlation': correlation
                })

        return correlated

    def should_block_entry(
        self,
        target_symbol: str,
        open_positions: List[Dict],
        max_correlated_positions: int = 2
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if entry should be blocked due to correlation risk

        Args:
            target_symbol: Symbol being considered for entry
            open_positions: List of current open positions
            max_correlated_positions: Maximum number of correlated positions allowed (default 2)

        Returns:
            (should_block: bool, reason: str)
        """
        # If correlation matrix not built yet, allow entry (fail-open)
        if not self.correlation_matrix:
            return False, None

        # Find correlated positions
        correlated_positions = self.get_correlated_symbols(target_symbol, open_positions)

        # Block if too many correlated positions
        if len(correlated_positions) >= max_correlated_positions:
            corr_symbols = [p['symbol'] for p in correlated_positions[:3]]
            corr_values = [f"{p['correlation']:.2f}" for p in correlated_positions[:3]]

            reason = (
                f"🚫 Correlation Risk: {len(correlated_positions)} positions highly correlated with {target_symbol}\n"
                f"   Correlated: {', '.join(corr_symbols)}\n"
                f"   Correlation: {', '.join(corr_values)}\n"
                f"   💡 Already have {len(correlated_positions)} positions moving together - avoid concentration"
            )

            return True, reason

        return False, None

    def get_correlation_report(self, open_positions: List[Dict], threshold: float = 0.7) -> Dict:
        """
        Generate correlation analysis report for current portfolio

        Args:
            open_positions: List of open positions
            threshold: Correlation threshold to highlight (default 0.7)

        Returns:
            Dict with correlation clusters and statistics
        """
        if not self.correlation_matrix:
            return {'status': 'No correlation data available'}

        # Build adjacency list of highly correlated positions
        position_symbols = [p.get('symbol') for p in open_positions]

        clusters = []
        processed = set()

        for sym1 in position_symbols:
            if sym1 in processed:
                continue

            # Find all symbols correlated with sym1
            cluster = [sym1]
            processed.add(sym1)

            for sym2 in position_symbols:
                if sym2 in processed:
                    continue

                corr = self.correlation_matrix.get((sym1, sym2), 0.0)

                if abs(corr) >= threshold:
                    cluster.append(sym2)
                    processed.add(sym2)

            if len(cluster) > 1:
                clusters.append(cluster)

        # Calculate average correlation within each cluster
        cluster_stats = []

        for cluster in clusters:
            correlations = []

            for i, sym1 in enumerate(cluster):
                for sym2 in cluster[i+1:]:
                    corr = self.correlation_matrix.get((sym1, sym2), 0.0)
                    correlations.append(abs(corr))

            avg_corr = np.mean(correlations) if correlations else 0.0

            cluster_stats.append({
                'symbols': cluster,
                'size': len(cluster),
                'avg_correlation': avg_corr
            })

        # Sort by cluster size (largest first)
        cluster_stats.sort(key=lambda x: x['size'], reverse=True)

        return {
            'total_positions': len(position_symbols),
            'correlation_clusters': cluster_stats,
            'largest_cluster_size': cluster_stats[0]['size'] if cluster_stats else 0,
            'total_clusters': len(cluster_stats),
            'diversification_score': 1.0 - (cluster_stats[0]['size'] / len(position_symbols) if position_symbols else 0)
        }

    def get_diversification_suggestions(self, all_symbols: List[str], open_positions: List[Dict]) -> List[str]:
        """
        Suggest symbols that would improve portfolio diversification

        Args:
            all_symbols: All available trading symbols
            open_positions: Current open positions

        Returns:
            List of symbols that are least correlated with current portfolio
        """
        if not self.correlation_matrix:
            return []

        position_symbols = [p.get('symbol') for p in open_positions]

        # Calculate average correlation of each candidate with portfolio
        candidate_scores = []

        for candidate in all_symbols:
            if candidate in position_symbols:
                continue  # Already have position

            # Calculate average correlation with existing positions
            correlations = []

            for pos_sym in position_symbols:
                corr = self.correlation_matrix.get((candidate, pos_sym), 0.0)
                correlations.append(abs(corr))

            avg_corr = np.mean(correlations) if correlations else 0.0

            candidate_scores.append({
                'symbol': candidate,
                'avg_correlation': avg_corr
            })

        # Sort by lowest correlation (most diversifying)
        candidate_scores.sort(key=lambda x: x['avg_correlation'])

        # Return top 5 most diversifying
        return [c['symbol'] for c in candidate_scores[:5]]


# Predefined correlation groups (for fallback when no historical data)
CORRELATION_GROUPS = {
    'L1_PLATFORMS': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'AVAX/USDT', 'DOT/USDT', 'ADA/USDT', 'MATIC/USDT'],
    'MEMECOINS': ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'FLOKI/USDT'],
    'DEFI_TOKENS': ['UNI/USDT', 'AAVE/USDT', 'LINK/USDT', 'CRV/USDT', 'SUSHI/USDT'],
    'GAMING_METAVERSE': ['SAND/USDT', 'MANA/USDT', 'AXS/USDT', 'GALA/USDT'],
    'STABLECOINS': ['USDT', 'USDC', 'DAI', 'BUSD']
}


def get_correlation_group(symbol: str) -> Optional[str]:
    """
    Fallback: Identify which correlation group a symbol belongs to

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')

    Returns:
        Group name or None
    """
    for group_name, symbols in CORRELATION_GROUPS.items():
        if symbol in symbols:
            return group_name
    return None


# Usage example:
# correlation_manager = CorrelationManager(correlation_window=30, correlation_threshold=0.7)
# correlation_manager.build_correlation_matrix(all_symbols, exchange.fetch_ohlcv)
# should_block, reason = correlation_manager.should_block_entry('SOL/USDT', open_positions, max_correlated_positions=2)
