from typing import Dict, Any, Optional
import pandas as pd
from .base_strategy_enhanced import BaseStrategyEnhanced
from core.interfaces.base_adapter import BaseExchangeAdapter
from utils.indicators import calculate_rsi

class DipStrategyV3(BaseStrategyEnhanced):
    """
    Buy-the-Dip Strategy V3 (Adapter Pattern)
    - Logic: Buy on RSI dips if Market Regime is Bullish/Sideways
    - Exit: Target Profit (5-10%) covering Fees.
    - Integrated with Regime Detector (injected)
    """
    
    def __init__(self, name: str, adapter: BaseExchangeAdapter, config: Dict[str, Any], regime_detector=None):
        super().__init__(name, adapter, config)
        self.regime_detector = regime_detector
        self.rsi_limit = config.get('rsi_limit', 30)
        self.dip_threshold = config.get('dip_threshold', 0.05)
        
        # User Requirement: 5-10% Profit
        self.target_profit_pct = config.get('take_profit_pct', 0.08) # Default 8%
        
    def run_iteration(self, btc_df_macro=None):
        """
        1. Check Regime (Macro)
        2. Check Coin RSI (Micro)
        3. Execute Buy
        """
        # 1. Regime Check
        if not self.check_safety(): return

        can_trade = True
        if self.regime_detector and btc_df_macro is not None:
             regime, conf, _ = self.regime_detector.detect_regime(btc_df_macro)
             if str(regime) == 'BEAR':
                 self.logger.info(f"[{self.name}] Skipped: Bear Market Regime")
                 can_trade = False
        
        if not can_trade: return

        # 2. Fetch Data
        df = self.adapter.fetch_ohlcv(self.symbol, timeframe='1h', limit=50)
        if df.empty: return
        
        current_price = df['close'].iloc[-1]
        rsi = calculate_rsi(df['close']).iloc[-1]
        
        # 3. Buy Logic
        if rsi < self.rsi_limit:
             reason = f"RSI Dip: {rsi:.1f} < {self.rsi_limit}"
             self.place_order('BUY', self.config.get('amount', 20), current_price, rsi=rsi, reason=reason)
             
    def check_exit(self, position: Dict, current_price: float) -> Optional[Dict]:
        """
        Check for exit conditions ensuring NET profit calls.
        """
        buy_price = position['buy_price']
        
        # Estimate Fees (0.1% Buy + 0.1% Sell)
        # We want Pure Profit > target_profit_pct
        # Formula: SellPrice = BuyPrice * (1 + 2*Fee + Margin)
        fee_rate = 0.001
        required_margin = self.target_profit_pct
        target_price = buy_price * (1 + (2 * fee_rate) + required_margin)
        
        if current_price >= target_price:
            profit_pct = ((current_price - buy_price) / buy_price) * 100
            return {
                'side': 'SELL',
                'price': current_price,
                'reason': f"Target Hit: {profit_pct:.1f}% (Net > {self.target_profit_pct*100}%)"
            }
            
        return None

    def get_signal(self, current_price: float, open_positions: pd.DataFrame, df: pd.DataFrame = None, **kwargs) -> Optional[Dict]:
        """V2 Compatible Signal Getter"""
        
        # EXIT CHECK
        if not open_positions.empty:
            for _, pos in open_positions.iterrows():
                exit_signal = self.check_exit(pos, current_price)
                if exit_signal:
                    exit_signal['position_id'] = pos['id']
                    return exit_signal
        
        # BUY CHECK
        try:
             rsi = calculate_rsi(df['close']).iloc[-1]
        except:
             return None
             
        # Only buy if no open position (Simple Mode for now, or averaging down?)
        # User said "No Losses", so maybe averaging down is better? 
        # For V3 MVP, we do 1 position per coin or respect max_exposure.
        
        if rsi < self.rsi_limit:
             return {
                 'side': 'BUY',
                 'price': current_price,
                 'reason': f"RSI Dip {rsi:.1f}"
             }
        return None
