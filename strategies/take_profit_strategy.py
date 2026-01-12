"""
CryptoBots V3 - Take Profit Strategy
Exits positions at target profit with trailing stop.
"""

from typing import Dict, Optional
from .base_strategy import BaseStrategy


class TakeProfitStrategy(BaseStrategy):
    """
    Take Profit + Trailing Stop Strategy
    
    Logic:
    - Set a profit target (e.g., 3%)
    - Once target hit, activate trailing stop
    - Trail by X% (e.g., 1%) to lock in gains
    - Always have a maximum stop loss (e.g., -2%)
    
    Configurable Parameters:
    - profit_target_percent: Profit target % (default: 3%)
    - trailing_stop_percent: Trailing stop % (default: 1%)
    - stop_loss_percent: Maximum loss % (default: 2%)
    - position_size_percent: % of balance per trade (default: 10%)
    """
    
    def __init__(self, config: Dict = None):
        default_config = {
            'profit_target_percent': 3.0,    # 3% profit target
            'trailing_stop_percent': 1.0,    # 1% trailing stop
            'stop_loss_percent': 2.0,        # 2% max loss
            'position_size_percent': 10.0    # Use 10% of balance
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="Take Profit", config=default_config)
        self.highest_price_since_entry = {}  # Track highest price per position
    
    def generate_signal(self, market_data: Dict) -> Optional[str]:
        """
        This strategy is primarily for exits, not entries.
        Use in combination with other entry strategies.
        
        Returns None as this doesn't generate entry signals.
        """
        return None
    
    def calculate_position_size(self, balance: float, price: float) -> float:
        """
        Calculate position size based on percentage of balance.
        
        Args:
            balance: Available trading balance (USDT)
            price: Current asset price
            
        Returns:
            Position size in base currency
        """
        position_value = balance * (self.config['position_size_percent'] / 100)
        position_size = position_value / price
        return position_size
    
    def check_exit_conditions(self, position: Dict, current_price: float) -> bool:
        """
        Check if position should be closed based on profit target or stops.
        
        Args:
            position: Dict with 'entry_price', 'position_id', etc.
            current_price: Current market price
            
        Returns:
            True if position should be closed
        """
        entry_price = position.get('entry_price')
        position_id = position.get('position_id', 'default')
        
        if not entry_price:
            return False
        
        # Track highest price since entry
        if position_id not in self.highest_price_since_entry:
            self.highest_price_since_entry[position_id] = entry_price
        
        if current_price > self.highest_price_since_entry[position_id]:
            self.highest_price_since_entry[position_id] = current_price
        
        # Calculate profit/loss percentages
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        loss_percent = ((entry_price - current_price) / entry_price) * 100
        
        # 1. Check stop loss (maximum loss)
        if loss_percent >= self.config['stop_loss_percent']:
            self._cleanup_position(position_id)
            return True
        
        # 2. Check if profit target reached
        if profit_percent >= self.config['profit_target_percent']:
            # Activate trailing stop
            highest = self.highest_price_since_entry[position_id]
            drop_from_high = ((highest - current_price) / highest) * 100
            
            if drop_from_high >= self.config['trailing_stop_percent']:
                self._cleanup_position(position_id)
                return True
        
        return False
    
    def _cleanup_position(self, position_id: str):
        """Remove position tracking data."""
        if position_id in self.highest_price_since_entry:
            del self.highest_price_since_entry[position_id]
    
    def get_trailing_info(self, position: Dict, current_price: float) -> Dict:
        """
        Get trailing stop information for a position.
        
        Args:
            position: Position details
            current_price: Current market price
            
        Returns:
            Dictionary with trailing stop metrics
        """
        entry_price = position.get('entry_price')
        position_id = position.get('position_id', 'default')
        
        if not entry_price:
            return {}
        
        highest = self.highest_price_since_entry.get(position_id, entry_price)
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        drop_from_high = ((highest - current_price) / highest) * 100
        
        trailing_active = profit_percent >= self.config['profit_target_percent']
        
        return {
            'entry_price': entry_price,
            'current_price': current_price,
            'highest_price': highest,
            'current_profit': f"{profit_percent:+.2f}%",
            'drop_from_high': f"{drop_from_high:.2f}%",
            'trailing_active': trailing_active,
            'profit_target': f"{self.config['profit_target_percent']}%",
            'trailing_trigger': f"{self.config['trailing_stop_percent']}%"
        }
    
    def get_strategy_info(self) -> Dict:
        """Get human-readable strategy information."""
        return {
            'name': self.name,
            'description': f"Exit at {self.config['profit_target_percent']}% profit with {self.config['trailing_stop_percent']}% trailing stop",
            'config': {
                'Profit Target': f"{self.config['profit_target_percent']}%",
                'Trailing Stop': f"{self.config['trailing_stop_percent']}%",
                'Max Stop Loss': f"{self.config['stop_loss_percent']}%",
                'Position Size': f"{self.config['position_size_percent']}% of balance"
            },
            'status': 'ENABLED' if self.enabled else 'DISABLED',
            'active_positions': len(self.highest_price_since_entry)
        }
