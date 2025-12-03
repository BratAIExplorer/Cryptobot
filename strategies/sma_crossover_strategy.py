from .base_strategy import BaseStrategy
from utils.indicators import calculate_sma, calculate_rsi

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.fast_period = config.get('fast_period', 50)
        self.slow_period = config.get('slow_period', 200)
        self.amount = config.get('amount', 100)

    def generate_signal(self, df):
        if len(df) < self.slow_period:
            return None
            
        fast_sma = calculate_sma(df['close'], self.fast_period)
        slow_sma = calculate_sma(df['close'], self.slow_period)
        
        # Check for crossover in the last candle
        prev_fast = fast_sma.iloc[-2]
        prev_slow = slow_sma.iloc[-2]
        curr_fast = fast_sma.iloc[-1]
        curr_slow = slow_sma.iloc[-1]
        
        # Golden Cross (Fast crosses above Slow)
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return {
                'side': 'BUY',
                'amount': self.amount,
                'reason': "Golden Cross (SMA 50 > SMA 200)"
            }
            
        # Death Cross (Fast crosses below Slow)
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            return {
                'side': 'SELL',
                'amount': self.amount,
                'reason': "Death Cross (SMA 50 < SMA 200)"
            }
            
        return None
