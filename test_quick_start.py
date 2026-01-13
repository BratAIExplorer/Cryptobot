#!/usr/bin/env python3
"""
QUICK START TEST - $500 Portfolio
Tests Grid Bot (BTC + ETH) with Take Profit exit strategy

Configuration:
- Capital: $500 ($250 BTC + $250 ETH)
- Mode: Paper trading (SAFE - no real money)
- Exchange: BINANCE
- Duration: 48 hours recommended
- Strategies: Grid Bot for entry + Take Profit for exits
"""

import sys
import os
import time
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine
from strategies.grid_strategy_v2 import DynamicGridStrategy
from strategies.take_profit_strategy import TakeProfitStrategy

def main():
    print("=" * 60)
    print("🚀 QUICK START TEST - $500 Portfolio")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Configuration:")
    print("  💰 Capital: $500 ($250 BTC + $250 ETH)")
    print("  📊 Mode: Paper Trading (SAFE)")
    print("  🏦 Exchange: BINANCE")
    print("  🤖 Strategies: Grid Bot + Take Profit")
    print("=" * 60)
    print()

    # Initialize TradingEngine
    print("📡 Initializing Trading Engine...")
    engine = TradingEngine(
        mode='paper',                                      # Paper mode (safe)
        exchange='BINANCE',                                # Binance exchange
        db_path='data/quick_start_test.db',               # New database
        telegram_config=None                               # No Telegram for now
    )

    print("✅ Trading Engine initialized")
    print(f"   Exchange: {engine.exchange_name}")
    print(f"   Mode: {engine.mode}")
    print(f"   Database: data/quick_start_test.db")
    print()

    # ============================================
    # STRATEGY #1: BTC Grid Bot (Entry Strategy)
    # ============================================
    print("📊 Configuring BTC Grid Bot...")
    btc_grid_config = {
        'symbol': 'BTC/USDT',
        'trade_amount': 25,          # $25 per grid fill
        'num_grids': 20,             # 20 grid levels
        'lower_price': 85000,        # Grid bottom
        'upper_price': 110000,       # Grid top
        'atr_multiplier': 2.0,       # Volatility adjustment
        'budget': 250                # $250 allocated
    }

    btc_grid = DynamicGridStrategy(btc_grid_config)
    print("✅ BTC Grid Bot configured")
    print(f"   Symbol: BTC/USDT")
    print(f"   Budget: $250")
    print(f"   Grid Levels: 20")
    print(f"   Range: $85,000 - $110,000")
    print()

    # ============================================
    # STRATEGY #2: ETH Grid Bot (Entry Strategy)
    # ============================================
    print("📊 Configuring ETH Grid Bot...")
    eth_grid_config = {
        'symbol': 'ETH/USDT',
        'trade_amount': 25,          # $25 per grid fill
        'num_grids': 30,             # 30 grid levels
        'lower_price': 2800,         # Grid bottom
        'upper_price': 4200,         # Grid top
        'atr_multiplier': 2.5,       # Volatility adjustment
        'budget': 250                # $250 allocated
    }

    eth_grid = DynamicGridStrategy(eth_grid_config)
    print("✅ ETH Grid Bot configured")
    print(f"   Symbol: ETH/USDT")
    print(f"   Budget: $250")
    print(f"   Grid Levels: 30")
    print(f"   Range: $2,800 - $4,200")
    print()

    # ============================================
    # STRATEGY #3: Take Profit (Exit Strategy)
    # ============================================
    print("📊 Configuring Take Profit Strategy (NEW!)...")
    take_profit_config = {
        'profit_target_percent': 3.0,    # Exit at 3% profit
        'trailing_stop_percent': 1.0,    # Trail by 1%
        'stop_loss_percent': 2.0,        # Max loss 2%
        'position_size_percent': 10.0    # Not used (Grid Bot handles sizing)
    }

    take_profit = TakeProfitStrategy(take_profit_config)
    print("✅ Take Profit Strategy configured")
    print(f"   Profit Target: 3%")
    print(f"   Trailing Stop: 1%")
    print(f"   Stop Loss: 2%")
    print(f"   Purpose: Exit Grid positions at profit")
    print()

    # Register strategies with engine
    print("🔗 Registering strategies with engine...")
    engine.active_bots = [btc_grid, eth_grid, take_profit]
    print(f"✅ {len(engine.active_bots)} strategies registered")
    print()

    # Display risk settings
    print("🛡️  Risk Management Settings:")
    print(f"   Daily Loss Limit: {engine.risk_manager.max_daily_loss_percent}%")
    print(f"   Max Position Size: {engine.risk_manager.max_position_size_percent}%")
    print(f"   Max Open Positions: {engine.risk_manager.max_positions}")
    print()

    # Start the engine
    print("=" * 60)
    print("🚀 STARTING TRADING ENGINE")
    print("=" * 60)
    print()
    print("⚠️  MONITORING TIPS:")
    print("   - Run: tail -f logs/quick_start_test.log")
    print("   - Check positions: sqlite3 data/quick_start_test.db 'SELECT * FROM positions;'")
    print("   - Monitor P&L: bash monitor_bot.sh")
    print()
    print("⏸️  TO STOP:")
    print("   - Press Ctrl+C")
    print("   - Or: kill <PID>")
    print("   - Or: touch STOP_SIGNAL")
    print()
    print("🔄 Starting trading cycles...")
    print()

    try:
        # Start the engine (runs indefinitely until stopped)
        engine.start()

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("🛑 STOPPING - Keyboard Interrupt")
        print("=" * 60)
        engine.is_running = False

        # Give time for cleanup
        time.sleep(2)

        print()
        print("✅ Test stopped cleanly")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR OCCURRED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print()
        print("=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)

        # Get final positions
        try:
            open_positions = engine.logger.get_open_positions()
            all_trades = engine.logger.get_all_trades()

            print(f"Open Positions: {len(open_positions)}")
            print(f"Total Trades: {len(all_trades)}")

            if all_trades:
                total_pnl = sum(t.get('profit', 0) for t in all_trades)
                print(f"Total P&L: ${total_pnl:.2f}")

                winning = len([t for t in all_trades if t.get('profit', 0) > 0])
                print(f"Win Rate: {winning}/{len(all_trades)} ({winning/len(all_trades)*100:.1f}%)")

        except Exception as e:
            print(f"⚠️  Could not retrieve final stats: {e}")

        print()
        print("📁 Data saved to:")
        print("   Database: data/quick_start_test.db")
        print("   Logs: logs/quick_start_test.log")
        print()
        print("👋 Test complete!")
        print()


if __name__ == "__main__":
    main()
