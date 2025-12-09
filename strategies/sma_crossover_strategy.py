from .base_strategy import BaseStrategy
from utils.indicators import calculate_sma, calculate_rsi

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.fast_period = config.get('fast_period', 20)  # Standard Golden Cross: 50
        self.slow_period = config.get('slow_period', 50)  # Standard Golden Cross: 200
        self.amount = config.get('amount', 100)
        # Force Daily Timeframe (User Requirement)
        self.timeframe = '1d'

    def generate_signal(self, df):
        # Ensure we have enough data for the slow SMA + buffer
        if len(df) < self.slow_period + 5:
            return None
            
        fast_sma = calculate_sma(df['close'], self.fast_period)
        slow_sma = calculate_sma(df['close'], self.slow_period)
        
        # Check for crossover in the last candle
        prev_fast = fast_sma.iloc[-2]
        prev_slow = slow_sma.iloc[-2]
        curr_fast = fast_sma.iloc[-1]
        curr_slow = slow_sma.iloc[-1]
        
        current_price = df['close'].iloc[-1]
        
        # 1. Golden Cross (Fast crosses above Slow)
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            # FILTER: Price must be above both SMAs (Strength confirmation)
            if current_price > curr_fast and current_price > curr_slow:
                return {
                    'side': 'BUY',
                    'amount': self.amount,
                    'reason': f"Golden Cross ({self.fast_period} > {self.slow_period}) on Daily"
                }
            
        # 2. Death Cross (Fast crosses below Slow) - EXIT SIGNAL
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            return {
                'side': 'SELL',
                'amount': self.amount, # Amount logic handled by engine (sells all)
                'reason': f"Death Cross ({self.fast_period} < {self.slow_period}) on Daily"
            }
            
        return None
