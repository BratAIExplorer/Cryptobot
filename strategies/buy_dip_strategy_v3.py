"""
CryptoBots V3 - Buy @ DIP Strategy
Buys when price drops X% below recent 24h high.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy


class BuyDipStrategy(BaseStrategy):
    """
    Buy the Dip Strategy
    
    Logic:
    - Monitor 24h high price
    - Buy when price drops X% below that high
    - Limit: Max 1 buy per cooldown period (default 4 hours)
    
    Configurable Parameters:
    - dip_percentage: % drop to trigger buy (default: 5%)
    - cooldown_hours: Hours between buys (default: 4)
    - position_size_percent: % of balance per trade (default: 10%)
    - stop_loss_percent: Stop loss % (default: 2%)
    """
    
    def __init__(self, config: Dict = None):
        default_config = {
            'name': 'Buy @ DIP',         # Strategy name
            'dip_percentage': 5.0,      # Buy at 5% dip
            'cooldown_hours': 4,         # 4 hour cooldown
            'position_size_percent': 10.0,  # Use 10% of balance
            'stop_loss_percent': 2.0     # 2% stop loss
        }

        if config:
            default_config.update(config)

        super().__init__(config=default_config)
        self.last_buy_time = None
        self.high_24h = None
    
    def generate_signal(self, market_data: Dict) -> Optional[str]:
        """
        Generate buy signal when price dips.
        
        market_data should contain:
        - current_price: Current market price
        - high_24h: 24-hour high price
        - timestamp: Current timestamp
        """
        if not self.enabled:
            return None
        
        current_price = market_data.get('current_price')
        high_24h = market_data.get('high_24h')
        
        if not current_price or not high_24h:
            return None
        
        # Update 24h high
        self.high_24h = high_24h
        
        # Check cooldown period
        if self.last_buy_time:
            cooldown = timedelta(hours=self.config['cooldown_hours'])
            if datetime.now() - self.last_buy_time < cooldown:
                return None
        
        # Calculate current dip percentage
        dip_percent = ((high_24h - current_price) / high_24h) * 100
        
        # Check if dip threshold is met
        if dip_percent >= self.config['dip_percentage']:
            self.last_buy_time = datetime.now()
            return 'BUY'
        
        return None
    
    def calculate_position_size(self, balance: float, price: float) -> float:
        """
        Calculate position size based on percentage of balance.
        
        Args:
            balance: Available trading balance (USDT)
            price: Current asset price
            
        Returns:
            Position size in base currency (e.g., BTC amount)
        """
        position_value = balance * (self.config['position_size_percent'] / 100)
        position_size = position_value / price
        return position_size
    
    def check_exit_conditions(self, position: Dict, current_price: float) -> bool:
        """
        Check if position should be closed (stop loss hit).
        
        Args:
            position: Dict with 'entry_price', 'size', etc.
            current_price: Current market price
            
        Returns:
            True if stop loss triggered
        """
        entry_price = position.get('entry_price')
        if not entry_price:
            return False
        
        # Calculate current loss percentage
        loss_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Close if stop loss hit
        if loss_percent >= self.config['stop_loss_percent']:
            return True
        
        return False
    
    def get_strategy_info(self) -> Dict:
        """Get human-readable strategy information."""
        return {
            'name': self.name,
            'description': f"Buy when price drops {self.config['dip_percentage']}% from 24h high",
            'config': {
                'Dip Trigger': f"{self.config['dip_percentage']}%",
                'Cooldown': f"{self.config['cooldown_hours']} hours",
                'Position Size': f"{self.config['position_size_percent']}% of balance",
                'Stop Loss': f"{self.config['stop_loss_percent']}%"
            },
            'status': 'ENABLED' if self.enabled else 'DISABLED',
            'last_buy': self.last_buy_time.isoformat() if self.last_buy_time else 'Never'
        }
