"""
Regime Detection System
Identifies market state to adjust trading aggression
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Tuple, Optional, Dict
import pandas as pd
import numpy as np


class RegimeState(Enum):
    """Market regime classifications"""
    BULL_CONFIRMED = "BULL_CONFIRMED"      # Clear uptrend, full aggression
    BEAR_CONFIRMED = "BEAR_CONFIRMED"      # Clear downtrend, sit out
    TRANSITION_BULLISH = "TRANSITION_UP"   # Turning bullish, 50% size
    TRANSITION_BEARISH = "TRANSITION_DOWN" # Turning bearish, 25% size
    UNDEFINED = "UNDEFINED"                 # Unclear, no trades
    CRISIS = "CRISIS"                       # Flash crash detected, freeze


@dataclass
class RegimeMetrics:
    """Metrics used for regime classification"""
    btc_price: float
    btc_ma50: float
    btc_ma200: float
    btc_volatility_percentile: float  # 0-100
    higher_highs: bool
    lower_lows: bool
    volume_trend: str  # INCREASING, STABLE, DECREASING
    recent_drawdown_pct: float  # From peak in last 30 days


class RegimeDetector:
    """
    Multi-timeframe regime detection for crypto markets.
    
    Logic:
    1. BULL_CONFIRMED: BTC > MA200, MA50 > MA200, higher highs, vol < 80th percentile
    2. BEAR_CONFIRMED: BTC < MA200, MA50 < MA200, lower lows
    3. TRANSITION_BULLISH: BTC crossed above MA200 recently, but no higher highs yet
    4. TRANSITION_BEARISH: BTC still > MA200, but MA50 < MA200
    5. UNDEFINED: Conflicting signals or choppy action
    6. CRISIS: >15% drawdown in 48 hours OR volatility > 95th percentile
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.last_state = RegimeState.UNDEFINED
        self.state_durability = 0 # How many candles the current state has held
        self.min_durability = 4   # Minimum periods to confirm state change (hysteresis)
        
    def detect_regime(self, btc_df: pd.DataFrame) -> Tuple[RegimeState, float, Dict]:
        """
        Detect current market regime based on BTC data.
        
        Args:
            btc_df: DataFrame with OHLCV data (minimum 200 candles)
            
        Returns:
            Tuple of (regime_state, confidence_score_0_to_1, metrics_dict)
        """
        if len(btc_df) < 200:
            return RegimeState.UNDEFINED, 0.0, {"error": "Insufficient data (need 200+ candles)"}
        
        # Calculate metrics
        metrics = self._calculate_metrics(btc_df)
        
        # Crisis detection (highest priority)
        if self._is_crisis(btc_df, metrics):
            return RegimeState.CRISIS, 1.0, self._metrics_to_dict(metrics)
        
        # Normal regime classification
        raw_regime, confidence = self._classify_regime(metrics)
        
        # Apply Hysteresis (Stability Filter)
        if raw_regime == self.last_state:
            self.state_durability += 1
        else:
            # Only switch if held for min periods OR switching to CRISIS (instant)
            if self.state_durability >= self.min_durability or raw_regime == RegimeState.CRISIS:
                self.last_state = raw_regime
                self.state_durability = 0
            else:
                self.state_durability += 1
                # Keep old state for stability
                raw_regime = self.last_state
                
        return raw_regime, confidence, self._metrics_to_dict(metrics)
    
    def _calculate_metrics(self, btc_df: pd.DataFrame) -> RegimeMetrics:
        """Calculate all metrics needed for regime classification"""
        current_price = float(btc_df['close'].iloc[-1])
        
        # Moving averages
        ma50 = float(btc_df['close'].rolling(50).mean().iloc[-1])
        ma200 = float(btc_df['close'].rolling(200).mean().iloc[-1])
        
        # Volatility percentile (using 90-day rolling std)
        volatility = btc_df['close'].pct_change().rolling(90).std()
        current_vol = float(volatility.iloc[-1])
        vol_percentile = float((volatility < current_vol).sum() / len(volatility) * 100)
        
        # Higher highs / Lower lows (last 30 days vs previous 30 days)
        recent_high = float(btc_df['high'].iloc[-30:].max())
        previous_high = float(btc_df['high'].iloc[-60:-30].max())
        higher_highs = recent_high > previous_high
        
        recent_low = float(btc_df['low'].iloc[-30:].min())
        previous_low = float(btc_df['low'].iloc[-60:-30].min())
        lower_lows = recent_low < previous_low
        
        # Volume trend
        recent_volume = btc_df['volume'].iloc[-20:].mean()
        previous_volume = btc_df['volume'].iloc[-40:-20].mean()
        if recent_volume > previous_volume * 1.2:
            volume_trend = "INCREASING"
        elif recent_volume < previous_volume * 0.8:
            volume_trend = "DECREASING"
        else:
            volume_trend = "STABLE"
        
        # Recent drawdown (from 30-day peak)
        peak_30d = float(btc_df['high'].iloc[-30:].max())
        drawdown_pct = ((current_price - peak_30d) / peak_30d) * 100
        
        return RegimeMetrics(
            btc_price=current_price,
            btc_ma50=ma50,
            btc_ma200=ma200,
            btc_volatility_percentile=vol_percentile,
            higher_highs=higher_highs,
            lower_lows=lower_lows,
            volume_trend=volume_trend,
            recent_drawdown_pct=drawdown_pct
        )
    
    def _is_crisis(self, btc_df: pd.DataFrame, metrics: RegimeMetrics) -> bool:
        """
        Detect crisis conditions (flash crash, extreme volatility)
        
        Crisis triggers:
        - >15% drawdown in last 48 hours (2 days)
        - Volatility > 95th percentile
        - Price gap > 10% in single candle
        """
        # Check 48-hour drawdown (assuming daily candles, check last 2)
        if len(btc_df) >= 2:
            peak_2d = float(btc_df['high'].iloc[-2:].max())
            current = float(btc_df['close'].iloc[-1])
            drawdown_2d = ((current - peak_2d) / peak_2d) * 100
            
            if drawdown_2d < -15:
                return True
        
        # Extreme volatility
        if metrics.btc_volatility_percentile > 95:
            return True
        
        # Price gap check (single candle)
        if len(btc_df) >= 2:
            prev_close = float(btc_df['close'].iloc[-2])
            current_open = float(btc_df['open'].iloc[-1])
            gap_pct = abs((current_open - prev_close) / prev_close) * 100
            
            if gap_pct > 10:
                return True
        
        return False
    
    def _classify_regime(self, metrics: RegimeMetrics) -> Tuple[RegimeState, float]:
        """
        Classify regime based on calculated metrics.
        
        Returns:
            Tuple of (regime_state, confidence_0_to_1)
        """
        price = metrics.btc_price
        ma50 = metrics.btc_ma50
        ma200 = metrics.btc_ma200
        
        # BULL CONFIRMED (1.2x Aggression)
        # BTC > MA200 AND MA50 > MA200 AND Low Vol
        if price > ma200 and ma50 > ma200 and metrics.higher_highs:
            if metrics.btc_volatility_percentile < 70:
                return RegimeState.BULL_CONFIRMED, 0.95
            
        # BEAR CONFIRMED (0.0x Aggression)
        if price < ma200 and ma50 < ma200 and metrics.lower_lows:
            return RegimeState.BEAR_CONFIRMED, 0.9
            
        # TRANSITION BULLISH (0.5x)
        # Price crossed MA200 but MA50 still below OR Volatility spiking
        if price > ma200 and (ma50 < ma200 or metrics.btc_volatility_percentile > 80):
            return RegimeState.TRANSITION_BULLISH, 0.6
            
        # TRANSITION BEARISH (0.25x)
        # Price still > MA200 but MA50 crossed below OR lower highs starting
        if price > ma200 and ma50 < ma200 and not metrics.higher_highs:
            return RegimeState.TRANSITION_BEARISH, 0.7
        
        # UNDEFINED (0.25x)
        # Mixed signals or within 2% of MA200 (Magnet zone)
        ma_prox = abs(price - ma200) / ma200
        if ma_prox < 0.02:
            return RegimeState.UNDEFINED, 0.5
            
        return RegimeState.UNDEFINED, 0.3
    
    def _metrics_to_dict(self, metrics: RegimeMetrics) -> Dict:
        """Convert metrics dataclass to dictionary"""
        return {
            'btc_price': metrics.btc_price,
            'btc_ma50': metrics.btc_ma50,
            'btc_ma200': metrics.btc_ma200,
            'price_vs_ma200': ((metrics.btc_price / metrics.btc_ma200) - 1) * 100,
            'volatility_percentile': metrics.btc_volatility_percentile,
            'higher_highs': metrics.higher_highs,
            'lower_lows': metrics.lower_lows,
            'volume_trend': metrics.volume_trend,
            'recent_drawdown_pct': metrics.recent_drawdown_pct
        }
    
    def get_risk_multiplier(self, regime: RegimeState) -> float:
        """
        Get position size multiplier based on regime.
        
        This is applied AFTER base confluence scoring:
        final_size = base_size * confluence_multiplier * regime_multiplier
        
        Returns:
            Multiplier from 0.0 (no trading) to 1.0 (full size)
        """
        multipliers = {
            RegimeState.BULL_CONFIRMED: 1.25,     # Increased aggression (1.25x)
            RegimeState.TRANSITION_BULLISH: 0.60, # Moderate
            RegimeState.UNDEFINED: 0.20,          # Conservative
            RegimeState.TRANSITION_BEARISH: 0.25, # Caution
            RegimeState.BEAR_CONFIRMED: 0.0,      # Block
            RegimeState.CRISIS: 0.0               # FREEZE
        }
        return multipliers.get(regime, 0.0)
    
    def detect_coin_crash(self, symbol: str, coin_df: pd.DataFrame, lookback_hours: int = 24) -> Tuple[bool, str, Dict]:
        """
        Detect if a specific coin is crashing independently of overall market.

        Args:
            symbol: Coin symbol (e.g., 'ETH/USDT')
            coin_df: DataFrame with OHLCV data for the coin (hourly recommended)
            lookback_hours: Hours to analyze for crash detection

        Returns:
            Tuple of (is_crashing, crash_reason, crash_metrics)

        Crash Detection Criteria:
        1. Flash Crash: >10% drop in single hour
        2. Sustained Crash: >20% drop in 24 hours
        3. Capitulation: >15% drop + 5x volume spike
        4. Death Spiral: Lower lows for 6+ consecutive candles with increasing volume
        """
        if len(coin_df) < lookback_hours:
            return False, "", {"error": "Insufficient data"}

        crash_metrics = {}
        current_price = float(coin_df['close'].iloc[-1])

        # 1. FLASH CRASH DETECTION (>10% in 1 hour)
        if len(coin_df) >= 2:
            prev_price = float(coin_df['close'].iloc[-2])
            hourly_change = ((current_price - prev_price) / prev_price) * 100
            crash_metrics['hourly_change_pct'] = hourly_change

            if hourly_change < -10:
                return True, f"Flash Crash: {hourly_change:.1f}% drop in 1 hour", crash_metrics

        # 2. SUSTAINED CRASH DETECTION (>20% in 24 hours)
        lookback = min(lookback_hours, len(coin_df))
        peak_24h = float(coin_df['high'].iloc[-lookback:].max())
        drawdown_24h = ((current_price - peak_24h) / peak_24h) * 100
        crash_metrics['drawdown_24h_pct'] = drawdown_24h

        if drawdown_24h < -20:
            return True, f"Sustained Crash: {drawdown_24h:.1f}% from 24h peak", crash_metrics

        # 3. CAPITULATION DETECTION (Price drop + Volume spike)
        if len(coin_df) >= 24:
            # Recent volume (last 4 hours)
            recent_volume = coin_df['volume'].iloc[-4:].mean()
            # Average volume (previous 20 hours)
            avg_volume = coin_df['volume'].iloc[-24:-4].mean()

            volume_spike = recent_volume / avg_volume if avg_volume > 0 else 1
            crash_metrics['volume_spike'] = volume_spike

            # Capitulation: >15% drop + 5x volume
            if drawdown_24h < -15 and volume_spike > 5:
                return True, f"Capitulation: {drawdown_24h:.1f}% drop + {volume_spike:.1f}x volume spike", crash_metrics

        # 4. DEATH SPIRAL DETECTION (Consecutive lower lows)
        if len(coin_df) >= 6:
            lows = coin_df['low'].iloc[-6:].values
            volumes = coin_df['volume'].iloc[-6:].values

            # Check if each low is lower than the previous
            consecutive_lower_lows = all(lows[i] < lows[i-1] for i in range(1, len(lows)))

            # Check if volume is increasing (panic selling)
            avg_vol_early = volumes[:3].mean()
            avg_vol_late = volumes[3:].mean()
            volume_increasing = avg_vol_late > avg_vol_early * 1.5

            crash_metrics['consecutive_lower_lows'] = consecutive_lower_lows
            crash_metrics['volume_increasing'] = volume_increasing

            if consecutive_lower_lows and volume_increasing:
                return True, "Death Spiral: 6+ lower lows with increasing volume", crash_metrics

        # 5. RELATIVE CRASH vs BTC (Coin drops but BTC stable)
        # This catches altcoin-specific crashes
        if 'btc_change_24h' in crash_metrics:  # If BTC data available
            btc_change = crash_metrics.get('btc_change_24h', 0)
            coin_change = drawdown_24h

            # If coin dropped >15% but BTC dropped <5%, it's a coin-specific issue
            if coin_change < -15 and btc_change > -5:
                crash_metrics['relative_crash'] = True
                return True, f"Altcoin-specific crash: {symbol} down {coin_change:.1f}% vs BTC {btc_change:.1f}%", crash_metrics

        # No crash detected
        crash_metrics['crash_detected'] = False
        return False, "", crash_metrics

    def should_trade(self, regime: RegimeState) -> bool:
        """
        Simple gate: Should we trade at all in this regime?
        
        Returns:
            True if trading allowed, False if blocked
        """
        blocked_regimes = {
            RegimeState.BEAR_CONFIRMED,
            RegimeState.CRISIS
        }
        return regime not in blocked_regimes


# Convenience function for quick checks
def detect_regime_quick(btc_df: pd.DataFrame) -> Tuple[str, float]:
    """
    Quick regime check without instantiating detector.
    
    Returns:
        Tuple of (regime_name, risk_multiplier)
    """
    detector = RegimeDetector()
    regime, confidence, _ = detector.detect_regime(btc_df)
    multiplier = detector.get_risk_multiplier(regime)
    
    return regime.value, multiplier
