from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
import logging
from collections import deque
from .correlation import CorrelationManager
from core.portfolio_analyzer import PortfolioCorrelationAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """User-friendly risk tolerance levels (Grandma Rule compliant)."""
    CONSERVATIVE = "conservative"  # Max 1% per trade, 5% daily loss
    MODERATE = "moderate"          # Max 2% per trade, 10% daily loss
    AGGRESSIVE = "aggressive"      # Max 5% per trade, 15% daily loss

# Sector Mapping for Portfolio Diversification
SECTOR_MAP = {
    'BTC': 'LEGACY',
    'ETH': 'L1',
    'SOL': 'L1',
    'ADA': 'L1',
    'DOT': 'L1',
    'AVAX': 'L1',
    'BNB': 'EXCHANGE',
    'XRP': 'PAYMENTS',
    'XLM': 'PAYMENTS',
    'DOGE': 'MEMES',
    'SHIB': 'MEMES',
    'PEPE': 'MEMES',
    'LINK': 'ORACLE',
    'AAVE': 'DEFI',
    'UNI': 'DEFI',
    'APT': 'L1',
    'NEAR': 'L1',
    'ICP': 'L1',
    'FET': 'AI',
    'TAO': 'AI',
    'RNDR': 'AI'
}


@dataclass
class RiskLimits:
    """
    Risk parameters for portfolio protection.
    """
    max_position_size_pct: Decimal
    max_daily_loss_pct: Decimal
    max_drawdown_pct: Decimal # Total account drawdown limit
    max_concurrent_positions: int
    max_correlated_positions: int
    volatility_scale_threshold: Decimal  # 0-100 percentile
    consecutive_loss_limit: int
    cooldown_minutes: int
    max_trade_amount_usd: float = 500.0 # HARD CAP per trade
    global_drawdown_limit_pct: float = 0.25 # 25% Max Account Loss -> Stop Bot (User Adjustment)
    max_portfolio_heat_pct: Decimal = Decimal("50.0") # Max 50% of total capital in active trades
    max_single_sector_pct: Decimal = Decimal("25.0") # Max 25% in one sector (L1s, Memes, AI, etc.)


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
        from datetime import time
        self.allowed_hours = (time(0, 0), time(23, 59)) # Default: 24/7
        
        # Institutional Hardening
        self.portfolio_analyzer = PortfolioCorrelationAnalyzer()
        self.peak_equity = Decimal("0")

        
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
    
    def set_schedule(self, start_hour: int, end_hour: int):
        """Set trading hours (Legacy port)"""
        from datetime import time
        self.allowed_hours = (time(start_hour, 0), time(end_hour, 59))

    def can_trade(self) -> bool:
        """Check if current time is within allowed hours (Legacy port)"""
        now = datetime.now().time()
        start, end = self.allowed_hours
        if start <= end:
            return start <= now <= end
        else: # Crosses midnight
            return start <= now or now <= end

    
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
        market_volatility_percentile: Decimal,
        confluence_score: Optional[int] = None
    ) -> Tuple[Decimal, str]:
        """
        Calculate safe position size based on current market conditions.
        
        Args:
            current_positions: Number of currently open positions
            market_volatility_percentile: Current volatility (0-100)
            confluence_score: Optional Confluence Score (0-100)
            
        Returns:
            Tuple of (position_size_pct, explanation)
        """
        base_size = self.limits.max_position_size_pct
        explanation_parts = [f"Base size: {base_size}%"]
        
        # 1. Confluence Scaling (Intel)
        # Higher conviction = Full size. Lower conviction = Reduced size.
        if confluence_score is not None:
            if confluence_score >= 80:
                # High Conviction: No reduction
                explanation_parts.append(f"High Confluence ({confluence_score}) ✅")
            elif confluence_score >= 60:
                # Medium Conviction: 75% size
                base_size = base_size * Decimal("0.75")
                explanation_parts.append(f"Medium Confluence ({confluence_score}) -> 75% size")
            else:
                # Low Conviction: 50% size
                base_size = base_size * Decimal("0.50")
                explanation_parts.append(f"Low Confluence ({confluence_score}) -> 50% size")

        # 2. Volatility Scaling (Risk)
        if market_volatility_percentile > self.limits.volatility_scale_threshold:
            base_size = base_size * Decimal("0.5")
            explanation_parts.append(f"High Volatility ({market_volatility_percentile}th) -> 50% reduction")
        
        # 3. Diversification Scaling (Portfolio)
        if current_positions >= self.limits.max_concurrent_positions - 1 and current_positions > 0:
            base_size = base_size * Decimal("0.75")
            explanation_parts.append(f"High Load ({current_positions} pos) -> 75% reduction")
        
        explanation = "; ".join(explanation_parts)
        return base_size, explanation
    
    def validate_new_trade(
        self,
        symbol: str,
        proposed_size: Decimal,
        current_positions: int,
        correlated_positions: int,
        active_symbols: list = None,
        total_exposure_usd: Decimal = Decimal("0"),
        sector_exposure_usd: Decimal = Decimal("0"),
        logger_instance = None,
        exchange_instance = None
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
        
        # Check 6: Portfolio Heat (New V2)
        proposed_amount_usd = (proposed_size / Decimal("100")) * self.portfolio_value
        allowed, reason = self.check_portfolio_heat(total_exposure_usd + proposed_amount_usd)
        if not allowed:
            return False, reason
            
        # Check 7: Sector Limits (New V2)
        allowed, reason = self.check_sector_limit(symbol, sector_exposure_usd, proposed_amount_usd)
        if not allowed:
            return False, reason

        # Check 8: Drawdown Velocity (Institutional Hardening)
        velocity_halt, velocity_reason = self.check_drawdown_velocity(logger=logger_instance)
        if velocity_halt:
            return False, velocity_reason
        
        # Check 9: Portfolio Correlation Matrix (Phase 6 Institutional)
        if active_symbols and exchange_instance:
             corr_res = self.portfolio_analyzer.get_portfolio_overlap(symbol, active_symbols, exchange_instance)
             if corr_res['risk'] in ['HIGH', 'EXTREME']:
                 max_corr = corr_res.get('max_correlation', 0)
                 return False, f"Portfolio Correlation Risk ({corr_res['risk']}): Max Corr {max_corr} with {corr_res.get('highly_correlated_with')}"
             
             # Apply position sizing penalty based on correlation
             penalty = self.portfolio_analyzer.get_penalty_multiplier(corr_res)
             if penalty < 1.0:
                 logger.info("Applying correlation penalty for %s: %.2fx", symbol, penalty)
                 # Note: In a real implementation, we'd adjust proposed_size here, but for validation 
                 # we mainly rejection if it's too high. Adjusting size needs to happen in TradingEngine.
            
        # Check 10: Intelligent Correlation (Legacy Placeholder)
        if active_symbols:
            is_risky, corr_reason = self.correlation_manager.check_correlation_risk(symbol, active_symbols)
            if is_risky:
                  return False, f"Correlation Risk: {corr_reason}"
        
        logger.info("Trade approved for %s: Size %.2f%%", symbol, proposed_size)
        return True, None

    
    def check_portfolio_heat(self, current_exposure_usd: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Ensure total active exposure doesn't exceed portfolio heat limit.
        """
        heat_pct = (current_exposure_usd / self.portfolio_value) * Decimal("100")
        if heat_pct > self.limits.max_portfolio_heat_pct:
            return False, f"Portfolio heat too high: {heat_pct:.1f}% (limit: {self.limits.max_portfolio_heat_pct}%)"
        return True, None

    def check_sector_limit(self, symbol: str, current_sector_exposure_usd: Decimal, new_trade_usd: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Check if adding this trade would exceed sector-level concentration limits.
        """
        # Get base symbol (remove /USDT)
        base = symbol.split('/')[0].split(':')[0]
        sector = SECTOR_MAP.get(base, 'ALT')
        
        total_after_trade = current_sector_exposure_usd + new_trade_usd
        sector_pct = (total_after_trade / self.portfolio_value) * Decimal("100")
        
        if sector_pct > self.limits.max_single_sector_pct:
            return False, f"Sector limit hit for {sector}: {sector_pct:.1f}% (limit: {self.limits.max_single_sector_pct}%)"
        
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

    def check_exit_conditions(self, position_data, regime_state: str = None) -> Tuple[str, Optional[str]]:
        """
        V4 Exit Engine - Custom Logic Per Strategy
        - Buy-the-Dip: Infinite hold until +5% profit (alerts at 60/90/120/200 days)
        - Other Strategies: Regime-aware stops, stagnation exits, regime protection
        """
        current_price = Decimal(str(position_data['current_price']))
        entry_price = Decimal(str(position_data['entry_price']))
        strategy = position_data.get('strategy', 'Unknown')
        entry_date = position_data.get('entry_date')

        # Parse entry_date if string
        if isinstance(entry_date, str):
            try:
                entry_date = datetime.fromisoformat(entry_date)
            except:
                entry_date = datetime.utcnow()

        # 1. Calculate PnL
        pnl_pct = (current_price - entry_price) / entry_price

        # 2. Calculate position age
        hours_open = 0
        days_open = 0
        if entry_date:
            hours_open = (datetime.utcnow() - entry_date).total_seconds() / 3600
            days_open = hours_open / 24

        # ========================================
        # BUY-THE-DIP HYBRID V2.0 STRATEGY
        # Dynamic Time-Weighted TP + Trailing Stops + Quality Floors
        # ========================================
        if strategy == "Buy-the-Dip Strategy":

            # STEP 1: Determine coin quality tier for catastrophic floor
            symbol = position_data.get('symbol', '')
            coin_base = symbol.split('/')[0] if '/' in symbol else symbol

            # Top 10 coins (strongest recovery probability)
            TOP_10 = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'MATIC']
            # Top 20 coins (moderate risk)
            TOP_20 = ['LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'ETC', 'FIL', 'APT', 'ICP', 'NEAR']

            if coin_base in TOP_10:
                catastrophic_floor = Decimal("-0.70")  # -70% for blue chips
            elif coin_base in TOP_20:
                catastrophic_floor = Decimal("-0.50")  # -50% for mid-caps
            else:
                catastrophic_floor = Decimal("-0.40")  # -40% for others (higher death risk)

            # STEP 2: Check catastrophic floor (prevents holding dead coins to -99%)
            if pnl_pct <= catastrophic_floor:
                return 'SELL', (
                    f"🚨 Catastrophic Floor Hit ({pnl_pct*100:.1f}%) | "
                    f"Tier: {'Top 10' if coin_base in TOP_10 else 'Top 20' if coin_base in TOP_20 else 'Other'} | "
                    f"Preventing total wipeout"
                )

            # STEP 3: Dynamic TP based on hold time (TIME-WEIGHTED PROFITS!)
            if days_open < 60:
                # 0-60 days: Quick wins, fast capital rotation
                tp_target = Decimal("0.05")  # 5% TP
                use_trailing = False
                trailing_pct = None

            elif days_open < 120:
                # 60-120 days: Reward patience with higher target
                tp_target = Decimal("0.08")  # 8% TP
                use_trailing = False
                trailing_pct = None

            elif days_open < 180:
                # 120-180 days: Long hold deserves bigger profit + protection
                tp_target = Decimal("0.12")  # 12% TP
                use_trailing = True
                trailing_pct = Decimal("0.08")  # 8% trailing stop

            else:
                # 180+ days: USER'S THEORY - Big bounces deserve big profits!
                tp_target = Decimal("0.15")  # 15% TP
                use_trailing = True
                trailing_pct = Decimal("0.10")  # 10% trailing stop

            # STEP 4: Check if TP target reached
            if pnl_pct >= tp_target:
                return 'SELL', (
                    f"✅ Take Profit Reached (+{pnl_pct*100:.2f}%) | "
                    f"Hold: {days_open:.0f} days | "
                    f"Target: {tp_target*100:.0f}%"
                )

            # STEP 5: Trailing stop logic (for 120+ day holds)
            if use_trailing and pnl_pct > 0:
                # Get position's peak price (stored in metadata)
                peak_price = position_data.get('peak_price', current_price)

                # Update peak if current price is higher
                if current_price > peak_price:
                    peak_price = current_price
                    # Note: Engine should update position metadata with new peak

                # Calculate trailing stop price
                trailing_stop_price = peak_price * (Decimal("1") - trailing_pct)

                # Check if trailing stop hit
                if current_price <= trailing_stop_price:
                    profit_captured = (current_price - entry_price) / entry_price
                    return 'SELL', (
                        f"📉 Trailing Stop Hit (+{profit_captured*100:.2f}%) | "
                        f"Hold: {days_open:.0f} days | "
                        f"Peak: ${peak_price:.6f} | Trail: {trailing_pct*100:.0f}%"
                    )

                # Return metadata to update peak price
                return 'HOLD', None, {'update_peak': True, 'peak_price': float(peak_price)}

            # STEP 6: Checkpoint Alerts (informational only)
            checkpoint_days = [60, 90, 120, 200, 300, 365]
            for checkpoint in checkpoint_days:
                # Alert within 12 hours of checkpoint
                if abs(days_open - checkpoint) <= 0.5:
                    return 'ALERT_CHECKPOINT', (
                        f"📅 Position Review: Day {days_open:.0f}\n"
                        f"Current P&L: {pnl_pct*100:+.1f}%\n"
                        f"Entry: ${entry_price:.6f} | Current: ${current_price:.6f}\n"
                        f"Current Target: +{tp_target*100:.0f}% "
                        f"({'+ ' + str(int(trailing_pct*100)) + '% trailing' if use_trailing else ''})\n"
                        f"Catastrophic Floor: {catastrophic_floor*100:.0f}%\n"
                        f"💡 Bot using Hybrid v2.0 dynamic strategy"
                    )

            # STEP 7: Default - HOLD and wait
            return 'HOLD', None

        # ========================================
        # STANDARD LOGIC FOR OTHER STRATEGIES
        # ========================================

        # Regime-Aware Stop Loss (Institutional Adjustment)
        sl_threshold = Decimal("-0.05") # Default -5%
        if regime_state == 'CRISIS':
            sl_threshold = Decimal("-0.02") # Tightest stop in crisis
        elif regime_state in ['BULL_CONFIRMED', 'TRANSITION_BULLISH']:
            sl_threshold = Decimal("-0.10") # Give space in bull runs

        # Time-Based Stagnation (Exit after 72h no progress)
        if hours_open > 72 and pnl_pct < 0.01:
            return 'SELL', f"Stagnation: Open {hours_open:.1f}h with <1% profit"

        # Regime Switch Veto (Sudden Bull -> Crisis)
        entry_regime = position_data.get('entry_regime')
        if entry_regime in ['BULL_CONFIRMED', 'TRANSITION_BULLISH'] and regime_state == 'CRISIS':
            if pnl_pct > -0.01: # Only if not already deeply in drawdown
                return 'SELL', f"Regime Veto: Market shifted to CRISIS state"

        # Take Profit (Strategy-Specific)
        tp_target = Decimal("0.03") # Default 3%
        if strategy == "Hyper-Scalper Bot": tp_target = Decimal("0.01")
        if strategy == "Grid Bot BTC" or strategy == "Grid Bot ETH": tp_target = Decimal("0.015")
        if strategy == "SMA Trend Bot": tp_target = Decimal("0.10")

        if pnl_pct >= tp_target:
             return 'SELL', f"Take Profit Reached (+{pnl_pct*100:.2f}%)"
             
        # 6. Stop Loss (Manual/Alert)
        if pnl_pct <= sl_threshold:
            return 'ALERT_STOP_LOSS', f"Stop Loss Threshold Hit ({pnl_pct*100:.2f}%) [Regime: {regime_state}]"
            
        return 'HOLD', None

    def check_drawdown_limit(self, current_equity: Decimal, logger=None) -> Tuple[bool, Decimal]:
        """
        Check if total account drawdown exceeds max allowed limit.
        """
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        drawdown_pct = Decimal("0")
        if self.peak_equity > 0:
            drawdown_pct = (self.peak_equity - current_equity) / self.peak_equity * Decimal("100")
            
        # Comparison with limit (already in pct)
        if drawdown_pct >= self.limits.max_drawdown_pct:
            return False, drawdown_pct
            
        return True, drawdown_pct

    def check_drawdown_velocity(self, logger=None) -> Tuple[bool, Optional[str]]:
        """
        Institutional Protect: Halt if drawdown is too fast.
        Default: Halt if account drops >10% in 168h (7 days).
        """
        if not logger:
            return False, None
            
        try:
            from core.database import PortfolioSnapshot
            session = logger.db.get_session()
            
            # Get latest snapshot
            latest = session.query(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).first()
            if not latest:
                session.close()
                return False, None
                
            # Get snapshot from 7 days ago
            cutoff = datetime.utcnow() - timedelta(days=7)
            historic = session.query(PortfolioSnapshot).filter(PortfolioSnapshot.timestamp <= cutoff).order_by(PortfolioSnapshot.timestamp.desc()).first()
            
            if not historic:
                # If we don't have 7 days of data, check for 24h as a secondary safety
                cutoff_24h = datetime.utcnow() - timedelta(hours=24)
                historic = session.query(PortfolioSnapshot).filter(PortfolioSnapshot.timestamp <= cutoff_24h).order_by(PortfolioSnapshot.timestamp.desc()).first()
                if not historic:
                    session.close()
                    return False, None
            
            # Calculate drop
            current_equity = latest.total_equity_usd
            historic_equity = historic.total_equity_usd
            
            if historic_equity > 0:
                vel_drawdown = (historic_equity - current_equity) / historic_equity
                
                # HALT if > 10% drop
                if vel_drawdown >= 0.10:
                    session.close()
                    return True, f"Drawdown Velocity Halt: Portfolio dropped {vel_drawdown*100:.1f}% in the last period."
            
            session.close()
            return False, None
            
        except Exception as e:
            print(f"[Risk] Error checking drawdown velocity: {e}")
            return False, None


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
