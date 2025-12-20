"""
Signal Analyzer - Analyzes correlation between technical signals and other indicators
to prevent inflated confluence scores from redundant data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os

class SignalAnalyzer:
    def __init__(self):
        # Known redundant pairs (high correlation by nature)
        self.REDUNDANT_GROUPS = {
            'momentum': ['rsi', 'stoch_rsi', 'mfi', 'cci'],
            'trend': ['sma50', 'sma200', 'ema50', 'ema200', 'supertrend'],
            'volatility': ['bollinger_width', 'atr_percentile', 'historical_volatility'],
            'volume': ['volume_ma_ratio', 'obv_slope', 'pvt']
        }

    def calculate_correlation_matrix(self, df: pd.DataFrame, signals: List[str]) -> pd.DataFrame:
        """Calculate correlation matrix for a set of signals over historical data"""
        available_signals = [s for s in signals if s in df.columns]
        if not available_signals:
            return pd.DataFrame()
            
        return df[available_signals].corr()

    def get_redundancy_penalty(self, active_signals: Dict[str, bool], signal_values: Dict[str, float]) -> float:
        """
        Calculates a graduated penalty multiplier based on signal redundancy.
        
        Institutional Scale:
        - 2 signals in group: 0.8x penalty (only 80% weight)
        - 3 signals in group: 0.5x penalty (High correlation cluster)
        - 4+ signals in group: 0.2x penalty (Echo chamber - only count 1.2 signals max)
        """
        penalty = 1.0
        
        for group, members in self.REDUNDANT_GROUPS.items():
            count = sum(1 for m in members if active_signals.get(m, False))
            
            if count >= 4:
                penalty *= 0.20 # Severe echo chamber
            elif count == 3:
                penalty *= 0.50 # High correlation
            elif count == 2:
                penalty *= 0.80 # Overlap
                
        return max(0.2, penalty)


    def analyze_signal_independence(self, df: pd.DataFrame, signals: List[str]) -> Dict:
        """Comprehensive analysis of signal independence"""
        matrix = self.calculate_correlation_matrix(df, signals)
        
        high_corr_pairs = []
        if not matrix.empty:
            for i in range(len(matrix.columns)):
                for j in range(i + 1, len(matrix.columns)):
                    corr = matrix.iloc[i, j]
                    if abs(corr) > 0.85:
                        high_corr_pairs.append({
                            's1': matrix.columns[i],
                            's2': matrix.columns[j],
                            'correlation': round(corr, 3)
                        })
                        
        return {
            'correlation_matrix': matrix.to_dict(),
            'high_correlation_pairs': high_corr_pairs,
            'independence_score': 100 - (len(high_corr_pairs) * 10) # Simple heuristic
        }

if __name__ == "__main__":
    # Test with dummy data
    data = {
        'rsi': np.random.normal(50, 10, 100),
        'stoch_rsi': np.random.normal(50, 10, 100) + 2, # Correlated
        'volume': np.random.normal(1000, 100, 100),
        'price': np.random.normal(100, 5, 100)
    }
    df = pd.DataFrame(data)
    # Add correlation
    df['stoch_rsi'] = df['rsi'] * 0.9 + np.random.normal(0, 1, 100)
    
    analyzer = SignalAnalyzer()
    res = analyzer.analyze_signal_independence(df, ['rsi', 'stoch_rsi', 'volume'])
    print(f"High Correlation Pairs: {res['high_correlation_pairs']}")
