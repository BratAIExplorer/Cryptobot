"""
Volatility Clustering Detection
Adjusts TP targets based on market volatility conditions
"""

from decimal import Decimal
import pandas as pd


class VolatilityClusterDetector:
    """
    Detect if market is in low/normal/high/extreme volatility regime
    and adjust take profit targets accordingly
    """

    def __init__(self):
        self.vol_window = 90  # 90-period rolling window for volatility

    def detect_volatility_state(self, df: pd.DataFrame) -> str:
        """
        Detect current volatility regime

        Args:
            df: OHLCV DataFrame

        Returns:
            'LOW', 'NORMAL', 'HIGH', or 'EXTREME'
        """
        if len(df) < self.vol_window:
            return 'NORMAL'  # Default if insufficient data

        # Calculate returns
        returns = df['close'].pct_change()

        # Rolling volatility (standard deviation)
        vol = returns.rolling(window=self.vol_window).std()

        if vol.empty or len(vol) < self.vol_window:
            return 'NORMAL'

        current_vol = vol.iloc[-1]

        # Calculate percentile of current volatility
        vol_percentile = (vol < current_vol).sum() / len(vol)

        # Classify
        if vol_percentile > 0.95:
            return 'EXTREME'  # Top 5% volatility
        elif vol_percentile > 0.75:
            return 'HIGH'  # Top 25%
        elif vol_percentile < 0.25:
            return 'LOW'  # Bottom 25%
        else:
            return 'NORMAL'

    def adjust_tp_for_volatility(self, base_tp: Decimal, vol_state: str) -> Decimal:
        """
        Adjust take profit based on volatility

        Args:
            base_tp: Base take profit percentage (e.g., 0.05 for 5%)
            vol_state: 'LOW', 'NORMAL', 'HIGH', or 'EXTREME'

        Returns:
            Adjusted TP as Decimal
        """
        if vol_state == 'EXTREME':
            # Extreme volatility = widen TP (let it run, could hit big moves)
            return base_tp * Decimal("1.5")

        elif vol_state == 'HIGH':
            # High volatility = slight widen
            return base_tp * Decimal("1.2")

        elif vol_state == 'LOW':
            # Low volatility = tighten TP (take profits faster)
            return base_tp * Decimal("0.8")

        else:
            # Normal volatility = use base TP
            return base_tp

    def get_volatility_context(self, df: pd.DataFrame) -> dict:
        """
        Get full volatility context for logging/debugging

        Returns:
            dict with vol_state, current_vol, percentile
        """
        if len(df) < self.vol_window:
            return {
                'vol_state': 'NORMAL',
                'current_vol': 0.0,
                'percentile': 0.5,
                'note': 'Insufficient data'
            }

        returns = df['close'].pct_change()
        vol = returns.rolling(window=self.vol_window).std()

        if vol.empty or len(vol) < self.vol_window:
            return {
                'vol_state': 'NORMAL',
                'current_vol': 0.0,
                'percentile': 0.5,
                'note': 'Insufficient volatility data'
            }

        current_vol = float(vol.iloc[-1])
        percentile = float((vol < current_vol).sum() / len(vol))
        vol_state = self.detect_volatility_state(df)

        return {
            'vol_state': vol_state,
            'current_vol': current_vol,
            'percentile': percentile,
            'note': 'OK'
        }


# Usage example:
# detector = VolatilityClusterDetector()
# vol_state = detector.detect_volatility_state(df)
# adjusted_tp = detector.adjust_tp_for_volatility(Decimal("0.05"), vol_state)
