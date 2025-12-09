from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
import logging
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """User-friendly risk tolerance levels (Grandma Rule compliant)."""
    CONSERVATIVE = "conservative"  # Max 1% per trade, 5% daily loss
    MODERATE = "moderate"          # Max 2% per trade, 10% daily loss
    AGGRESSIVE = "aggressive"      # Max 5% per trade, 15% daily loss


@dataclass
class RiskLimits:
    """
    Risk parameters for portfolio protection.
    """
    max_position_size_pct: Decimal
    max_daily_loss_pct: Decimal
    max_drawdown_pct: Decimal # Total account drawdown limit
    max_concurrent_positions: int
    max_concurrent_positions: int
    max_correlated_positions: int
    volatility_scale_threshold: Decimal  # 0-100 percentile
    consecutive_loss_limit: int
    cooldown_minutes: int

    @classmethod
    def from_risk_level(cls, level: RiskLevel) -> 'RiskLimits':
        """Factory method: Convert user-friendly risk level to technical limits."""
        configs = {
            RiskLevel.CONSERVATIVE: cls(
                max_position_size_pct=Decimal("1.0"),
                max_daily_loss_pct=Decimal("5.0"),
                max_drawdown_pct=Decimal("15.0"),
                max_concurrent_positions=3,
                max_correlated_positions=2,
                volatility_scale_threshold=Decimal("80.0"),
                consecutive_loss_limit=3,
                cooldown_minutes=60
            ),
            RiskLevel.MODERATE: cls(
                max_position_size_pct=Decimal("2.0"),
                max_daily_loss_pct=Decimal("10.0"),
                max_drawdown_pct=Decimal("20.0"),
                max_concurrent_positions=5,
                max_correlated_positions=3,
                volatility_scale_threshold=Decimal("85.0"),
                consecutive_loss_limit=4,
                cooldown_minutes=30
            ),
            RiskLevel.AGGRESSIVE: cls(
                max_position_size_pct=Decimal("5.0"),
                max_daily_loss_pct=Decimal("15.0"),
                max_drawdown_pct=Decimal("25.0"),
                max_concurrent_positions=8,
                max_correlated_positions=4,
                volatility_scale_threshold=Decimal("90.0"),
                consecutive_loss_limit=5,
                cooldown_minutes=15
            )
        }
        return configs[level]


class RiskManager:
    """
    Central risk management system.
    Enforces all safety constraints before allowing trades.
    """
    
    def __init__(self, limits: RiskLimits, portfolio_value: Decimal):
        self.limits = limits
        self.portfolio_value = portfolio_value
        self.daily_start_value = portfolio_value
        self.daily_reset_time = datetime.now()
        self.consecutive_losses = 0
        self.cooldown_until: Optional[datetime] = None
        
    @property
    def max_drawdown_pct(self) -> Decimal:
        return self.limits.max_drawdown_pct

    def reset_daily_tracking(self) -> None:
        """Reset daily loss tracking at start of new trading day."""
        if datetime.now() - self.daily_reset_time > timedelta(hours=24):
            self.daily_start_value = self.portfolio_value
            self.daily_reset_time = datetime.now()
            logger.info("Daily risk tracking reset. Starting value: %s", 
                       self.daily_start_value)
    
    def update_portfolio_value(self, new_value: Decimal) -> None:
        """Update current portfolio value and check daily loss limit."""
        self.portfolio_value = new_value
        self.reset_daily_tracking()
        
    def check_cooldown(self) -> Tuple[bool, Optional[str]]:
        """
        Check if trading is in cooldown period.
        
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            remaining = (self.cooldown_until - datetime.now()).seconds // 60
            return False, f"Trading paused for {remaining} more minutes due to consecutive losses"
        return True, None
    
    def check_daily_loss_limit(self) -> Tuple[bool, Optional[str]]:
        """
        Check if daily loss limit has been exceeded.
        
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        self.reset_daily_tracking()
        
        # Prevent division by zero if start value is 0
        if self.daily_start_value == 0:
             return True, None

        current_loss_pct = ((self.daily_start_value - self.portfolio_value) 
                           / self.daily_start_value * Decimal("100"))
        
        if current_loss_pct > self.limits.max_daily_loss_pct:
            return False, (f"Daily loss limit reached: {current_loss_pct:.2f}% "
                          f"(limit: {self.limits.max_daily_loss_pct}%)")
        return True, None
    
    def calculate_position_size(
        self, 
        current_positions: int,
        market_volatility_percentile: Decimal
    ) -> Tuple[Decimal, str]:
        """
        Calculate safe position size based on current market conditions.
        
        Args:
            current_positions: Number of currently open positions
            market_volatility_percentile: Current volatility (0-100)
            
        Returns:
            Tuple of (position_size_pct, explanation)
        """
        base_size = self.limits.max_position_size_pct
        explanation = f"Using standard position size of {base_size}%"
        
        # Scale down if high volatility
        if market_volatility_percentile > self.limits.volatility_scale_threshold:
            base_size = base_size * Decimal("0.5")
            explanation = (f"Position size reduced to {base_size}% due to "
                          f"high market volatility ({market_volatility_percentile}th percentile)")
        
        # Further reduce if many positions open (diversification)
        if current_positions >= self.limits.max_concurrent_positions - 1 and current_positions > 0:
            base_size = base_size * Decimal("0.75")
            explanation += f" and adjusted down due to {current_positions} open positions"
        
        return base_size, explanation
    
    def validate_new_trade(
        self,
        symbol: str,
        proposed_size: Decimal,
        current_positions: int,
        correlated_positions: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Master validation: Check all risk constraints before allowing trade.
        """
        # Check 1: Cooldown period
        allowed, reason = self.check_cooldown()
        if not allowed:
            return False, reason
        
        # Check 2: Daily loss limit
        allowed, reason = self.check_daily_loss_limit()
        if not allowed:
            return False, reason
        
        # Check 3: Position size limit
        if proposed_size > self.limits.max_position_size_pct:
            return False, (f"Position size {proposed_size}% exceeds limit "
                          f"{self.limits.max_position_size_pct}%")
        
        # Check 4: Concurrent positions limit
        if current_positions >= self.limits.max_concurrent_positions:
            return False, (f"Maximum concurrent positions reached "
                          f"({self.limits.max_concurrent_positions})")
        
        # Check 5: Correlation limit
        if correlated_positions >= self.limits.max_correlated_positions:
            return False, (f"Too many correlated positions ({correlated_positions}). "
                          f"Limit: {self.limits.max_correlated_positions}")
        
        logger.info("Trade approved for %s: Size %.2f%%", symbol, proposed_size)
        return True, None
    
    def record_trade_result(self, was_profitable: bool) -> None:
        """
        Track trade outcome for consecutive loss detection.
        """
        if was_profitable:
            self.consecutive_losses = 0
            logger.info("Profitable trade. Consecutive losses reset to 0")
        else:
            self.consecutive_losses += 1
            logger.warning("Loss recorded. Consecutive losses: %d/%d",
                          self.consecutive_losses, 
                          self.limits.consecutive_loss_limit)
            
            # Trigger cooldown if limit reached
            if self.consecutive_losses >= self.limits.consecutive_loss_limit:
                self.cooldown_until = (datetime.now() + 
                                      timedelta(minutes=self.limits.cooldown_minutes))
                logger.critical("Consecutive loss limit reached! Trading paused until %s",
                               self.cooldown_until)

    # --- LEGACY MIGRATION: Methods ported from old risk_manager.py ---
    
    def check_profit_guard(self, current_price, buy_price, fee_rate=Decimal("0.001"), min_profit_pct=Decimal("0.005")):
        """
        Check if selling now yields a profit after fees (using Decimal).
        Ported from v1 engine.
        """
        # Ensure inputs are Decimal
        cp = Decimal(str(current_price))
        bp = Decimal(str(buy_price))
        fr = Decimal(str(fee_rate))
        mpp = Decimal(str(min_profit_pct))
        
        # Cost to buy 1 unit
        buy_cost = bp * (Decimal('1') + fr)
        
        # Net proceeds from selling 1 unit
        sell_proceeds = cp * (Decimal('1') - fr)
        
        # Profit
        profit = sell_proceeds - buy_cost
        
        # Avoid division by zero
        if buy_cost == 0:
            return False, Decimal('0')
            
        profit_pct = (profit / buy_cost) * Decimal('100')
        
        is_profitable = profit_pct >= (mpp * 100)
        
        return is_profitable, profit_pct

    def check_drawdown_limit(self, current_equity, logger=None):
        """
        Check if current drawdown from PEAK exceeds maximum allowed.
        This protects against slow bleed over weeks/months.
        """
        ce = Decimal(str(current_equity))
        
        # Peak equity is tracked in self.daily_start_value for daily, 
        # but we need an absolute peak for Total Drawdown.
        if not hasattr(self, 'peak_equity') or self.peak_equity is None:
            self.peak_equity = ce
        
        # Update peak if we've grown
        if ce > self.peak_equity:
            self.peak_equity = ce
        
        # Avoid division by zero
        if self.peak_equity == 0:
             return True, Decimal('0')

        # Calculate drawdown from peak
        drawdown = (self.peak_equity - ce) / self.peak_equity
        drawdown_pct = drawdown * Decimal('100')
        
        # Use a default 20% max drawdown if not in limits, or add to limits.
        # Expert review said "Max Drawdown < 20%".
        # We'll expect limits to have it, or default to 20.
        max_dd = getattr(self.limits, 'max_drawdown_pct', Decimal("20.0"))
        
        # Check if we've exceeded the max drawdown limit
        if drawdown_pct > max_dd:
            return False, drawdown_pct
        
        return True, drawdown_pct


def setup_safe_trading_bot(user_risk_level: str) -> 'RiskManager':
    """Grandma-friendly wrapper to init risk manager"""
    try:
        level = RiskLevel(user_risk_level.lower())
    except ValueError:
        logger.warning(f"Invalid risk level '{user_risk_level}', defaulting to CONSERVATIVE")
        level = RiskLevel.CONSERVATIVE
        
    return RiskManager(
        limits=RiskLimits.from_risk_level(level),
        portfolio_value=Decimal("10000") # Default placeholder, should be updated by bot immediately
    )
