import sys
import os
from decimal import Decimal
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.risk_module import setup_safe_trading_bot, RiskLevel
from core.notifier import TelegramNotifier

class TestPhase2Features(unittest.TestCase):
    def setUp(self):
        self.risk_manager = setup_safe_trading_bot("moderate")
        # Mock limits for consistent testing
        self.risk_manager.limits.max_position_size_pct = Decimal("2.0")
        self.risk_manager.limits.volatility_scale_threshold = Decimal("80") 
        
        self.notifier = TelegramNotifier(token="TEST_TOKEN", chat_id="TEST_CHAT")
        self.notifier.send_message = MagicMock()

    def test_risk_confluence_logic(self):
        """Test that position size scales with confluence score"""
        print("\n--- Testing Risk & Confluence Logic ---")
        
        # Case 1: High Conviction (Score 90) -> Full Size (2.0%)
        # Low volatility
        size, expl = self.risk_manager.calculate_position_size(
            current_positions=0,
            market_volatility_percentile=Decimal("50"),
            confluence_score=90
        )
        print(f"Case 1 (Score 90, Vol 50): {size}% - {expl}")
        self.assertEqual(size, Decimal("2.0"))
        self.assertIn("High Confluence", expl)

        # Case 2: Medium Conviction (Score 70) -> 75% Size (1.5%)
        size, expl = self.risk_manager.calculate_position_size(
            current_positions=0,
            market_volatility_percentile=Decimal("50"),
            confluence_score=70
        )
        print(f"Case 2 (Score 70, Vol 50): {size}% - {expl}")
        self.assertEqual(size, Decimal("1.5"))
        
        # Case 3: Low Conviction (Score 40) -> 50% Size (1.0%)
        size, expl = self.risk_manager.calculate_position_size(
            current_positions=0,
            market_volatility_percentile=Decimal("50"),
            confluence_score=40
        )
        print(f"Case 3 (Score 40, Vol 50): {size}% - {expl}")
        self.assertEqual(size, Decimal("1.0"))

        # Case 4: High Volatility + High Conviction -> 50% reduction
        # Base 2.0 -> Score 90 (2.0) -> Volatility (>80) (1.0)
        size, expl = self.risk_manager.calculate_position_size(
            current_positions=0,
            market_volatility_percentile=Decimal("90"),
            confluence_score=90
        )
        print(f"Case 4 (Score 90, Vol 90): {size}% - {expl}")
        self.assertEqual(size, Decimal("1.0"))
        self.assertIn("High Volatility", expl)

    def test_notifier_payload(self):
        """Test that notifier formats messages correctly"""
        print("\n--- Testing Notifier Payload ---")
        
        breakdown = {
            'technical': {'score': 25},
            'onchain': {'score': 20},
            'macro': {'score': 15},
            'fundamental': {'score': 10}
        }
        
        self.notifier.notify_confluence_signal("BTC/USDT", 70, breakdown)
        
        # Convert call args to string to verify content
        args, _ = self.notifier.send_message.call_args
        msg = args[0]
        print(f"Notification Message:\n{msg}")
        
        self.assertIn("✨ *POTENTIAL OPPORTUNITY*", msg)
        self.assertIn("Confluence Score: *70/100*", msg)
        self.assertIn("Macro: `15`", msg)

if __name__ == '__main__':
    unittest.main()
