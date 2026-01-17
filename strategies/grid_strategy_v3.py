import numpy as np
import pandas as pd
from decimal import Decimal
from typing import Dict, Any, Optional
from utils.indicators import calculate_sma, calculate_atr
from .base_strategy_enhanced import BaseStrategyEnhanced
from core.interfaces.base_adapter import BaseExchangeAdapter

class GridStrategyV3(BaseStrategyEnhanced):
    """
    Grid Bot V3 (Adapter Pattern)
    - Ported from DynamicGridStrategy
    - Logic: Dynamic ATR Grid
    - Execution: self.place_order() via Adapter
    """
    
    def __init__(self, name: str, adapter: BaseExchangeAdapter, config: Dict[str, Any]):
        super().__init__(name, adapter, config)
        
        # Grid Settings
        self.grid_levels = config.get('grid_levels', 20)
        self.amount_per_grid = config.get('amount', 50)
        self.limit_step_pct = 0.95 # Sell target is 95% of step to ensure fill
        
        # Dynamic Settings
        self.atr_period = config.get('atr_period', 14)
        self.atr_multiplier = config.get('atr_multiplier', 2.0)
        self.ma_period = config.get('ma_period', 20)
        
        # State
        self.grids = None
        self.grid_step = None
        self.lower_limit = None
        self.upper_limit = None
        self.is_locked = False 
        
        # Fallback (Static)
        self.lower_limit_static = config.get('lower_limit', 90000)
        self.upper_limit_static = config.get('upper_limit', 105000)
        
        self.logger.info(f"[{self.name}] Initialized Grid V3 for {self.symbol}")

    def calculate_grids(self, df: pd.DataFrame) -> bool:
        """Calculate dynamic grid levels based on SMA +/- ATR"""
        if df is None or len(df) < self.ma_period: return False

        # Indicators
        sma = calculate_sma(df['close'], self.ma_period).iloc[-1]
        atr = calculate_atr(df, self.atr_period).iloc[-1]
        
        if pd.isna(sma) or pd.isna(atr): return False
            
        # Range
        half_range = atr * self.atr_multiplier
        self.lower_limit = sma - half_range
        self.upper_limit = sma + half_range
        
        # Construct Grids
        self.grids = np.linspace(self.lower_limit, self.upper_limit, self.grid_levels)
        self.grid_step = (self.upper_limit - self.lower_limit) / (self.grid_levels - 1)
        return True

    def initialize_grids_static(self):
        """Fallback to static grids"""
        self.lower_limit = self.lower_limit_static
        self.upper_limit = self.upper_limit_static
        self.grids = np.linspace(self.lower_limit, self.upper_limit, self.grid_levels)
        self.grid_step = (self.upper_limit - self.lower_limit) / (self.grid_levels - 1)
        self.logger.info(f"[{self.name}] Using static range ${self.lower_limit:.0f}-${self.upper_limit:.0f}")

    def run_iteration(self):
        """
        Main Loop: Fetch Data -> Analyze -> Execute
        """
        # 1. Fetch Data
        df = self.adapter.fetch_ohlcv(self.symbol, timeframe='1h', limit=50)
        if df.empty:
            self.logger.warning(f"[{self.name}] No data for {self.symbol}")
            return

        current_price = df['close'].iloc[-1]

        # 2. Get Open Positions (needs Logger or Adapter to support this)
        # Note: Adapter currently creates orders but Logger tracks them.
        # Ideally, Adapter should facilitate retrieval, or we pass Logger to Strategy.
        # For V3 Clean Architecture, Strategy should query Adapter for "open orders" or "positions".
        # However, our system tracks "positions" in SQL DB (TradeLogger).
        # We might need to inject `trade_logger` into this class or use adapter to fetch from exchange.
        # For now, let's assume `open_positions` is passed via `run_iteration` or injected.
        # CRITICAL: `BaseStrategyEnhanced` doesn't have `self.logger_db`.
        # I will inject it for now to match V2 parity.
        # ACTUALLY: Engine passes data.
        pass

    # For now, let's implement get_signal to keep Engine compatibility during transition.
    # The Engine will call strategy.get_signal() and then Engine executes.
    # This allows step-by-step migration.
    
    def get_signal(self, current_price: float, open_positions: pd.DataFrame, df: pd.DataFrame = None) -> Optional[Dict]:
        """
        V2-Compatible Signal Logic
        """
        has_positions = not open_positions.empty

        # Initialize grids if needed
        if self.grids is None:
            self.initialize_grids_static()

        # Lock logic - FIXED: Allow multiple concurrent positions (pyramiding)
        # Previous: Locked after ANY position (limited to 1 position)
        # New: Allow up to max_concurrent_positions (default 10)
        max_concurrent = self.config.get('max_concurrent_positions', 10)
        self.is_locked = len(open_positions) >= max_concurrent

        # 1. SELL Logic (Profit Taking)
        if has_positions:
            for _, position in open_positions.iterrows():
                target = position['buy_price'] + self.grid_step * self.limit_step_pct
                if current_price >= target:
                    return {
                        'side': 'SELL',
                        'position_id': position['id'],
                        'reason': f"Grid Profit: {position['buy_price']:.2f} -> {current_price:.2f}"
                    }

        # 2. BUY Logic (Entry)
        if self.lower_limit and current_price < self.lower_limit * 0.98:
            return None # Stop-Grid (Falling Knife)

        if self.grids is None: return None
        
        grid_idx = np.searchsorted(self.grids, current_price) - 1
        if grid_idx < 0: return None
        
        buy_level = self.grids[grid_idx]
        
        # Check existing overlap
        if has_positions:
            for _, pos in open_positions.iterrows():
                if abs(pos['buy_price'] - buy_level) < (self.grid_step * 0.5):
                    return None # Already have position here
        
        # Buy condition
        if abs(current_price - buy_level) < (self.grid_step * 0.5):
            return {
                'side': 'BUY',
                'price': current_price,
                'reason': f"Grid Entry at {buy_level:.2f}"
            }
            
        return None

    def get_grid_metrics(self):
        """Visualization Metadata"""
        if self.grids is None: return {}
        return {
            'lower_limit': float(self.lower_limit),
            'upper_limit': float(self.upper_limit),
            'grid_levels': [float(g) for g in self.grids],
            'is_locked': self.is_locked
        }
