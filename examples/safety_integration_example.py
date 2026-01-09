"""
Safety Systems Integration Example - 100% Customizable

Demonstrates how to use the configuration-driven safety systems
for scalable, robust, customizable trading bots.

This example shows:
1. Configuration-driven initialization (no hardcoding)
2. Paper vs Live separation
3. Strategy-specific customization
4. Scaling presets for different capital levels
5. Runtime reconfiguration
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.safety import (
    EmergencyKillSwitch,
    CapitalLimits,
    SlippageProtection,
    get_safety_config
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigurableTradingBot:
    """
    Example trading bot with 100% customizable safety systems

    All parameters loaded from YAML config - NO hardcoding!
    """

    def __init__(
        self,
        exchange: str,
        mode: str,
        strategy: str = None,
        scaling_preset: str = None
    ):
        """
        Initialize bot with customizable safety systems

        Args:
            exchange: Exchange name (BINANCE, LUNO, MEXC)
            mode: Trading mode (paper, live, monitor)
            strategy: Optional strategy name (GridBot, MomentumBot, etc)
            scaling_preset: Optional preset (micro, small, medium, large)
        """
        self.exchange = exchange
        self.mode = mode
        self.strategy = strategy
        self.scaling_preset = scaling_preset

        logger.info(f"Initializing {exchange} {mode} bot...")
        if strategy:
            logger.info(f"  Strategy: {strategy}")
        if scaling_preset:
            logger.info(f"  Scaling preset: {scaling_preset}")

        # Load configuration
        self.config_loader = get_safety_config('config/safety_limits.yaml')

        # Get all configs at once (100% from YAML)
        configs = self.config_loader.get_all_configs(
            exchange=exchange,
            mode=mode,
            strategy=strategy,
            scaling_preset=scaling_preset
        )

        # Initialize safety systems with loaded configs
        self._initialize_safety_systems(configs)

        logger.info(f"✅ {exchange} {mode} bot initialized")

    def _initialize_safety_systems(self, configs):
        """Initialize all safety systems from configuration"""

        # Check global halt
        if configs['global_halt']:
            logger.critical("🚨 GLOBAL HALT ENABLED - Bot will not trade")
            self.global_halt = True
            return

        self.global_halt = False

        # 1. Kill Switch (100% configurable)
        kill_switch_config = configs['kill_switch']
        self.kill_switch = EmergencyKillSwitch(
            max_daily_loss_usd=kill_switch_config['max_daily_loss_usd'],
            max_weekly_loss_usd=kill_switch_config['max_weekly_loss_usd'],
            state_file=configs['state_files']['kill_switch']
        )
        logger.info(f"  Kill switch: Daily ${kill_switch_config['max_daily_loss_usd']}, "
                   f"Weekly ${kill_switch_config['max_weekly_loss_usd']}")

        # 2. Capital Limits (100% configurable)
        capital_config = configs['capital_limits']
        self.capital_limits = CapitalLimits(
            max_position_size_usd=capital_config['max_position_size_usd'],
            max_open_positions=capital_config['max_open_positions'],
            max_total_exposure_usd=capital_config['max_total_exposure_usd'],
            max_daily_trades=capital_config['max_daily_trades'],
            min_account_balance_usd=capital_config['min_account_balance_usd']
        )
        logger.info(f"  Capital limits: Max position ${capital_config['max_position_size_usd']}, "
                   f"Max {capital_config['max_open_positions']} positions")

        # 3. Slippage Protection (100% configurable)
        slippage_config = configs['slippage_protection']
        self.slippage_guard = SlippageProtection(
            max_slippage_percent=slippage_config['max_slippage_percent'],
            order_timeout_seconds=slippage_config['order_timeout_seconds'],
            enable_protection=slippage_config['enable_protection']
        )
        logger.info(f"  Slippage: Max {slippage_config['max_slippage_percent']}%, "
                   f"Timeout {slippage_config['order_timeout_seconds']}s")

        # Store authorization code
        self.auth_code = configs['authorization']['kill_switch_code']

    def execute_trade(self, symbol, side, amount, price):
        """
        Execute trade with all safety checks

        This is the pattern to integrate into TradingEngine
        """
        logger.info(f"Attempting trade: {side} {amount} {symbol} @ ${price}")

        # 1. Check global halt
        if self.global_halt:
            logger.error("🛑 Global halt active - trade blocked")
            return None

        # 2. Check kill switch
        if self.kill_switch.is_active():
            status = self.kill_switch.get_status()
            logger.error(f"🛑 Kill switch active: {status['reason']}")
            logger.error(f"   Daily loss: ${status['daily_loss']:.2f}")
            return None

        # 3. Validate capital limits
        position_size_usd = amount * price
        current_positions = 2  # Example: get from database
        current_exposure = 400.0  # Example: get from database
        current_balance = 1000.0  # Example: get from exchange API

        can_trade, reason = self.capital_limits.can_trade(
            proposed_size_usd=position_size_usd,
            current_open_positions=current_positions,
            current_total_exposure_usd=current_exposure,
            current_balance_usd=current_balance
        )

        if not can_trade:
            logger.error(f"🛑 Capital limit violation: {reason}")
            return None

        # 4. Execute with slippage protection
        logger.info(f"✅ All safety checks passed")
        logger.info(f"   Executing order with slippage protection...")

        # In real integration, would call:
        # success, order, error = self.slippage_guard.create_protected_order(
        #     exchange=self.exchange,
        #     symbol=symbol,
        #     side=side,
        #     amount=amount,
        #     current_price=price
        # )

        # Simulate successful execution
        order = {
            'id': '12345',
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price
        }

        # 5. Record trade
        self.capital_limits.record_trade()

        logger.info(f"✅ Trade executed: Order {order['id']}")
        return order

    def on_trade_close(self, pnl):
        """Handle trade close - record P&L for kill switch"""
        logger.info(f"Trade closed: P&L ${pnl:.2f}")

        # Record for kill switch
        self.kill_switch.record_pnl(pnl)

        # Check if kill switch triggered
        if self.kill_switch.is_active():
            status = self.kill_switch.get_status()
            logger.critical(f"🚨 KILL SWITCH ACTIVATED: {status['reason']}")
            logger.critical(f"   Daily loss: ${status['daily_loss']:.2f}")
            logger.critical(f"   Weekly loss: ${status['weekly_loss']:.2f}")
            # In real bot: send Telegram alert, halt trading

    def get_status(self):
        """Get comprehensive bot status"""
        if self.global_halt:
            return {"status": "GLOBAL_HALT", "trading": False}

        return {
            "exchange": self.exchange,
            "mode": self.mode,
            "strategy": self.strategy,
            "kill_switch": self.kill_switch.get_status(),
            "capital_limits": self.capital_limits.get_limits_status(
                current_open_positions=2,
                current_total_exposure_usd=400.0,
                current_balance_usd=1000.0
            ),
            "trading": not self.kill_switch.is_active()
        }


# ============================================================
# EXAMPLE USAGE - Different Bot Configurations
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Safety Systems Integration - 100% Customizable Examples")
    print("=" * 70)

    # Example 1: Binance LIVE bot with MICRO preset ($100 capital)
    print("\n" + "=" * 70)
    print("Example 1: Binance LIVE - MICRO preset ($100 capital)")
    print("=" * 70)

    binance_live_micro = ConfigurableTradingBot(
        exchange='BINANCE',
        mode='live',
        scaling_preset='micro'
    )

    # Attempt a trade
    print("\nAttempting $20 trade...")
    binance_live_micro.execute_trade(
        symbol='BTC/USDT',
        side='buy',
        amount=0.0002,
        price=95000.0
    )

    # Simulate losses to trigger kill switch
    print("\nSimulating losses...")
    binance_live_micro.on_trade_close(-5.0)   # -$5
    binance_live_micro.on_trade_close(-4.0)   # -$4 (total -$9)
    binance_live_micro.on_trade_close(-2.0)   # -$2 (total -$11, should trigger at $10)

    # Try to trade again (should be blocked)
    print("\nAttempting another trade after kill switch...")
    binance_live_micro.execute_trade(
        symbol='BTC/USDT',
        side='buy',
        amount=0.0002,
        price=95000.0
    )

    # Example 2: Binance PAPER bot (more tolerant)
    print("\n" + "=" * 70)
    print("Example 2: Binance PAPER - Default config")
    print("=" * 70)

    binance_paper = ConfigurableTradingBot(
        exchange='BINANCE',
        mode='paper'
    )

    print("\nAttempting $400 trade (would fail in live, ok in paper)...")
    binance_paper.execute_trade(
        symbol='ETH/USDT',
        side='buy',
        amount=0.15,
        price=3300.0
    )

    # Example 3: GridBot with strategy-specific limits
    print("\n" + "=" * 70)
    print("Example 3: Binance LIVE - GridBot strategy")
    print("=" * 70)

    binance_grid = ConfigurableTradingBot(
        exchange='BINANCE',
        mode='live',
        strategy='GridBot'
    )

    print("\nGridBot has custom limits (6 positions, $200 max)...")
    status = binance_grid.get_status()
    print(f"Max positions: {status['capital_limits']['open_positions']['max']}")
    print(f"Max position size: ${status['capital_limits']['position_size_limit']}")

    # Example 4: LUNO monitor mode (no trading)
    print("\n" + "=" * 70)
    print("Example 4: LUNO MONITOR mode (no trading allowed)")
    print("=" * 70)

    luno_monitor = ConfigurableTradingBot(
        exchange='LUNO',
        mode='monitor'
    )

    print("\nAttempting trade on monitor-only bot...")
    luno_monitor.execute_trade(
        symbol='BTC/ZAR',
        side='buy',
        amount=0.001,
        price=1500000.0
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ All examples complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. ✅ 100% customizable via YAML config")
    print("  2. ✅ NO hardcoded limits in code")
    print("  3. ✅ Exchange-specific configs (BINANCE/LUNO/MEXC)")
    print("  4. ✅ Mode-specific configs (paper/live/monitor)")
    print("  5. ✅ Strategy-specific overrides (GridBot/MomentumBot)")
    print("  6. ✅ Scaling presets (micro/small/medium/large)")
    print("  7. ✅ Separate kill switches for each bot")
    print("  8. ✅ Robust fail-safe design")
    print("  9. ✅ Scalable to unlimited bots")
    print("  10. ✅ Runtime reconfigurable")
    print("\nTo change limits: Edit config/safety_limits.yaml")
    print("No code changes required!")
