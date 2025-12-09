from .base_strategy import BaseStrategy
from utils.indicators import calculate_rsi

class HyperScalperStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.rsi_limit = config.get('rsi_limit', 10) # Aggressive
        self.amount = config.get('amount', 10)
        # Note: Profit taking is handled by the Risk Manager / Engine logic usually,
        # but for this strategy, we might want to enforce a tight exit in the engine.

    def generate_signal(self, df):
        if df.empty:
            return None
            
        # 1. Volume Filter (CRITICAL: Ignore low volume noise)
        # Check if current volume is > 1.3x average of last 20 candles
        if 'volume' not in df.columns:
            # Fallback if volume datastream missing (should not happen on Binance)
            current_vol_ratio = 1.5 
        else:
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            
            if avg_volume > 0:
                current_vol_ratio = current_volume / avg_volume
            else:
                current_vol_ratio = 1.0
                
        # Filter: Skip if volume is effectively dead
        if current_vol_ratio < 1.3:
            # Log effectively handled by returning None (no signal), 
            # but in debug mode we might want to know why.
            return None

        # 2. RSI Check
        # Use configurable period (default 14 based on expert debate, but user wanted A/B testing support)
        rsi_period = self.config.get('rsi_period', 14)
        current_rsi = calculate_rsi(df['close'], period=rsi_period).iloc[-1]
        
        if current_rsi < self.rsi_limit:
            return {
                'side': 'BUY',
                'amount': self.amount,
                'reason': f"Hyper RSI({rsi_period}): {current_rsi:.2f} < {self.rsi_limit} | VolRatio: {current_vol_ratio:.2f}x"
            }
            
        return None
