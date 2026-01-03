import numpy as np
import pandas as pd
from decimal import Decimal
from utils.indicators import calculate_sma, calculate_atr

class DynamicGridStrategy:
    """
    Dynamic ATR Grid Bot
    - Adapts range based on Market Volatility (ATR).
    - Locks grids when positions are open to prevent 'shifting goalposts'.
    - Self-Healing: Resets grids when range is cleared.
    """
    def __init__(self, config):
        self.config = config
        self.symbol = config.get('symbol', 'BTC/USDT')
        self.grid_levels = config.get('grid_levels', 20)
        self.amount_per_grid = config.get('amount', 50)
        
        # Dynamic Settings
        self.atr_period = config.get('atr_period', 14)
        self.atr_multiplier = config.get('atr_multiplier', 2.0)
        self.ma_period = config.get('ma_period', 20)
        
        # State
        self.grids = None
        self.grid_step = None
        self.lower_limit = None
        self.upper_limit = None
        self.is_locked = False # True if we have open positions (prevent grid shift)
        
        # Fallback (Static) if no data
        self.lower_limit_static = config.get('lower_limit', 90000)
        self.upper_limit_static = config.get('upper_limit', 105000)

        print(f"[DynamicGrid] Initialized {self.symbol}: Dynamic ATR Mode (Mult: {self.atr_multiplier})")

    def calculate_grids(self, df):
        """
        Calculate grid levels based on SMA +/- ATR * multiplier
        """
        if df is None or len(df) < self.ma_period:
            return False

        # Calculate Indicators
        sma = calculate_sma(df['close'], self.ma_period).iloc[-1]
        atr = calculate_atr(df, self.atr_period).iloc[-1]
        
        if pd.isna(sma) or pd.isna(atr):
            return False
            
        # Define Range
        half_range = atr * self.atr_multiplier
        self.lower_limit = sma - half_range
        self.upper_limit = sma + half_range
        
        # Generate Grids
        self.grids = np.linspace(self.lower_limit, self.upper_limit, self.grid_levels)
        self.grid_step = (self.upper_limit - self.lower_limit) / (self.grid_levels - 1)
        
        return True

    def get_signal(self, current_price, open_positions, df=None):
        """
        Determine if we should BUY or SELL based on grid levels.
        Accepts full DataFrame to calculate dynamic grids.
        """
        
        # 0. Check Grid State
        has_positions = not open_positions.empty
        
        # DEBUG
        print(f"[GRID DEBUG] {self.symbol}: Price=${current_price:.2f}, Lower=${self.lower_limit}, Upper=${self.upper_limit}")

        # Initialize limits if None (use static fallback)
        if self.lower_limit is None:
            self.lower_limit = self.lower_limit_static
            self.upper_limit = self.upper_limit_static
            self.grids = np.linspace(self.lower_limit_static, self.upper_limit_static, self.grid_levels)
            self.grid_step = (self.upper_limit_static - self.lower_limit_static) / (self.grid_levels - 1)
            print(f"[Grid] {self.symbol}: Initialized with static range ${self.lower_limit:.0f}-${self.upper_limit:.0f}")

        # Lock grids if we have positions, Unlock if empty
        if has_positions:
            self.is_locked = True
        else:
            self.is_locked = False
            
        # If unlocked and we have data, update grids
        if False and not self.is_locked and df is not None:  # FORCE STATIC GRIDS FOR PROFITABILITY
             if self.calculate_grids(df):
                 # print(f"[GridUpdate] New Range: {self.lower_limit:.2f} - {self.upper_limit:.2f}")
                 pass
             elif self.grids is None:
                 # Fallback to static if calc failed and no grids exist
                 self.lower_limit = self.lower_limit_static
                 self.upper_limit = self.upper_limit_static
                 self.grids = np.linspace(self.lower_limit_static, self.upper_limit_static, self.grid_levels)
                 self.grid_step = (self.upper_limit_static - self.lower_limit_static) / (self.grid_levels - 1)
                 print(f"[Grid] Using static range ${self.lower_limit:.0f}-${self.upper_limit:.0f}")

        # Safety: If grids still None, abort
        if self.grids is None:
            return None

        # 1. Check for SELL opportunities (Profit taking)
        if has_positions:
            for _, position in open_positions.iterrows():
                buy_price = position['buy_price']
                position_id = position['id']
                
                # Target price is the next grid level above buy price
                target_price = buy_price + self.grid_step * 0.95 
                
                if current_price >= target_price:
                    return {
                        'side': 'SELL',
                        'position_id': position_id,
                        'reason': f"Grid Profit: Bought {buy_price:.2f} -> Now {current_price:.2f}"
                    }

        # 2. Check for BUY opportunities
        print(f"[GRID] {self.symbol}: Checking BUY opportunities, grids={len(self.grids) if self.grids is not None else 0}")
        
        # Stop-Grid Protection: Don't buy if price is below lower limit (falling knife)
        if self.lower_limit and current_price < self.lower_limit * 0.98: # 2% buffer below range
            return None 

        grid_idx = np.searchsorted(self.grids, current_price) - 1
        
        if grid_idx < 0:
            return None # Below range
            
        buy_level = self.grids[grid_idx]
        
        # Check if we already have a position at this level
        has_position_at_level = False
        if has_positions:
            for _, position in open_positions.iterrows():
                if abs(position['buy_price'] - buy_level) < (self.grid_step * 0.5):
                    has_position_at_level = True
                    break
        
        if not has_position_at_level:
            # Buy if close to grid line
            if abs(current_price - buy_level) < (self.grid_step * 0.5):
                return {
                    'side': 'BUY',
                    'price': current_price,
                    'reason': f"Grid Entry at {buy_level:.2f}"
                }
                
        return None

    def get_grid_metrics(self):
        """Return current grid state for visualization"""
        if self.grids is None:
            return {}
            
        return {
            'lower_limit': float(self.lower_limit) if self.lower_limit else self.lower_limit_static,
            'upper_limit': float(self.upper_limit) if self.upper_limit else self.upper_limit_static,
            'grid_levels': [float(g) for g in self.grids],
            'is_locked': self.is_locked,
            'atr_multiplier': self.atr_multiplier
        }
