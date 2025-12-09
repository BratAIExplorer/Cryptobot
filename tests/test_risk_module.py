import pytest
from decimal import Decimal
from datetime import datetime
from core.risk_module import RiskManager, RiskLimits, RiskLevel

class TestRiskModule:
    
    def test_conservative_limits(self):
        """Test that conservative mode applies strict limits."""
        limits = RiskLimits.from_risk_level(RiskLevel.CONSERVATIVE)
        assert limits.max_position_size_pct == Decimal("1.0")
        assert limits.max_daily_loss_pct == Decimal("5.0")
        assert limits.cooldown_minutes == 60

    def test_daily_loss_check(self):
        """Test daily loss limit trigger."""
        limits = RiskLimits.from_risk_level(RiskLevel.MODERATE) # 10% loss limit
        # Start with 10000
        rm = RiskManager(limits, Decimal("10000"))
        
        # Loss of 500 (5%) -> Should be fine
        rm.update_portfolio_value(Decimal("9500"))
        can_trade, reason = rm.check_daily_loss_limit()
        assert can_trade is True
        
        # Loss of 1100 (11%) -> Should trigger stop
        rm.update_portfolio_value(Decimal("8900"))
        can_trade, reason = rm.check_daily_loss_limit()
        assert can_trade is False
        assert "Daily loss limit reached" in reason

    def test_position_sizing_volatility(self):
        """Test position sizing reduction during high volatility."""
        limits = RiskLimits.from_risk_level(RiskLevel.AGGRESSIVE) # 5% base
        rm = RiskManager(limits, Decimal("10000"))
        
        # Low volatility -> Full size (5%)
        size, _ = rm.calculate_position_size(current_positions=0, market_volatility_percentile=Decimal("50"))
        assert size == Decimal("5.0")
        
        # High volatility (>90) -> Half size (2.5%)
        size, _ = rm.calculate_position_size(current_positions=0, market_volatility_percentile=Decimal("95"))
        assert size == Decimal("2.5")

    def test_consecutive_loss_cooldown(self):
        """Test that consecutive losses trigger a cooldown."""
        limits = RiskLimits.from_risk_level(RiskLevel.CONSERVATIVE) # Limit: 3 losses
        rm = RiskManager(limits, Decimal("10000"))
        
        # Record 2 losses
        rm.record_trade_result(was_profitable=False)
        rm.record_trade_result(was_profitable=False) 
        can_trade, _ = rm.check_cooldown()
        assert can_trade is True
        
        # Record 3rd loss -> Trigger cooldown
        rm.record_trade_result(was_profitable=False)
        can_trade, reason = rm.check_cooldown()
        assert can_trade is False
        assert "Trading paused" in reason
        
    def test_validate_new_trade(self):
        """Test master validation function."""
        limits = RiskLimits.from_risk_level(RiskLevel.MODERATE) # Max size 2%
        rm = RiskManager(limits, Decimal("10000"))
        
        # Check size too big
        can_trade, reason = rm.validate_new_trade("BTC", Decimal("3.0"), 0, 0)
        assert can_trade is False
        assert "exceeds limit" in reason
        
        # Check too many positions
        can_trade, reason = rm.validate_new_trade("BTC", Decimal("1.0"), 10, 0)
        assert can_trade is False
        assert "Maximum concurrent" in reason
        
        # Check valid
        can_trade, reason = rm.validate_new_trade("BTC", Decimal("1.0"), 2, 0)
        assert can_trade is True
