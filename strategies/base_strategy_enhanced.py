from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging
from core.interfaces.base_adapter import BaseExchangeAdapter

logger = logging.getLogger(__name__)

class BaseStrategyEnhanced(ABC):
    """
    Enhanced Base Strategy.
    Decouples strategy logic from specific exchanges using the Adapter Pattern.
    """

    def __init__(self, name: str, adapter: BaseExchangeAdapter, config: Dict[str, Any], trade_logger=None):
        self.name = name
        self.adapter = adapter
        self.config = config
        self.symbol = config.get('symbol')
        self.logger = logger # System logger
        self.trade_logger = trade_logger # DB logger
        
    def check_safety(self) -> bool:
        """
        Global safety check before any logic.
        """
        if self.adapter.kill_switch_active:
            self.logger.warning(f"🛑 {self.name}: Skipped (Kill Switch Active)")
            return False
        return True

    def get_current_price(self) -> Optional[float]:
        return self.adapter.get_current_price(self.symbol)

    def place_order(self, side: str, amount: float, price: Optional[float] = None, order_type: str = 'limit', **kwargs) -> Optional[Dict]:
        """
        Unified order placement wrapper.
        Accepts kwargs for logging (e.g. rsi=30.5).
        """
        if not self.check_safety():
            return None
            
        self.logger.info(f"ORDERS: {self.name} placing {side} {amount} {self.symbol} @ {price}")
        result = self.adapter.create_order(self.symbol, side, amount, price)
        
        if result and self.trade_logger:
            # Log to Database
            self.trade_logger.log_trade(
                strategy=self.name,
                symbol=self.symbol,
                side=side,
                price=price or result.get('price', 0),
                amount=amount,
                fee=0.0, 
                rsi=kwargs.get('rsi'), # Capture RSI from kwargs
                market_condition=kwargs.get('reason', ''),
                exchange=self.adapter.exchange_name
            )
        return result

    @abstractmethod
    def run_iteration(self):
        """
        Core strategy logic to be implemented by child classes.
        """
        pass
    
    def on_stop(self):
        """Cleanup hook"""
        pass
