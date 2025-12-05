import numpy as np
import pandas as pd

class GridStrategyV2:
    def __init__(self, config):
        self.config = config
        self.symbol = config.get('symbol', 'BTC/USDT')
        self.lower_limit = config.get('lower_limit', 90000)
        self.upper_limit = config.get('upper_limit', 105000)
        self.grid_levels = config.get('grid_levels', 20)
        self.amount_per_grid = config.get('amount', 50)
        
        # Calculate grids
        self.grids = np.linspace(self.lower_limit, self.upper_limit, self.grid_levels)
        self.grid_step = (self.upper_limit - self.lower_limit) / (self.grid_levels - 1)
        
        print(f"[GridBot] Initialized {self.symbol}: Range {self.lower_limit}-{self.upper_limit}, {self.grid_levels} grids")

    def get_signal(self, current_price, open_positions):
        """
        Determine if we should BUY or SELL based on grid levels.
        Returns:
        - {'side': 'BUY', 'price': price, 'reason': reason}
        - {'side': 'SELL', 'position_id': id, 'reason': reason}
        - None
        """
        
        # 1. Check for SELL opportunities (Profit taking)
        # Iterate through all open positions to find one that hit its target
        if not open_positions.empty:
            for _, position in open_positions.iterrows():
                buy_price = position['buy_price']
                position_id = position['id']
                
                # Target price is the next grid level above buy price
                # We add a small buffer (e.g. 0.5 * step) to ensure we clear the level
                target_price = buy_price + self.grid_step * 0.95 
                
                if current_price >= target_price:
                    return {
                        'side': 'SELL',
                        'position_id': position_id,
                        'reason': f"Grid Profit: Bought {buy_price:.2f} -> Now {current_price:.2f}"
                    }

        # 2. Check for BUY opportunities
        # Find the closest grid level below current price
        # We only buy if we don't already have a position at this level
        
        # Find grid level just below current price
        grid_idx = np.searchsorted(self.grids, current_price) - 1
        
        if grid_idx < 0:
            return None # Below range
            
        buy_level = self.grids[grid_idx]
        
        # Check if we are close enough to this level to buy (e.g. within 1% of step)
        # But in paper trading, we just buy if we crossed it downwards?
        # Simplified logic: If price is within X% of a grid level, and we don't have a position there.
        
        # Better logic:
        # We want to buy at 'buy_level'.
        # Check if we already have a position "near" this level.
        has_position = False
        if not open_positions.empty:
            for _, position in open_positions.iterrows():
                if abs(position['buy_price'] - buy_level) < (self.grid_step * 0.5):
                    has_position = True
                    break
        
        if not has_position:
            # Check if price is close to buy_level (e.g. within 0.5% tolerance)
            # or if we just crossed it. 
            # For simplicity in this engine: Buy if current_price is close to a grid line
            if abs(current_price - buy_level) < (self.grid_step * 0.2):
                return {
                    'side': 'BUY',
                    'price': current_price,
                    'reason': f"Grid Entry at {buy_level:.2f}"
                }
                
        return None
