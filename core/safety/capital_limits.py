"""
Capital Limits - Position Size & Exposure Controls

Enforces:
1. Maximum position size per trade
2. Maximum open positions
3. Maximum total exposure
4. Maximum daily trade count

Design: REJECT trades that violate limits
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LimitViolationError(Exception):
    """Raised when trade violates capital limits"""
    pass


class CapitalLimits:
    """
    Capital limits enforcement system

    Validates trades BEFORE execution to prevent:
    - Over-sized positions
    - Over-leverage
    - Excessive trading (spam protection)
    """

    def __init__(
        self,
        max_position_size_usd: float = 250.0,
        max_open_positions: int = 4,
        max_total_exposure_usd: float = 1000.0,
        max_daily_trades: int = 20,
        min_account_balance_usd: float = 100.0
    ):
        """
        Initialize capital limits

        Args:
            max_position_size_usd: Maximum size per position
            max_open_positions: Maximum concurrent open positions
            max_total_exposure_usd: Maximum total capital at risk
            max_daily_trades: Maximum trades per 24h (spam protection)
            min_account_balance_usd: Never trade below this balance
        """
        self.max_position_size = max_position_size_usd
        self.max_open_positions = max_open_positions
        self.max_total_exposure = max_total_exposure_usd
        self.max_daily_trades = max_daily_trades
        self.min_balance = min_account_balance_usd

        # Track daily trades
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()

        logger.info(f"Capital Limits initialized:")
        logger.info(f"  Max position size: ${max_position_size_usd}")
        logger.info(f"  Max open positions: {max_open_positions}")
        logger.info(f"  Max total exposure: ${max_total_exposure_usd}")
        logger.info(f"  Max daily trades: {max_daily_trades}")

    def validate_trade(
        self,
        proposed_size_usd: float,
        current_open_positions: int,
        current_total_exposure_usd: float,
        current_balance_usd: float
    ) -> bool:
        """
        Validate if trade meets all capital limits

        Args:
            proposed_size_usd: Size of proposed trade
            current_open_positions: Number of currently open positions
            current_total_exposure_usd: Total capital currently at risk
            current_balance_usd: Current account balance

        Returns:
            bool: True if trade is allowed

        Raises:
            LimitViolationError: If trade violates any limit
        """
        # Reset daily counter at midnight
        current_date = datetime.now().date()
        if current_date > self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
            logger.info("Daily trade counter reset")

        # Check 1: Position size
        if proposed_size_usd > self.max_position_size:
            raise LimitViolationError(
                f"Position size ${proposed_size_usd:.2f} exceeds limit ${self.max_position_size:.2f}"
            )

        # Check 2: Number of open positions
        if current_open_positions >= self.max_open_positions:
            raise LimitViolationError(
                f"Already at max open positions: {current_open_positions} / {self.max_open_positions}"
            )

        # Check 3: Total exposure
        new_total_exposure = current_total_exposure_usd + proposed_size_usd
        if new_total_exposure > self.max_total_exposure:
            raise LimitViolationError(
                f"Total exposure ${new_total_exposure:.2f} would exceed limit ${self.max_total_exposure:.2f}"
            )

        # Check 4: Daily trade count
        if self.daily_trade_count >= self.max_daily_trades:
            raise LimitViolationError(
                f"Daily trade limit reached: {self.daily_trade_count} / {self.max_daily_trades}"
            )

        # Check 5: Minimum balance
        balance_after_trade = current_balance_usd - proposed_size_usd
        if balance_after_trade < self.min_balance:
            raise LimitViolationError(
                f"Trade would bring balance below minimum: ${balance_after_trade:.2f} < ${self.min_balance:.2f}"
            )

        # All checks passed
        logger.info(f"✅ Trade validation passed: ${proposed_size_usd:.2f}")
        return True

    def record_trade(self):
        """Record that a trade was executed (increment counter)"""
        self.daily_trade_count += 1
        logger.info(f"Trade recorded: {self.daily_trade_count} / {self.max_daily_trades} today")

    def get_limits_status(
        self,
        current_open_positions: int,
        current_total_exposure_usd: float,
        current_balance_usd: float
    ) -> Dict:
        """
        Get current status vs limits

        Returns:
            Dict with current usage and remaining capacity
        """
        return {
            'position_size_limit': self.max_position_size,
            'open_positions': {
                'current': current_open_positions,
                'max': self.max_open_positions,
                'remaining': max(0, self.max_open_positions - current_open_positions),
            },
            'total_exposure': {
                'current': current_total_exposure_usd,
                'max': self.max_total_exposure,
                'remaining': max(0, self.max_total_exposure - current_total_exposure_usd),
            },
            'daily_trades': {
                'current': self.daily_trade_count,
                'max': self.max_daily_trades,
                'remaining': max(0, self.max_daily_trades - self.daily_trade_count),
            },
            'balance': {
                'current': current_balance_usd,
                'min_required': self.min_balance,
                'available': max(0, current_balance_usd - self.min_balance),
            },
        }

    def can_trade(
        self,
        proposed_size_usd: float,
        current_open_positions: int,
        current_total_exposure_usd: float,
        current_balance_usd: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check if trade can execute (non-exception version)

        Returns:
            (can_trade: bool, reason_if_not: str)
        """
        try:
            self.validate_trade(
                proposed_size_usd,
                current_open_positions,
                current_total_exposure_usd,
                current_balance_usd
            )
            return (True, None)
        except LimitViolationError as e:
            return (False, str(e))


# Example usage
if __name__ == "__main__":
    # Initialize limits for $500 capital
    limits = CapitalLimits(
        max_position_size_usd=125.0,    # $125 per trade
        max_open_positions=4,            # Max 4 positions
        max_total_exposure_usd=500.0,   # Total $500
        max_daily_trades=20,             # Max 20 trades/day
        min_account_balance_usd=100.0   # Keep $100 reserve
    )

    # Test scenarios
    print("Test 1: Normal trade ($100)")
    try:
        limits.validate_trade(
            proposed_size_usd=100.0,
            current_open_positions=1,
            current_total_exposure_usd=100.0,
            current_balance_usd=400.0
        )
        limits.record_trade()
        print("✅ PASS")
    except LimitViolationError as e:
        print(f"❌ FAIL: {e}")

    print("\nTest 2: Position too large ($150)")
    try:
        limits.validate_trade(
            proposed_size_usd=150.0,
            current_open_positions=1,
            current_total_exposure_usd=100.0,
            current_balance_usd=400.0
        )
        print("✅ PASS")
    except LimitViolationError as e:
        print(f"❌ FAIL: {e}")

    print("\nTest 3: Too many open positions")
    try:
        limits.validate_trade(
            proposed_size_usd=100.0,
            current_open_positions=4,  # Already at max
            current_total_exposure_usd=400.0,
            current_balance_usd=100.0
        )
        print("✅ PASS")
    except LimitViolationError as e:
        print(f"❌ FAIL: {e}")

    print("\nCurrent status:")
    status = limits.get_limits_status(
        current_open_positions=2,
        current_total_exposure_usd=200.0,
        current_balance_usd=300.0
    )
    import json
    print(json.dumps(status, indent=2))
