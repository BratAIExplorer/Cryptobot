#!/usr/bin/env python3
"""
Diagnostic Script for LIVE Trading Bot
Checks why Grid Bot has zero trades
"""
import sqlite3
import os
from datetime import datetime, timedelta

def check_database(db_path):
    """Check if database exists and analyze contents"""
    print(f"\n{'='*80}")
    print(f"📊 Analyzing Database: {db_path}")
    print(f"{'='*80}\n")

    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database not found at {db_path}")
        print("\n💡 Solution: The LIVE bot may be using a different database path")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check bot_status table
    print("🤖 Bot Status Check:")
    try:
        cursor.execute("SELECT strategy, status, total_trades, total_pnl, wallet_balance, last_heartbeat FROM bot_status")
        bots = cursor.fetchall()

        if not bots:
            print("   ❌ NO BOTS REGISTERED")
            print("\n   💡 This means the bot service is running but no strategies are active!")
            print("   💡 Check run_bot_LIVE.py configuration")
        else:
            print(f"   ✅ Found {len(bots)} registered bots:")
            for bot in bots:
                strategy, status, trades, pnl, balance, heartbeat = bot
                print(f"\n   📌 {strategy}")
                print(f"      Status: {status}")
                print(f"      Trades: {trades}")
                print(f"      P&L: ${pnl:.2f}")
                print(f"      Balance: ${balance:.2f}")
                print(f"      Last Heartbeat: {heartbeat}")
    except Exception as e:
        print(f"   ⚠️  Error checking bot_status: {e}")

    # Check trades in last 24 hours
    print(f"\n{'='*80}")
    print("📈 Trade Activity (Last 24 Hours):")
    try:
        cursor.execute("""
            SELECT COUNT(*) as total_trades,
                   SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                   SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                   ROUND(SUM(cost), 2) as total_volume
            FROM trades
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        result = cursor.fetchone()
        total_trades, buys, sells, volume = result

        print(f"   Total Trades: {total_trades}")
        print(f"   Buys: {buys}")
        print(f"   Sells: {sells}")
        print(f"   Total Volume: ${volume if volume else 0:.2f}")

        if total_trades == 0:
            print("\n   ❌ ZERO TRADES IN LAST 24 HOURS")
            print("   💡 This confirms the Grid Bot is not executing")
    except Exception as e:
        print(f"   ⚠️  Error checking trades: {e}")

    # Check open positions
    print(f"\n{'='*80}")
    print("💼 Open Positions:")
    try:
        cursor.execute("""
            SELECT symbol, strategy, entry_price, amount, unrealized_pnl_usd, entry_date
            FROM positions
            WHERE status='OPEN'
        """)
        positions = cursor.fetchall()

        if not positions:
            print("   📭 No open positions")
        else:
            print(f"   ✅ {len(positions)} open positions:")
            for pos in positions:
                symbol, strategy, entry, amount, pnl, entry_date = pos
                print(f"\n   📌 {symbol} ({strategy})")
                print(f"      Entry: ${entry:.4f}")
                print(f"      Amount: {amount:.4f}")
                print(f"      P&L: ${pnl:.2f}")
                print(f"      Entry Date: {entry_date}")
    except Exception as e:
        print(f"   ⚠️  Error checking positions: {e}")

    # Check circuit breaker
    print(f"\n{'='*80}")
    print("🔴 Circuit Breaker Status:")
    try:
        cursor.execute("""
            SELECT is_open, consecutive_errors, last_error_time, last_error_message
            FROM circuit_breaker
            WHERE id=1
        """)
        result = cursor.fetchone()

        if result:
            is_open, errors, error_time, error_msg = result
            if is_open:
                print(f"   ⚠️  CIRCUIT BREAKER TRIGGERED")
                print(f"      Consecutive Errors: {errors}")
                print(f"      Last Error Time: {error_time}")
                print(f"      Last Error: {error_msg}")
            else:
                print(f"   ✅ Circuit Breaker: Clear")
                print(f"      Consecutive Errors: {errors}")
        else:
            print("   ℹ️  No circuit breaker data")
    except Exception as e:
        print(f"   ⚠️  Error checking circuit breaker: {e}")

    conn.close()
    return True

def check_live_bot_process():
    """Check if LIVE bot process is running"""
    print(f"\n{'='*80}")
    print("🔍 Process Status Check:")
    print(f"{'='*80}\n")

    import subprocess

    # Check systemd service
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'cryptobot_live.service'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip() == 'active':
            print("   ✅ cryptobot_live.service is RUNNING")
        else:
            print(f"   ❌ cryptobot_live.service is {result.stdout.strip()}")
    except Exception as e:
        print(f"   ⚠️  Cannot check systemd service: {e}")

    # Check if process is actually running
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        if 'run_bot_LIVE.py' in result.stdout:
            print("   ✅ run_bot_LIVE.py process found")
            # Extract process details
            for line in result.stdout.split('\n'):
                if 'run_bot_LIVE.py' in line:
                    print(f"      {line}")
        else:
            print("   ❌ run_bot_LIVE.py process NOT found")
            print("   💡 Service may be running but bot script is not executing")
    except Exception as e:
        print(f"   ⚠️  Cannot check processes: {e}")

def main():
    print("\n" + "="*80)
    print("🔧 LIVE TRADING BOT DIAGNOSTIC")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Check multiple possible database locations
    possible_db_paths = [
        '/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db',
        '/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3.db',
        '/Antigravity/antigravity/scratch/crypto_trading_bot/data/trades_v3_live.db',
        'data/trades_v3_live.db',
    ]

    db_found = False
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            db_found = True
            check_database(db_path)
            break

    if not db_found:
        print(f"\n{'='*80}")
        print("❌ CRITICAL: No LIVE database found!")
        print(f"{'='*80}\n")
        print("Searched locations:")
        for path in possible_db_paths:
            print(f"   - {path}")
        print("\n💡 The LIVE bot may be configured with a different database path")

    # Check process status
    check_live_bot_process()

    # Final recommendations
    print(f"\n{'='*80}")
    print("📋 RECOMMENDATIONS:")
    print(f"{'='*80}\n")

    if not db_found or True:  # Always show recommendations
        print("1. Check /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/run_bot_LIVE.py")
        print("   - Verify strategies are configured (engine.add_bot calls)")
        print("   - Check db_path in TradingEngine initialization")
        print("")
        print("2. Check systemd service logs:")
        print("   sudo journalctl -u cryptobot_live.service -n 100")
        print("")
        print("3. Check for errors in bot log files:")
        print("   tail -n 100 /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/*.log")
        print("")
        print("4. Restart the LIVE bot service:")
        print("   sudo systemctl restart cryptobot_live.service")
        print("")
        print("5. Monitor the dashboard at http://72.60.40.29:8501")
        print("   - Switch to LIVE mode")
        print("   - Check if bots appear after restart")

    print(f"\n{'='*80}")
    print("Diagnostic Complete")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
