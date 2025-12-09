import pytest
from decimal import Decimal
from core.risk_manager import RiskManager

class TestFinancialLogic:
    def test_precision_math(self):
        """
        Test that Decimal handles floating point artifacts correctly.
        Case: 0.1 + 0.1 + 0.1 - 0.3 should be EXACTLY 0.
        """
        # Float fail case (reference only, not asserting)
        f_res = 0.1 + 0.1 + 0.1 - 0.3
        # In float architecture this is usually 5.55e-17, not 0
        
        # Decimal success case
        d1 = Decimal('0.1')
        d_res = d1 + d1 + d1 - Decimal('0.3')
        assert d_res == Decimal('0'), f"Decimal precision failed! Got {d_res}"

    def test_risk_manager_profit_calc(self):
        """
        Verify check_profit_guard handles fees with high precision.
        """
        # 0.1% fee, 0.5% min profit
        rm = RiskManager(min_profit_pct=0.5, fee_rate=0.001)
        
        # Buy at 100
        buy_price = Decimal('100.00')
        # Cost = 100 * 1.001 = 100.10
        
        # Sell at 101
        sell_price = Decimal('101.00')
        # Proceeds = 101 * 0.999 = 100.899
        
        # Profit = 100.899 - 100.10 = 0.799
        # Return = 0.799 / 100.10 ~= 0.798%
        
        is_prof, actual_pct = rm.check_profit_guard(sell_price, buy_price)
        
        assert is_prof is True
        # Check strict decimal value
        expected_profit = (Decimal('101') * Decimal('0.999')) - (Decimal('100') * Decimal('1.001'))
        expected_pct = (expected_profit / (Decimal('100') * Decimal('1.001'))) * 100
        
        assert actual_pct == expected_pct

    def test_drawdown_precision(self):
        """
        Test heavy drawdown decimals
        """
        rm = RiskManager(max_drawdown_pct=0.10) # 10%
        
        # Start 1000
        rm.check_drawdown_limit(Decimal('1000'), None)
        
        # Drop to 899.99 (Drawdown > 10%)
        # Drawdown = (1000 - 899.99) / 1000 = 100.01 / 1000 = 10.001%
        can_trade, dd_pct = rm.check_drawdown_limit(Decimal('899.99'), None)
        
        assert can_trade is False
        assert dd_pct > Decimal('10.0')

    def test_input_sanitization(self):
        """
        Ensure RiskManager accepts floats in __init__ but converts to Decimal internally
        """
        rm = RiskManager(min_profit_pct=0.5)
        assert isinstance(rm.min_profit_pct, Decimal)
