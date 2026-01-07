from abc import ABC, abstractmethod
from decimal import Decimal
import pandas as pd
from typing import Dict, Any, Optional, List
from ..health_monitor import ExchangeHealthMonitor

class BaseExchangeAdapter(ABC):
    """
    Abstract Base Class for all Exchange Adapters.
    """

    def __init__(self, mode: str = 'paper'):
        self.mode = mode.lower()
        self.kill_switch_active = False
        self.exchange_name = "BASE"
        # Initialize Health Monitor but DON'T start it yet
        # Child class must call self.health_monitor.start() AFTER initializing self.exchange
        self.health_monitor = None  # Will be initialized by child

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Fetch current price for a symbol"""
        pass

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data as DataFrame"""
        pass

    @abstractmethod
    def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Create an order.
        Must respect self.kill_switch_active status.
        Returns dict with keys: id, symbol, side, amount, price, status, exchange, mode
        """
        pass

    @abstractmethod
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get balance for specific currency"""
        pass
    
    @abstractmethod
    def get_fee_rate(self, symbol: str, order_type: str = 'taker') -> float:
        """Get Fee rate (e.g. 0.001 for 0.1%)"""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """
        Check connectivity and latency.
        Delegate to health monitor if active.
        """
        if self.health_monitor.is_running:
            return self.health_monitor.get_stats()
        # Fallback for manual check if monitor not started
        return {'status': 'UNKNOWN', 'warning': 'Monitor not started'}

    def trigger_kill_switch(self, reason: str):
        """Active the Kill Switch to block all new orders"""
        self.kill_switch_active = True
        print(f"🛑 KILL SWITCH ACTIVATED for {self.exchange_name}: {reason}")

    def reset_kill_switch(self):
        """Reset the Kill Switch (Manual intervention usually required)"""
        self.kill_switch_active = False
        print(f"✅ KILL SWITCH RESET for {self.exchange_name}")

    def shutdown(self):
        """Graceful cleanup"""
        if self.health_monitor:
            self.health_monitor.stop()
