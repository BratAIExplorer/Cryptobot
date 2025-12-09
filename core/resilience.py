from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, List
import logging
from collections import deque

logger = logging.getLogger(__name__)

class ExchangeStatus(Enum):
    """Exchange connection health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Slow but functional
    STALE = "stale"        # Data too old
    DISCONNECTED = "disconnected"


@dataclass
class ExchangeHealth:
    """
    Track exchange connection health metrics.
    """
    status: ExchangeStatus
    last_heartbeat: datetime
    last_price_update: datetime
    consecutive_failures: int
    average_latency_ms: Decimal


class ExchangeResilienceManager:
    """
    Monitors exchange connectivity and handles failure scenarios.
    Prevents trading on stale data or during outages.
    """
    
    # Constants per ACAS standards
    HEARTBEAT_INTERVAL_SECONDS = 30
    STALE_DATA_THRESHOLD_SECONDS = 10
    MAX_CONSECUTIVE_FAILURES = 3
    RECONNECT_BACKOFF_SECONDS = [5, 10, 30, 60, 300]  # Exponential backoff
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.health = ExchangeHealth(
            status=ExchangeStatus.DISCONNECTED,
            last_heartbeat=datetime.min,
            last_price_update=datetime.min,
            consecutive_failures=0,
            average_latency_ms=Decimal("0")
        )
        self.latency_window = deque(maxlen=20)
        
    def update_heartbeat(self, latency_ms: Decimal) -> None:
        """
        Record successful heartbeat ping.
        """
        self.health.last_heartbeat = datetime.now()
        self.health.consecutive_failures = 0
        
        # Update rolling average latency
        self.latency_window.append(latency_ms)
        self.health.average_latency_ms = (
            sum(self.latency_window) / Decimal(str(len(self.latency_window)))
        )
        
        # Update status based on latency
        if self.health.average_latency_ms > Decimal("2000"):
            self.health.status = ExchangeStatus.DEGRADED
            logger.warning("%s performance degraded. Avg latency: %sms",
                          self.exchange_name, self.health.average_latency_ms)
        else:
            self.health.status = ExchangeStatus.HEALTHY
            
    def update_price_data(self) -> None:
        """Record that fresh price data was received."""
        self.health.last_price_update = datetime.now()
        
    def record_failure(self) -> None:
        """Record failed API request and update status."""
        self.health.consecutive_failures += 1
        
        if self.health.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            self.health.status = ExchangeStatus.DISCONNECTED
            logger.error("%s marked as DISCONNECTED after %d failures",
                        self.exchange_name, self.health.consecutive_failures)
    
    def is_data_fresh(self) -> bool:
        """
        Check if price data is recent enough for trading decisions.
        """
        if self.health.last_price_update == datetime.min:
            return False
            
        age_seconds = (datetime.now() - self.health.last_price_update).total_seconds()
        
        if age_seconds > self.STALE_DATA_THRESHOLD_SECONDS:
            if self.health.status != ExchangeStatus.STALE:
                 self.health.status = ExchangeStatus.STALE
                 logger.error("Price data is stale! Age: %.1fs (threshold: %ds)",
                            age_seconds, self.STALE_DATA_THRESHOLD_SECONDS)
            return False
        return True
    
    def can_trade(self) -> Tuple[bool, Optional[str]]:
        """
        Master check: Is exchange ready for trading?
        """
        if self.health.status == ExchangeStatus.DISCONNECTED:
            return False, f"{self.exchange_name} is disconnected"
        
        if self.health.status == ExchangeStatus.STALE:
            return False, f"{self.exchange_name} price data is stale"
        
        if not self.is_data_fresh():
            return False, f"{self.exchange_name} data not fresh"
        
        if self.health.status == ExchangeStatus.DEGRADED:
            logger.warning("Trading on degraded connection (high latency)")
        
        return True, None
    
    def get_reconnect_delay(self) -> int:
        """
        Calculate backoff delay for reconnection attempts.
        """
        attempt = min(self.health.consecutive_failures, 
                     len(self.RECONNECT_BACKOFF_SECONDS) - 1)
        return self.RECONNECT_BACKOFF_SECONDS[attempt]
