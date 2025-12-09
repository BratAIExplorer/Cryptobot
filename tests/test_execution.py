import pytest
from decimal import Decimal
import time
from datetime import datetime, timedelta
from core.execution import OrderExecutionManager, OrderStatus

class TestExecutionModule:

    def test_slippage_calculation(self):
        """Test slippage logic."""
        # Expected price 100
        oem = OrderExecutionManager("BTC", Decimal("100.00"))
        
        # Execute at 100.20 (0.2% slippage) -> OK
        res = oem.validate_execution(Decimal("1"), Decimal("1"), Decimal("100.20"))
        assert res.success is True
        assert res.slippage_pct == Decimal("0.2")

        # Execute at 101.00 (1.0% slippage) -> FAIL
        res = oem.validate_execution(Decimal("1"), Decimal("1"), Decimal("101.00"))
        assert res.success is False
        assert res.status == OrderStatus.FAILED
        assert res.slippage_pct == Decimal("1.0")

    def test_timeout_partial_fills(self):
        """Test timeout handling logic."""
        oem = OrderExecutionManager("ETH", Decimal("3000"))
        
        # Simulate 3 minutes passed (Timeout > 120s)
        oem.order_placed_at = datetime.now() - timedelta(seconds=180)
        
        # Case A: Only 10% filled -> CANCEL
        res = oem.validate_execution(Decimal("0.1"), Decimal("1.0"), Decimal("3000"))
        assert res.success is False
        assert res.status == OrderStatus.CANCELLED
        
        # Case B: 80% filled -> PARTIAL SUCCESS
        res = oem.validate_execution(Decimal("0.8"), Decimal("1.0"), Decimal("3000"))
        assert res.success is True
        assert res.status == OrderStatus.PARTIAL
        
    def test_zero_division_guard(self):
        """Ensure no crash if expected price is 0 (edge case)."""
        oem = OrderExecutionManager("FREE", Decimal("0"))
        res = oem.validate_execution(Decimal("1"), Decimal("1"), Decimal("0"))
        assert res.slippage_pct == Decimal("0")
