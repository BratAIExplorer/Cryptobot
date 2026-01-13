"""
CryptoBots V3 - Trend Following Strategy
Uses moving average crossovers to follow market trends.
"""

from typing import Dict, Optional, List
from .base_strategy import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    Simple Trend Following Strategy
    
    Logic:
    - Golden Cross (fast MA > slow MA) = BUY signal
    - Death Cross (fast MA < slow MA) = SELL signal
    - Max drawdown limit to protect capital
    
    Configurable Parameters:
    - fast_ma_period: Fast MA period (default: 50)
    - slow_ma_period: Slow MA period (default: 200)
    - max_drawdown_percent: Max acceptable drawdown (default: 5%)
    - position_size_percent: % of balance per trade (default: 15%)
    """
    
    def __init__(self, config: Dict = None):
        default_config = {
            'fast_ma_period': 50,           # 50-period MA
            'slow_ma_period': 200,          # 200-period MA
            'max_drawdown_percent': 5.0,    # 5% max drawdown
            'position_size_percent': 15.0   # Use 15% of balance
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="Trend Following", config=default_config)
        self.last_signal = None
        self.peak_balance = None
    
    def generate_signal(self, market_data: Dict) -> Optional[str]:
        """
        Generate trading signal based on MA crossover.
        
        market_data should contain:
        - fast_ma: Fast moving average value
        - slow_ma: Slow moving average value
        - prices: List of recent prices (optional, for calculating MA)
        """
        if not self.enabled:
            return None
        
        # Option 1: Pre-calculated MAs provided
        fast_ma = market_data.get('fast_ma')
        slow_ma = market_data.get('slow_ma')
        
        # Option 2: Calculate MAs from price history
        if fast_ma is None or slow_ma is None:
            prices = market_data.get('prices', [])
            if len(prices) >= self.config['slow_ma_period']:
                fast_ma = self._calculate_sma(prices, self.config['fast_ma_period'])
                slow_ma = self._calculate_sma(prices, self.config['slow_ma_period'])
        
        if fast_ma is None or slow_ma is None:
            return None  # Not enough data
        
        # Detect crossover
        signal = None
        
        # Golden Cross: Fast MA crosses above Slow MA (bullish)
        if fast_ma > slow_ma:
            if self.last_signal != 'BUY':
                signal = 'BUY'
                self.last_signal = 'BUY'
        
        # Death Cross: Fast MA crosses below Slow MA (bearish)
        elif fast_ma < slow_ma:
            if self.last_signal != 'SELL':
                signal = 'SELL'
                self.last_signal = 'SELL'
        
        return signal
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: List of prices (most recent last)
            period: Number of periods for MA
            
        Returns:
            Moving average value
        """
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        return sum(recent_prices) / period
    
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
        Check if position should be closed based on drawdown.
        
        Args:
            position: Dict with 'entry_price', 'balance', etc.
            current_price: Current market price
            
        Returns:
            True if max drawdown exceeded
        """
        entry_price = position.get('entry_price')
        
        if not entry_price:
            return False
        
        # Calculate current drawdown
        drawdown_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Close if max drawdown exceeded
        if drawdown_percent >= self.config['max_drawdown_percent']:
            return True
        
        return False
    
    def check_portfolio_drawdown(self, current_balance: float) -> bool:
        """
        Check if portfolio drawdown limit is exceeded.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if max drawdown exceeded
        """
        # Track peak balance
        if self.peak_balance is None or current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        if self.peak_balance is None:
            return False
        
        # Calculate portfolio drawdown
        drawdown_percent = ((self.peak_balance - current_balance) / self.peak_balance) * 100
        
        return drawdown_percent >= self.config['max_drawdown_percent']
    
    def get_ma_info(self, market_data: Dict) -> Dict:
        """
        Get current moving average information.
        
        Args:
            market_data: Market data with prices or pre-calculated MAs
            
        Returns:
            Dictionary with MA values and trend direction
        """
        fast_ma = market_data.get('fast_ma')
        slow_ma = market_data.get('slow_ma')
        
        if fast_ma is None or slow_ma is None:
            prices = market_data.get('prices', [])
            if len(prices) >= self.config['slow_ma_period']:
                fast_ma = self._calculate_sma(prices, self.config['fast_ma_period'])
                slow_ma = self._calculate_sma(prices, self.config['slow_ma_period'])
        
        if fast_ma and slow_ma:
            trend = 'BULLISH' if fast_ma > slow_ma else 'BEARISH'
            gap_percent = abs((fast_ma - slow_ma) / slow_ma * 100)
        else:
            trend = 'UNKNOWN'
            gap_percent = 0
        
        return {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma,
            'fast_period': self.config['fast_ma_period'],
            'slow_period': self.config['slow_ma_period'],
            'trend': trend,
            'gap_percent': f"{gap_percent:.2f}%",
            'last_signal': self.last_signal or 'NONE'
        }
    
    def get_strategy_info(self) -> Dict:
        """Get human-readable strategy information."""
        return {
            'name': self.name,
            'description': f"Follow trends using {self.config['fast_ma_period']}/{self.config['slow_ma_period']} MA crossover",
            'config': {
                'Fast MA': f"{self.config['fast_ma_period']} periods",
                'Slow MA': f"{self.config['slow_ma_period']} periods",
                'Max Drawdown': f"{self.config['max_drawdown_percent']}%",
                'Position Size': f"{self.config['position_size_percent']}% of balance"
            },
            'status': 'ENABLED' if self.enabled else 'DISABLED',
            'last_signal': self.last_signal or 'NONE',
            'peak_balance': f"${self.peak_balance:,.2f}" if self.peak_balance else "Not set"
        }
