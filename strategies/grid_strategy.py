from .base_strategy import BaseStrategy
import numpy as np

class GridStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.grid_levels = config.get('grid_levels', 10)
        self.range_pct = config.get('range_pct', 0.1) # +/- 10%
        self.amount_per_grid = config.get('amount_per_grid', 10)
        self.grids = [] # List of price levels

    def calculate_grids(self, current_price):
        """Recalculate grid levels based on current price"""
        upper = current_price * (1 + self.range_pct)
        lower = current_price * (1 - self.range_pct)
        self.grids = np.linspace(lower, upper, self.grid_levels)

    def generate_signal(self, df):
        if df.empty:
            return None
            
        current_price = df['close'].iloc[-1]
        
        if not any(self.grids):
            self.calculate_grids(current_price)
            return None # Initial setup
            
        # Simple Grid Logic: 
        # Find closest grid level. If we are below it, BUY. If above, SELL.
        # (Real grid bots are stateful, this is a simplified version for demo)
        
        # For now, let's just use a simple mean reversion logic
        # Buy if price is in the lower half of the range, Sell if in upper half
        
        mean_price = np.mean(self.grids)
        
        if current_price < mean_price * 0.98: # 2% below mean
            return {
                'side': 'BUY',
                'amount': self.amount_per_grid,
                'reason': f"Price {current_price} < Mean {mean_price}"
            }
        elif current_price > mean_price * 1.02: # 2% above mean
            return {
                'side': 'SELL',
                'amount': self.amount_per_grid,
                'reason': f"Price {current_price} > Mean {mean_price}"
            }
            
        return None
