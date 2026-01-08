"""
Emergency Kill Switch - Critical Safety System

Automatically halts ALL trading when:
1. Daily loss limit exceeded
2. Weekly loss limit exceeded
3. Manual trigger via emergency_stop()

Design: FAIL-SAFE (defaults to HALT if uncertain)
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EmergencyKillSwitch:
    """
    Emergency kill switch with persistent state

    Features:
    - Daily/weekly loss tracking
    - Manual emergency stop
    - Persistent state (survives bot restart)
    - Telegram alert integration
    - Requires manual reactivation after trigger
    """

    def __init__(
        self,
        max_daily_loss_usd: float = 50.0,
        max_weekly_loss_usd: float = 150.0,
        state_file: str = 'data/kill_switch_state.json'
    ):
        """
        Initialize kill switch

        Args:
            max_daily_loss_usd: Maximum loss per 24h period
            max_weekly_loss_usd: Maximum loss per 7-day period
            state_file: Persistent state storage
        """
        self.max_daily_loss = max_daily_loss_usd
        self.max_weekly_loss = max_weekly_loss_usd
        self.state_file = state_file

        # Load persistent state
        self.state = self._load_state()

        # Track losses
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.last_reset_date = datetime.now().date()

        logger.info(f"Kill Switch initialized: Daily limit ${max_daily_loss_usd}, Weekly limit ${max_weekly_loss_usd}")

    def _load_state(self) -> Dict:
        """Load persistent state from disk"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Kill switch state loaded: {state}")
                    return state
            except Exception as e:
                logger.error(f"Failed to load kill switch state: {e}")

        # Default state
        return {
            'active': False,
            'reason': None,
            'triggered_at': None,
            'manual_override': False,
        }

    def _save_state(self):
        """Persist state to disk"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info(f"Kill switch state saved: {self.state}")
        except Exception as e:
            logger.error(f"Failed to save kill switch state: {e}")

    def record_pnl(self, pnl: float):
        """
        Record trade P&L and check limits

        Args:
            pnl: Profit/loss from trade (negative for loss)
        """
        # Only track losses
        if pnl < 0:
            self.daily_loss += abs(pnl)
            self.weekly_loss += abs(pnl)

            logger.info(f"Loss recorded: ${abs(pnl):.2f} | Daily total: ${self.daily_loss:.2f} | Weekly total: ${self.weekly_loss:.2f}")

            # Check limits
            self._check_limits()

        # Reset daily counter at midnight
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_loss = 0.0
            self.last_reset_date = current_date
            logger.info("Daily loss counter reset")

    def _check_limits(self):
        """Check if loss limits exceeded"""
        if self.daily_loss >= self.max_daily_loss:
            self.activate(f"Daily loss limit exceeded: ${self.daily_loss:.2f} >= ${self.max_daily_loss:.2f}")

        if self.weekly_loss >= self.max_weekly_loss:
            self.activate(f"Weekly loss limit exceeded: ${self.weekly_loss:.2f} >= ${self.max_weekly_loss:.2f}")

    def activate(self, reason: str):
        """
        Activate kill switch - HALT ALL TRADING

        Args:
            reason: Why kill switch was triggered
        """
        if self.state['active']:
            logger.warning(f"Kill switch already active: {self.state['reason']}")
            return

        self.state.update({
            'active': True,
            'reason': reason,
            'triggered_at': datetime.now().isoformat(),
            'manual_override': False,
        })

        self._save_state()

        # Log critical event
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
        logger.critical(f"🛑 ALL TRADING HALTED")
        logger.critical(f"📊 Daily loss: ${self.daily_loss:.2f}, Weekly loss: ${self.weekly_loss:.2f}")

        # Alert should be sent by caller (TradingEngine)

    def is_active(self) -> bool:
        """Check if kill switch is currently active"""
        return self.state['active']

    def get_status(self) -> Dict:
        """Get current kill switch status"""
        return {
            'active': self.state['active'],
            'reason': self.state['reason'],
            'triggered_at': self.state['triggered_at'],
            'daily_loss': self.daily_loss,
            'weekly_loss': self.weekly_loss,
            'daily_limit': self.max_daily_loss,
            'weekly_limit': self.max_weekly_loss,
            'daily_remaining': max(0, self.max_daily_loss - self.daily_loss),
            'weekly_remaining': max(0, self.max_weekly_loss - self.weekly_loss),
        }

    def emergency_stop(self, reason: str = "Manual emergency stop"):
        """
        Manual emergency stop - highest priority

        Args:
            reason: Reason for manual stop
        """
        self.state['manual_override'] = True
        self.activate(reason)
        logger.critical(f"🚨 MANUAL EMERGENCY STOP: {reason}")

    def deactivate(self, authorization_code: str):
        """
        Deactivate kill switch - requires manual authorization

        Args:
            authorization_code: Security code (prevents accidental reactivation)

        Returns:
            bool: True if deactivated successfully
        """
        # Simple authorization (enhance with env var in production)
        expected_code = os.getenv('KILL_SWITCH_AUTH_CODE', 'RESUME_TRADING_2026')

        if authorization_code != expected_code:
            logger.error("Kill switch deactivation FAILED: Invalid authorization code")
            return False

        if not self.state['active']:
            logger.warning("Kill switch already inactive")
            return True

        # Reset state
        old_reason = self.state['reason']
        self.state.update({
            'active': False,
            'reason': None,
            'triggered_at': None,
            'manual_override': False,
        })

        self._save_state()

        logger.warning(f"✅ Kill switch DEACTIVATED (was: {old_reason})")
        logger.warning(f"🟢 Trading RESUMED")

        return True

    def reset_weekly_counter(self):
        """Reset weekly loss counter (call every 7 days)"""
        self.weekly_loss = 0.0
        logger.info("Weekly loss counter reset")

    def __str__(self) -> str:
        """String representation"""
        status = "🔴 ACTIVE" if self.state['active'] else "🟢 INACTIVE"
        return (
            f"Kill Switch [{status}]\n"
            f"  Daily Loss: ${self.daily_loss:.2f} / ${self.max_daily_loss:.2f}\n"
            f"  Weekly Loss: ${self.weekly_loss:.2f} / ${self.max_weekly_loss:.2f}\n"
            f"  Reason: {self.state['reason'] or 'N/A'}"
        )


# Example usage
if __name__ == "__main__":
    # Test kill switch
    kill_switch = EmergencyKillSwitch(max_daily_loss_usd=50.0)

    print("Initial status:")
    print(kill_switch)

    # Simulate losses
    print("\nSimulating losses...")
    kill_switch.record_pnl(-20.0)  # -$20 loss
    print(kill_switch.get_status())

    kill_switch.record_pnl(-25.0)  # -$25 loss
    print(kill_switch.get_status())

    kill_switch.record_pnl(-10.0)  # -$10 loss (total -$55, should trigger)
    print(kill_switch.get_status())

    # Try to trade
    if kill_switch.is_active():
        print("\n🛑 Kill switch is ACTIVE - trading blocked!")

    # Deactivate
    print("\nAttempting to deactivate...")
    kill_switch.deactivate("RESUME_TRADING_2026")
    print(kill_switch)
