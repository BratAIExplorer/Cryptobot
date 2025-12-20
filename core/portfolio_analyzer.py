import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class PortfolioCorrelationAnalyzer:
    """
    Analyzes correlation between different coins in the portfolio
    to prevent over-exposure to highly correlated assets.
    """
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.correlation_threshold = 0.70  # Institutional limit for "High Correlation"

    def get_portfolio_overlap(self, target_symbol: str, active_symbols: List[str], exchange) -> Dict:
        """
        Calculate correlation between target coin and existing portfolio.
        
        Args:
            target_symbol: The coin we want to buy (e.g. "SOL/USDT")
            active_symbols: List of symbols already in positions (e.g. ["BTC/USDT", "ETH/USDT"])
            exchange: Exchange interface to fetch data
            
        Returns:
            Dict with correlation details and risk assessment
        """
        if not active_symbols:
            return {'average_correlation': 0.0, 'max_correlation': 0.0, 'risk': 'LOW', 'highly_correlated_with': []}

        all_symbols = list(set(active_symbols + [target_symbol]))
        price_data = {}
        
        # Fetch historical data for all involved coins
        for symbol in all_symbols:
            try:
                # 30 days of daily data for stable correlation baseline
                df = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=self.lookback_days + 1)
                if not df.empty:
                    # Use closing prices
                    price_data[symbol] = df['close'].pct_change().dropna()
            except Exception as e:
                print(f"[Correlation] Failed to fetch data for {symbol}: {e}")

        if target_symbol not in price_data or len(price_data) < 2:
            return {'average_correlation': 0.0, 'max_correlation': 0.0, 'risk': 'UNKNOWN'}

        # Build returns matrix
        returns_df = pd.DataFrame(price_data)
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Get correlations with target_symbol
        target_corrs = corr_matrix[target_symbol].drop(target_symbol)
        
        avg_corr = target_corrs.mean()
        max_corr = target_corrs.max()
        highly_correlated_with = target_corrs[target_corrs > self.correlation_threshold].index.tolist()
        
        risk_level = 'LOW'
        if max_corr > 0.85:
            risk_level = 'EXTREME'
        elif max_corr > 0.70:
            risk_level = 'HIGH'
        elif avg_corr > 0.50:
            risk_level = 'MEDIUM'
            
        return {
            'average_correlation': round(float(avg_corr), 3),
            'max_correlation': round(float(max_corr), 3),
            'risk': risk_level,
            'highly_correlated_with': highly_correlated_with,
            'matrix': corr_matrix.to_dict()
        }

    def get_penalty_multiplier(self, correlation_result: Dict) -> float:
        """
        Return a suggested multiplier to reduce position size based on correlation risk.
        """
        risk = correlation_result.get('risk', 'LOW')
        if risk == 'EXTREME':
            return 0.25  # Only 25% of normal size
        elif risk == 'HIGH':
            return 0.50
        elif risk == 'MEDIUM':
            return 0.80
        return 1.0

if __name__ == "__main__":
    # Example test logic
    pass
