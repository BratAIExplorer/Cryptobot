#!/usr/bin/env python3
"""
MEXC Live Trading Bot - CONSERVATIVE START
Balance: $218 USDT
Phase 1: Grid Bots Only (2 strategies, low risk)

CRITICAL: This config is for LIVE TRADING with REAL MONEY!
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine

def check_stop_signal():
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL")
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ MEXC LIVE CONFIGURATION
# ==========================================
TRADING_MODE = 'live'  # 🔴 LIVE TRADING MODE
EXCHANGE = 'MEXC'
DATABASE_FILE = 'data/trades_mexc_live.db'
# ==========================================

def main():
    print("=" * 80)
    print("🔴 MEXC LIVE TRADING BOT - PHASE 1: GRID BOTS ONLY")
    print("=" * 80)
    print(f"⚠️  WARNING: LIVE TRADING WITH REAL MONEY!")
    print(f"Exchange: {EXCHANGE}")
    print(f"Mode: {TRADING_MODE}")
    print(f"Database: {DATABASE_FILE}")
    print(f"Balance: $218 USDT")
    print(f"Allocation: $140 (keep $78 reserve)")
    print("=" * 80)

    # Confirm before starting
    print("\n⏸️  SAFETY CHECK:")
    print("   - API keys configured? (check .env)")
    print("   - Position sizes reviewed? ($80 BTC, $60 ETH)")
    print("   - Emergency stop ready? (touch STOP_SIGNAL)")
    print("   - Telegram alerts working?")
    print("\n⚠️  Press Ctrl+C within 10 seconds to abort...")

    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n❌ Aborted by user. No trades executed.")
        return

    print("\n🚀 Starting live trading in 3 seconds...")
    time.sleep(3)

    # Telegram config
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️  Telegram notifications disabled (RECOMMENDED to enable!)")

    # Initialize engine
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange=EXCHANGE,
        db_path=DATABASE_FILE
    )

    print("\n" + "=" * 80)
    print("💰 PHASE 1 CAPITAL ALLOCATION: $140 Total")
    print("=" * 80)

    # ==========================================
    # STRATEGY 1: GRID BOT BTC - $80
    # ==========================================
    print("\n1️⃣  Grid Bot BTC: $80 (5 levels)")
    engine.add_bot({
        'name': 'MEXC_Grid_BTC_Live',
        'type': 'GRID',
        'symbols': ['BTC/USDT'],
        'amount': 80,           # $80 total allocation
        'grid_levels': 5,       # 5 grid levels (conservative)
        'range_pct': 0.08,      # 8% range (tight for BTC)
        'profit_per_grid': 0.015, # 1.5% profit per grid fill
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })

    # ==========================================
    # STRATEGY 2: GRID BOT ETH - $60
    # ==========================================
    print("2️⃣  Grid Bot ETH: $60 (5 levels)")
    engine.add_bot({
        'name': 'MEXC_Grid_ETH_Live',
        'type': 'GRID',
        'symbols': ['ETH/USDT'],
        'amount': 60,           # $60 total allocation
        'grid_levels': 5,       # 5 grid levels
        'range_pct': 0.10,      # 10% range (ETH more volatile)
        'profit_per_grid': 0.02, # 2% profit per grid fill
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })

    print("\n" + "=" * 80)
    print("✅ 2 Grid Bots configured!")
    print("💰 Total Allocated: $140 USDT")
    print("💰 Reserve: $78 USDT (35% safety buffer)")
    print("🗄️  Database: data/trades_mexc_live.db")
    print("🏷️  All trades tagged: exchange='MEXC', mode='LIVE'")
    print("=" * 80)

    print("\n📊 EXPECTED PERFORMANCE:")
    print("   - Daily trades: 5-15 grid fills")
    print("   - Daily profit target: $1-3 (0.5-1.5%)")
    print("   - Weekly profit target: $10-20")
    print("   - Risk level: LOW (grid bots are stable)")

    print("\n⚠️  MONITORING SCHEDULE:")
    print("   - First hour: Check every 15 minutes")
    print("   - First 24h: Check every 2-4 hours")
    print("   - After: Daily review minimum")

    print("\n🛑 EMERGENCY STOP:")
    print("   touch STOP_SIGNAL")
    print("   or: kill $(cat bot.pid)")
    print("   or: Ctrl+C")

    # Run the engine
    print("\n🚀 Starting MEXC live bots NOW...")
    try:
        engine.start()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Shutting down gracefully...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ MEXC bot stopped.")
        print(f"📊 Review results: python analyze_trades.py --db {DATABASE_FILE}")

if __name__ == "__main__":
    main()
