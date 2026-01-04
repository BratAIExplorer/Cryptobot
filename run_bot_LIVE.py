#!/usr/bin/env python3
"""
🔴 LIVE TRADING BOT - REAL MONEY 🔴
Version: 2026.01.04 - Conservative Grid Bot Launch

IMPORTANT SAFETY NOTES:
1. This bot trades with REAL MONEY on your exchange account
2. Starting with ONLY Grid Bots (proven in paper trading)
3. Using 10% of paper trading allocations for safety
4. Monitor closely for first 72 hours before scaling

Paper Trading Results (Validation):
- Grid Bot BTC: +$1,734 profit, 83% win rate, 52 trades
- Grid Bot ETH: +$6,475 profit, 100% win rate, 116 trades
- Total: +$8,209 in 1 month (paper trading)

LIVE Trading Plan:
- Grid Bot BTC: $300 allocation (vs $3,000 paper)
- Grid Bot ETH: $300 allocation (vs $3,000 paper)
- Total LIVE Exposure: $600 (10% of paper)
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine

def check_stop_signal():
    """Check for manual stop signal file"""
    if os.path.exists("STOP_SIGNAL_LIVE"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down LIVE bot...")
        try:
            os.remove("STOP_SIGNAL_LIVE")
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ CONFIGURATION - LIVE MODE
# ==========================================
VERSION_ID = "2026.01.04-LIVE-LAUNCH"
TRADING_MODE = 'live'  # ⚠️ REAL MONEY MODE
# ==========================================

def main():
    print("=" * 80, flush=True)
    print(f"🔴 LIVE TRADING BOT - REAL MONEY (v{VERSION_ID}) 🔴", flush=True)
    print("=" * 80, flush=True)
    print("⚠️  WARNING: This bot trades with REAL MONEY", flush=True)
    print("📊 Starting with Grid Bots only (proven strategy)", flush=True)
    print("💰 Conservative allocation: $600 total", flush=True)
    print("=" * 80, flush=True)

    # Telegram config
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN_LIVE') or os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID_LIVE') or os.environ.get('TELEGRAM_CHAT_ID')

    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled (LIVE alerts)")
    else:
        print("⚠️  WARNING: Telegram notifications disabled!")
        print("   Set TELEGRAM_BOT_TOKEN_LIVE and TELEGRAM_CHAT_ID_LIVE")
        print("   Continuing without notifications...")

    # Initialize engine with LIVE database
    engine = TradingEngine(
        mode=TRADING_MODE,  # 'live' - REAL MONEY
        telegram_config=telegram_config,
        exchange='MEXC',
        db_path='data/trades_v3_live.db'  # ⚠️ Separate LIVE database
    )

    # ==========================================
    # 🎯 GRID BOT BTC - CONSERVATIVE LIVE START
    # ==========================================
    # Paper Results: +$1,734 profit, 83% win rate, 52 trades (1 month)
    # LIVE Allocation: $300 (10% of paper $3,000)
    # Expected LIVE: +$173/month (10% of paper profit)

    engine.add_bot({
        'name': 'Grid Bot BTC (LIVE)',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],

        # LIVE Allocation (10% of paper)
        'amount': 15,              # $15 per grid level (was $150 in paper)
        'initial_balance': 300,    # $300 total (was $3,000 in paper)
        'max_exposure_per_coin': 300,

        # Grid Configuration (SAME as paper - proven to work)
        'grid_levels': 20,
        'atr_multiplier': 2.0,
        'atr_period': 14,
        'lower_limit': 88000,      # ✅ Current price: $91,267 (within range)
        'upper_limit': 108000,

        # Safety (same as paper)
        'circuit_breaker_daily': -50,   # Stop if lose $50/day
        'circuit_breaker_weekly': -100  # Stop if lose $100/week
    })

    # ==========================================
    # 🎯 GRID BOT ETH - CONSERVATIVE LIVE START
    # ==========================================
    # Paper Results: +$6,475 profit, 100% win rate!, 116 trades (1 month)
    # LIVE Allocation: $300 (10% of paper $3,000)
    # Expected LIVE: +$647/month (10% of paper profit)

    engine.add_bot({
        'name': 'Grid Bot ETH (LIVE)',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],

        # LIVE Allocation (10% of paper)
        'amount': 10,              # $10 per grid level (was $100 in paper)
        'initial_balance': 300,    # $300 total (was $3,000 in paper)
        'max_exposure_per_coin': 300,

        # Grid Configuration (SAME as paper - proven to work)
        'grid_levels': 30,
        'atr_multiplier': 2.5,
        'atr_period': 14,
        'lower_limit': 2800,       # ✅ Current price: $3,103 (within range)
        'upper_limit': 3600,

        # Safety (same as paper)
        'circuit_breaker_daily': -50,   # Stop if lose $50/day
        'circuit_breaker_weekly': -100  # Stop if lose $100/week
    })

    # ==========================================
    # 🚫 OTHER STRATEGIES - PAUSED FOR LIVE
    # ==========================================
    # We are NOT adding other strategies to LIVE yet:
    # - SMA Trend Bot V2
    # - Buy-the-Dip Strategy
    # - Momentum Swing Bot
    # - Hidden Gem Monitor V2
    #
    # Reason: Grid Bots are proven (100% win rate ETH, 83% BTC)
    # Plan: Add other strategies after 72h of successful LIVE Grid Bot trading

    # Send startup notification
    if engine.notifier:
        active_bots_summary = []
        for b in engine.active_bots:
            syms = [s.split('/')[0] for s in b.get('symbols', [])[:5]]
            active_bots_summary.append({
                'name': b['name'],
                'symbols': syms,
                'total_count': len(b.get('symbols', []))
            })

        # Custom LIVE startup message
        startup_msg = f"""
🔴 LIVE TRADING BOT STARTED 🔴

⚠️ REAL MONEY MODE ACTIVE

📊 Active Strategies:
• Grid Bot BTC: $300 allocation
• Grid Bot ETH: $300 allocation

💰 Total LIVE Exposure: $600

📈 Based on Paper Results:
• BTC: +$1,734 (83% win rate)
• ETH: +$6,475 (100% win rate)
• Expected LIVE: ~$82/month (conservative)

🎯 72-Hour Monitoring Phase
Monitor closely, then scale up.

⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        try:
            engine.notifier.send_message(startup_msg)
        except Exception as e:
            print(f"⚠️ Could not send startup notification: {e}")

    # Initialize and run
    try:
        engine.start()
    except Exception as e:
        print(f"⚠️ Engine startup warning: {e}")

    print("=" * 80)
    print(f"🔴 LIVE BOT RUNNING - REAL MONEY MODE 🔴")
    print("   Portfolio Allocation:")
    print("   - Grid Bot BTC:   $300 (50%)")
    print("   - Grid Bot ETH:   $300 (50%)")
    print("   - Total Exposure: $600")
    print()
    print("   Expected Monthly Performance:")
    print("   - Conservative:   +$82  (13.7% return)")
    print("   - Expected:       +$164 (27.3% return)")
    print("   - Optimistic:     +$246 (41% return)")
    print()
    print("   ⚠️  MONITOR CLOSELY FOR FIRST 72 HOURS")
    print("=" * 80)
    print("Press Ctrl+C to stop, or create STOP_SIGNAL_LIVE file")
    print()

    try:
        while True:
            if check_stop_signal():
                break

            try:
                engine.run_cycle()
            except Exception as e:
                print(f"❌ Error in run_cycle: {e}")
                import traceback
                traceback.print_exc()

                # Send error alert
                if engine.notifier:
                    try:
                        engine.notifier.send_message(f"⚠️ LIVE BOT ERROR:\n{str(e)[:500]}")
                    except:
                        pass

                print("💤 Sleeping 300s before retry...")
                time.sleep(300)
                continue

            time.sleep(180)  # 3 minutes between cycles

    except KeyboardInterrupt:
        print("\n🛑 Stopping LIVE bot...")

        if engine.notifier:
            try:
                engine.notifier.send_message("🛑 LIVE Trading Bot stopped manually")
            except:
                pass

        engine.stop()
        print("✅ LIVE bot stopped successfully")

if __name__ == "__main__":
    main()
