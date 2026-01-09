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

    # Add ONE bot for testing - Grid Bot BTC (adjusted for $500 budget)
    print("\n🤖 Adding Grid Bot BTC ($500 realistic budget)...", flush=True)
    engine.add_bot({
        'name': 'Test Grid Bot BTC',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],
        'amount': 25,           # $25 per trade ($500/20 levels)
        'grid_levels': 20,      # Proven levels
        'atr_multiplier': 2.0,
        'atr_period': 14,
        'lower_limit': 85000,   # Proven range
        'upper_limit': 110000,
        'initial_balance': 500, # Realistic starting capital
        'max_exposure_per_coin': 500
    })

    print("✅ Grid Bot BTC configured", flush=True)
    print("\n" + "=" * 80, flush=True)
    print("🚀 STARTING ADAPTER TEST - Paper Trading Only", flush=True)
    print("=" * 80, flush=True)
    print("\n📊 Expected Performance (based on $500 budget):", flush=True)
    print("   - Trades per day: ~5-10 grid fills", flush=True)
    print("   - Profit per trade: ~$0.20-$0.30 (after Binance fees)", flush=True)
    print("   - Grid range: $85,000 - $110,000", flush=True)
    print("   - Capital deployed: $500 (realistic starting amount)", flush=True)
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

            # Count closed trades with PnL
            cursor.execute("""
                SELECT COUNT(*), ROUND(SUM(realized_pnl), 2), ROUND(AVG(realized_pnl), 2)
                FROM positions
                WHERE status='CLOSED' AND realized_pnl IS NOT NULL
            """)
            closed_count, total_pnl, avg_pnl = cursor.fetchone()
            if closed_count and closed_count > 0:
                print(f"✅ Closed Trades: {closed_count}", flush=True)
                print(f"💰 Total PnL: ${total_pnl:.2f}", flush=True)
                print(f"📊 Average PnL: ${avg_pnl:.2f}", flush=True)
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
