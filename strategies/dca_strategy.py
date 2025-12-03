from .base_strategy import BaseStrategy
from utils.indicators import calculate_rsi

class DCAStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.rsi_limit = config.get('rsi_limit', 40)
        self.amount = config.get('amount', 10) # USD amount

    def generate_signal(self, df):
        if df.empty:
            return None
            
        current_rsi = calculate_rsi(df['close']).iloc[-1]
        
        # Logic: Buy if RSI is low (Buy the dip)
        if current_rsi < self.rsi_limit:
            return {
                'side': 'BUY',
                'amount': self.amount, # In USD, engine converts to units
                'reason': f"RSI {current_rsi:.2f} < {self.rsi_limit}"
            }
            
        return None
