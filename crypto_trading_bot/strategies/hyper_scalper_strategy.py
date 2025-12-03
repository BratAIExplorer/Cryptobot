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
            
        # Use a very short period for RSI to be "Hyper"
        current_rsi = calculate_rsi(df['close'], period=3).iloc[-1]
        
        if current_rsi < self.rsi_limit:
            return {
                'side': 'BUY',
                'amount': self.amount,
                'reason': f"Hyper RSI {current_rsi:.2f} < {self.rsi_limit}"
            }
            
        return None
