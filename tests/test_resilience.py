import pytest
import time
from decimal import Decimal
from datetime import datetime
from core.resilience import ExchangeResilienceManager, ExchangeStatus

class TestResilienceModule:
    
    def test_heartbeat_updates_status(self):
        """Test that heartbeats update status and latency."""
        erm = ExchangeResilienceManager("Binance")
        assert erm.health.status == ExchangeStatus.DISCONNECTED
        
        # Good heartbeat (100ms)
        erm.update_heartbeat(Decimal("100"))
        assert erm.health.status == ExchangeStatus.HEALTHY
        assert erm.health.average_latency_ms == Decimal("100")
        
        # Slow heartbeat (2500ms) -> Degraded
        erm.update_heartbeat(Decimal("2500"))
        # Avg = (100 + 2500) / 2 = 1300 -- Still Healthy avg < 2000
        assert erm.health.status == ExchangeStatus.HEALTHY
        
        # Another slow one
        erm.update_heartbeat(Decimal("4000"))
        # Avg ~ 2200 -> Degraded
        assert erm.health.status == ExchangeStatus.DEGRADED

    def test_stale_data_detection(self):
        """Test that trading is blocked if data is old."""
        erm = ExchangeResilienceManager("Luno")
        erm.update_heartbeat(Decimal("50"))
        erm.update_price_data()
        
        # Fresh data
        assert erm.is_data_fresh() is True
        can_trade, _ = erm.can_trade()
        assert can_trade is True
        
        # Simulate time passing (we can't easily wait 10s in unit test, 
        # so we'll manipulate the last_update time)
        erm.health.last_price_update = datetime.min
        
        assert erm.is_data_fresh() is False
        can_trade, reason = erm.can_trade()
        assert can_trade is False
        assert "data not fresh" in reason

    def test_consecutive_failures_disconnect(self):
        """Test that 3 failures triggers DISCONNECTED state."""
        erm = ExchangeResilienceManager("Kraken")
        erm.update_heartbeat(Decimal("50"))
        assert erm.health.status == ExchangeStatus.HEALTHY
        
        erm.record_failure()
        assert erm.health.status == ExchangeStatus.HEALTHY # 1/3
        
        erm.record_failure()
        assert erm.health.status == ExchangeStatus.HEALTHY # 2/3
        
        erm.record_failure()
        assert erm.health.status == ExchangeStatus.DISCONNECTED # 3/3
        
        can_trade, reason = erm.can_trade()
        assert can_trade is False
        assert "disconnected" in reason

    def test_backoff_calculator(self):
        """Verify exponential backoff values."""
        erm = ExchangeResilienceManager("Test")
        
        erm.health.consecutive_failures = 0
        assert erm.get_reconnect_delay() == 5
        
        erm.health.consecutive_failures = 1
        assert erm.get_reconnect_delay() == 10
        
        erm.health.consecutive_failures = 4
        assert erm.get_reconnect_delay() == 300 # Max cap
