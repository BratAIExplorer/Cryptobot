"""
CryptoBots V3 - Trading Strategies Package
"""

from .base_strategy import BaseStrategy
from .buy_dip_strategy import BuyDipStrategy
from .take_profit_strategy import TakeProfitStrategy
from .trend_following_strategy import TrendFollowingStrategy

__all__ = [
    'BaseStrategy',
    'BuyDipStrategy',
    'TakeProfitStrategy',
    'TrendFollowingStrategy'
]
