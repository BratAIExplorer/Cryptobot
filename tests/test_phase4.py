"""
Test Script for Phase 4: Correlation Manager
Verifies that the Risk Manager correctly blocks trades based on correlation.
"""
import sys
import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.risk_module import RiskManager, RiskLimits, RiskLevel
from core.correlation import CorrelationManager

class TestPhase4(unittest.TestCase):
    def setUp(self):
        # Setup Risk Manager with Aggressive limits (allows more positions usually)
        limits = RiskLimits.from_risk_level(RiskLevel.AGGRESSIVE)
        self.risk_manager = RiskManager(limits, portfolio_value=Decimal("50000"))
        
        # Mock Correlation Manager to avoid real API calls
        self.risk_manager.correlation_manager = MagicMock()

    def test_correlation_block(self):
        """Test that high correlation blocks a trade"""
        # Scenario: User holds BTC, wants to buy ETH.
        # Correlation Manager says they are 95% correlated (Risky)
        
        # Mock behavior
        self.risk_manager.correlation_manager.check_correlation_risk.return_value = (True, "Mocked Correlation Risk")
        
        # Validate
        is_valid, reason = self.risk_manager.validate_new_trade(
            symbol='ETH/USDT',
            proposed_size=Decimal("5.0"),
            current_positions=1,
            correlated_positions=0,
            active_symbols=['BTC/USDT']
        )
        
        print(f"\n[Test] Buying ETH with BTC held -> Valid: {is_valid}, Reason: {reason}")
        
        self.assertFalse(is_valid)
        self.assertIn("Correlation Risk", reason)

    def test_correlation_allow(self):
        """Test that low correlation allows a trade"""
        # Scenario: User holds BTC, wants to buy SOL (Assume decoupled for test)
        
        # Mock behavior
        self.risk_manager.correlation_manager.check_correlation_risk.return_value = (False, "Safe")
        
        # Validate
        is_valid, reason = self.risk_manager.validate_new_trade(
            symbol='SOL/USDT',
            proposed_size=Decimal("5.0"),
            current_positions=1,
            correlated_positions=0,
            active_symbols=['BTC/USDT']
        )
        
        print(f"[Test] Buying SOL with BTC held -> Valid: {is_valid}, Reason: {reason}")
        
        self.assertTrue(is_valid)

if __name__ == '__main__':
    unittest.main()
