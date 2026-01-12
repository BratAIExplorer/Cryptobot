"""
CryptoBots V3 - Base Strategy Class
All strategies inherit from this base class for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Ensures consistent interface for signal generation and position management.
    """
    
    def __init__(self, name: str, config: Dict = None):
        """
        Initialize the strategy.
        
        Args:
            name: Strategy name for identification
            config: Strategy-specific configuration parameters
        """
        self.name = name
        self.config = config or {}
        self.positions = []
        self.trade_history = []
        self.enabled = True
        
    @abstractmethod
    def generate_signal(self, market_data: Dict) -> Optional[str]:
        """
        Analyze market data and generate trading signal.
        
        Args:
            market_data: Dictionary containing price, volume, indicators etc.
            
        Returns:
            'BUY', 'SELL', or None (no signal)
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, balance: float, price: float) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            balance: Available trading balance
            price: Current asset price
            
        Returns:
            Position size in base currency
        """
        pass
    
    @abstractmethod
    def check_exit_conditions(self, position: Dict, current_price: float) -> bool:
        """
        Check if a position should be exited.
        
        Args:
            position: Current position details
            current_price: Current market price
            
        Returns:
            True if position should be closed
        """
        pass
    
    def get_config(self) -> Dict:
        """Return current strategy configuration."""
        return self.config.copy()
    
    def update_config(self, new_config: Dict):
        """Update strategy configuration."""
        self.config.update(new_config)
    
    def enable(self):
        """Enable this strategy."""
        self.enabled = True
    
    def disable(self):
        """Disable this strategy."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        return self.enabled
    
    def add_trade(self, trade: Dict):
        """Record a completed trade."""
        trade['timestamp'] = datetime.now().isoformat()
        trade['strategy'] = self.name
        self.trade_history.append(trade)
    
    def get_trade_history(self) -> List[Dict]:
        """Get all trades executed by this strategy."""
        return self.trade_history.copy()
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate performance metrics for this strategy.
        
        Returns:
            Dictionary with win rate, avg profit, total trades, etc.
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_profit': 0.0
            }
        
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
        losing_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) < 0)
        total_pnl = sum(t.get('pnl', 0) for t in self.trade_history)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'total_pnl': total_pnl,
            'avg_profit': total_pnl / total_trades if total_trades > 0 else 0.0
        }
    
    def __str__(self):
        """String representation of strategy."""
        status = "ENABLED" if self.enabled else "DISABLED"
        return f"{self.name} ({status})"
    
    def __repr__(self):
        """Detailed representation of strategy."""
        return f"<{self.__class__.__name__} name='{self.name}' enabled={self.enabled}>"
