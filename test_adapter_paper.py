#!/usr/bin/env python3
"""
🧪 Adapter Pattern - Paper Trading Test
Version: 2026.01.09

Purpose: Test the adapter pattern core with minimal risk
- ONE strategy only (Grid Bot BTC)
- Paper trading mode
- Proven parameters from GRID_AND_DIP_STRATEGIES_REFERENCE.md
- Simple configuration for validation

This script tests the adapter architecture WITHOUT Priority 1 enhancements.
Priority 1 features (health monitor, adapter config, enhanced base) are tested separately.
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine

def check_stop_signal():
    """Check for manual stop signal file"""
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL")
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ TEST CONFIGURATION
# ==========================================
VERSION_ID = "2026.01.09-ADAPTER-TEST-BINANCE"
TRADING_MODE = 'paper'
EXCHANGE = 'BINANCE'  # User requested Binance only
# ==========================================

def main():
    print("=" * 80, flush=True)
    print(f"🧪 Adapter Pattern Test - Paper Trading (v{VERSION_ID})", flush=True)
    print(f"📊 Exchange: {EXCHANGE}", flush=True)
    print(f"🎯 Mode: {TRADING_MODE.upper()}", flush=True)
    print("=" * 80, flush=True)

    # Telegram config (optional)
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled", flush=True)
    else:
        print("⚠️  Telegram notifications disabled (no credentials)", flush=True)

    # Custom database path for test isolation
    db_path = f'data/test_adapter_{EXCHANGE.lower()}_paper.db'
    print(f"💾 Database: {db_path}", flush=True)

    # Initialize engine with adapter pattern
    print(f"\n🔧 Initializing TradingEngine with {EXCHANGE} adapter...", flush=True)
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange=EXCHANGE,
        db_path=db_path
    )

    print(f"✅ Engine initialized - Adapter: {engine.exchange.__class__.__name__}", flush=True)
    print(f"✅ Kill Switch Status: {'ACTIVE' if engine.exchange.kill_switch_active else 'INACTIVE'}", flush=True)

    # Add TWO grid bots - BTC and ETH (ADJUSTED for Risk Manager limits)
    print("\n🤖 Adding Grid Bot BTC ($250 budget - ADJUSTED)...", flush=True)
    engine.add_bot({
        'name': 'Test Grid Bot BTC',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],
        'amount': 10,           # ADJUSTED: $10 per trade (2% of $500 = fits MODERATE limit)
        'grid_levels': 20,      # PROVEN: 20 levels
        'atr_multiplier': 2.0,  # PROVEN: 2.0 ATR
        'atr_period': 14,
        'lower_limit': 85000,   # PROVEN: $85K lower
        'upper_limit': 110000,  # PROVEN: $110K upper ($25K range)
        'initial_balance': 250, # PROVEN: $250 budget
        'max_exposure_per_coin': 250
    })
    print("✅ Grid Bot BTC configured (Risk Manager compliant)", flush=True)

    print("\n🤖 Adding Grid Bot ETH ($250 budget - ADJUSTED)...", flush=True)
    engine.add_bot({
        'name': 'Test Grid Bot ETH',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],
        'amount': 10,           # ADJUSTED: $10 per trade (2% of $500 = fits MODERATE limit)
        'grid_levels': 30,      # PROVEN: 30 levels
        'atr_multiplier': 2.5,  # PROVEN: 2.5 ATR
        'atr_period': 14,
        'lower_limit': 2800,    # PROVEN: $2.8K lower
        'upper_limit': 4200,    # PROVEN: $4.2K upper ($1.4K range) - FIXED!
        'initial_balance': 250, # PROVEN: $250 budget
        'max_exposure_per_coin': 250
    })
    print("✅ Grid Bot ETH configured (Risk Manager compliant)", flush=True)

    # ⚠️ CRITICAL FIX: Update Risk Manager with actual starting capital
    # Risk Manager defaults to $10,000, but our test has only $500
    # Without this, it thinks we lost 95% and blocks all trading!
    total_initial_balance = sum(bot.get('initial_balance', 0) for bot in engine.active_bots)
    from decimal import Decimal
    engine.risk_manager.update_portfolio_value(Decimal(str(total_initial_balance)))
    engine.risk_manager.daily_start_value = Decimal(str(total_initial_balance))
    print(f"✅ Risk Manager initialized with ${total_initial_balance} starting capital", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("🚀 STARTING ADAPTER TEST - Paper Trading Only", flush=True)
    print("=" * 80, flush=True)
    print("\n📊 Expected Performance (ADJUSTED for Risk Manager - $500 total):", flush=True)
    print("   - BTC: 20 levels @ $10/trade, range $85K-$110K ($25K spread)", flush=True)
    print("   - ETH: 30 levels @ $10/trade, range $2.8K-$4.2K ($1.4K spread)", flush=True)
    print("   - Trades per day: ~10-15 grid fills (combined)", flush=True)
    print("   - Profit per BTC trade: ~$0.13 (1.27% net per round trip, scaled)", flush=True)
    print("   - Profit per ETH trade: ~$0.10-$0.14 (after Binance fees, scaled)", flush=True)
    print("   - Total capital deployed: $500 ($250 BTC + $250 ETH)", flush=True)
    print("   - ⚠️  Trade size ADJUSTED: $10 instead of $25 (Risk Manager 2% limit)", flush=True)
    print("\n⚠️  This is a TEST - Monitoring adapter pattern core only", flush=True)
    print("⚠️  Priority 1 enhancements NOT active (health monitor, config manager)", flush=True)
    print("\n💡 To stop: Create a file named 'STOP_SIGNAL' or press Ctrl+C\n", flush=True)

    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"🔄 Cycle #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            # Check stop signal
            if check_stop_signal():
                break

            # Run engine cycle
            engine.run_cycle()

            # Print adapter status
            if hasattr(engine.exchange, 'get_health_status'):
                health = engine.exchange.get_health_status()
                print(f"📡 Adapter Status: {health}")

            # Show active positions
            active_positions = engine.logger.get_open_positions()
            print(f"📊 Active Positions: {len(active_positions)}")

            # Sleep between cycles
            print(f"\n💤 Sleeping 300 seconds before next cycle...")
            time.sleep(300)  # 5 minutes between cycles

    except KeyboardInterrupt:
        print("\n\n🛑 Keyboard interrupt received. Shutting down gracefully...", flush=True)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 80, flush=True)
        print("🏁 ADAPTER TEST SHUTDOWN", flush=True)
        print("=" * 80, flush=True)

        # Show final stats
        active_positions = engine.logger.get_open_positions()
        print(f"\n📊 Final Active Positions: {len(active_positions)}", flush=True)

        # Show recent trades
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Count total trades
            cursor.execute("SELECT COUNT(*) FROM positions")
            total_trades = cursor.fetchone()[0]
            print(f"📈 Total Positions Created: {total_trades}", flush=True)

            # Count closed trades
            cursor.execute("SELECT COUNT(*) FROM positions WHERE status='CLOSED'")
            closed_count = cursor.fetchone()[0]
            
            if closed_count and closed_count > 0:
                print(f"✅ Closed Trades: {closed_count}", flush=True)
                # Calculate PnL from trades table if possible, or skip for now to avoid crash
                try:
                    cursor.execute("SELECT SUM(cost) FROM trades WHERE side='SELL'")
                    total_sells = cursor.fetchone()[0] or 0.0
                    cursor.execute("SELECT SUM(cost) FROM trades WHERE side='BUY'")
                    total_buys = cursor.fetchone()[0] or 0.0
                    total_pnl = total_sells - total_buys
                    print(f"💰 Total PnL (Approx): ${total_pnl:.2f}", flush=True)
                except:
                    print("⚠️  Could not calculate exact PnL from DB directly.", flush=True)
            else:
                print("⏳ No closed trades yet (needs more time)", flush=True)

            conn.close()
        except Exception as e:
            print(f"⚠️  Could not retrieve final stats: {e}", flush=True)

        print("\n✅ Test completed. Check logs and database for details.", flush=True)
        print(f"💾 Database location: {db_path}", flush=True)
        print(f"📄 Logs: bot.log", flush=True)

if __name__ == "__main__":
    main()
