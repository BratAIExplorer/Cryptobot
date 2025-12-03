from .base_strategy import BaseStrategy

class VolatilityHunterStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.volatility_threshold = config.get('volatility_threshold', 0.02) # 2% move
        self.amount = config.get('amount', 10)

    def generate_signal(self, df):
        if df.empty or len(df) < 2:
            return None
            
        # Check percentage change of the last closed candle
        # (Assuming df includes the current open candle at the end, we look at -2 and -1)
        # Actually, let's look at the change from Open to Close of the last completed candle
        # OR the current rolling change. Let's use the last closed candle for stability.
        
        last_close = df['close'].iloc[-1]
        last_open = df['open'].iloc[-1]
        
        pct_change = (last_close - last_open) / last_open
        
        if abs(pct_change) > self.volatility_threshold:
            # If big move UP, maybe follow trend? Or Mean Revert?
            # "Hunter" usually implies catching the momentum.
            if pct_change > 0:
                return {
                    'side': 'BUY',
                    'amount': self.amount,
                    'reason': f"Volatility Surge: {pct_change*100:.2f}% > {self.volatility_threshold*100}%"
                }
            
        return None
