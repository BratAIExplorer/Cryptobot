#!/usr/bin/env python3
"""
Paper Trading Grid Bot Performance Analysis
Checks Grid Bot performance in the last 24 hours
"""
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Try multiple possible database locations
DB_PATHS = [
    '/Antigravity/antigravity/scratch/crypto_trading_bot/data/trades_v3_paper.db',
    '/home/user/Cryptobot/data/trades_v3_paper.db',
    'data/trades_v3_paper.db',
]

def find_database():
    """Find the paper trading database"""
    for db_path in DB_PATHS:
        if os.path.exists(db_path):
            return db_path
    return None

def analyze_grid_bot_performance(db_path):
    """Analyze Grid Bot performance"""
    print("=" * 80)
    print("📊 PAPER TRADING - GRID BOT PERFORMANCE ANALYSIS")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # === GRID BOT STATUS ===
    print("=" * 80)
    print("🤖 GRID BOT STATUS")
    print("=" * 80)
    cursor.execute("""
        SELECT strategy, status, total_trades, total_pnl, wallet_balance,
               last_heartbeat, started_at
        FROM bot_status
        WHERE strategy LIKE '%Grid%'
    """)
    grid_bots = cursor.fetchall()

    if not grid_bots:
        print("❌ NO GRID BOTS FOUND in bot_status table")
        print("💡 Grid Bots may not be registered or using different strategy names")
    else:
        for bot in grid_bots:
            strategy, status, trades, pnl, balance, heartbeat, started = bot
            print(f"\n📌 {strategy}")
            print(f"   Status: {status}")
            print(f"   Total Trades: {trades}")
            print(f"   Total P&L: ${pnl:.2f}")
            print(f"   Wallet Balance: ${balance:.2f}")
            print(f"   Started: {started}")
            print(f"   Last Heartbeat: {heartbeat}")

    # === GRID BOT TRADES (LAST 24 HOURS) ===
    print(f"\n{'=' * 80}")
    print("📈 GRID BOT TRADES (LAST 24 HOURS)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            strategy,
            COUNT(*) as total_trades,
            SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
            ROUND(SUM(cost), 2) as total_volume,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade
        FROM trades
        WHERE strategy LIKE '%Grid%'
          AND timestamp > datetime('now', '-24 hours')
        GROUP BY strategy
    """)

    grid_trades_24h = cursor.fetchall()

    if not grid_trades_24h:
        print("❌ ZERO GRID BOT TRADES IN LAST 24 HOURS")
        print()
        print("Possible Reasons:")
        print("1. Grid Bot is not running")
        print("2. Price is outside grid range")
        print("3. Market is too stable (no price movement)")
        print("4. Grid Bot just started (no time for trades yet)")
    else:
        for trade_data in grid_trades_24h:
            strategy, total, buys, sells, volume, first, last = trade_data
            print(f"\n📊 {strategy}")
            print(f"   Total Trades: {total}")
            print(f"   Buys: {buys}")
            print(f"   Sells: {sells}")
            print(f"   Total Volume: ${volume:.2f}")
            print(f"   First Trade: {first}")
            print(f"   Last Trade: {last}")

            # Calculate time since last trade
            if last:
                try:
                    last_trade_time = datetime.fromisoformat(last)
                    hours_ago = (datetime.now() - last_trade_time).total_seconds() / 3600
                    print(f"   ⏰ Last trade was {hours_ago:.1f} hours ago")

                    if hours_ago > 12:
                        print(f"   ⚠️  WARNING: No trades in {hours_ago:.1f} hours!")
                except:
                    pass

    # === ALL GRID BOT TRADES (ALL TIME) ===
    print(f"\n{'=' * 80}")
    print("📜 GRID BOT TRADES (ALL TIME)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            strategy,
            symbol,
            COUNT(*) as total_trades,
            SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
            ROUND(SUM(cost), 2) as total_volume,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade
        FROM trades
        WHERE strategy LIKE '%Grid%'
        GROUP BY strategy, symbol
        ORDER BY total_trades DESC
    """)

    all_grid_trades = cursor.fetchall()

    if not all_grid_trades:
        print("❌ NO GRID BOT TRADES FOUND (ALL TIME)")
    else:
        print(f"Found {len(all_grid_trades)} Grid Bot trading pairs:")
        print()
        for trade_data in all_grid_trades:
            strategy, symbol, total, buys, sells, volume, first, last = trade_data
            print(f"📌 {strategy} - {symbol}")
            print(f"   Total Trades: {total}")
            print(f"   Buys: {buys} | Sells: {sells}")
            print(f"   Volume: ${volume:.2f}")
            print(f"   First: {first}")
            print(f"   Last: {last}")
            print()

    # === RECENT GRID BOT TRADES (LAST 10) ===
    print("=" * 80)
    print("📋 RECENT GRID BOT TRADES (LAST 10)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            datetime(timestamp) as time,
            strategy,
            symbol,
            side,
            ROUND(price, 2) as price,
            ROUND(amount, 6) as amount,
            ROUND(cost, 2) as cost,
            exchange
        FROM trades
        WHERE strategy LIKE '%Grid%'
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    recent_trades = cursor.fetchall()

    if not recent_trades:
        print("❌ No recent Grid Bot trades found")
    else:
        print(f"{'Time':<20} {'Strategy':<20} {'Symbol':<12} {'Side':<6} {'Price':<10} {'Amount':<12} {'Cost':<10}")
        print("-" * 100)
        for trade in recent_trades:
            time, strategy, symbol, side, price, amount, cost, exchange = trade
            print(f"{time:<20} {strategy[:19]:<20} {symbol:<12} {side:<6} ${price:<9.2f} {amount:<12.6f} ${cost:<9.2f}")

    # === GRID BOT OPEN POSITIONS ===
    print(f"\n{'=' * 80}")
    print("💼 GRID BOT OPEN POSITIONS")
    print("=" * 80)

    cursor.execute("""
        SELECT
            symbol,
            strategy,
            ROUND(entry_price, 4) as entry_price,
            ROUND(current_price, 4) as current_price,
            ROUND(amount, 6) as amount,
            ROUND(unrealized_pnl_usd, 2) as pnl,
            ROUND(unrealized_pnl_pct, 2) as pnl_pct,
            datetime(entry_date) as entry_time
        FROM positions
        WHERE strategy LIKE '%Grid%'
          AND status = 'OPEN'
        ORDER BY entry_date DESC
    """)

    open_positions = cursor.fetchall()

    if not open_positions:
        print("📭 No open Grid Bot positions")
    else:
        print(f"Found {len(open_positions)} open positions:")
        print()
        for pos in open_positions:
            symbol, strategy, entry, current, amount, pnl, pnl_pct, entry_time = pos
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            print(f"{pnl_emoji} {symbol} ({strategy})")
            print(f"   Entry: ${entry:.4f} | Current: ${current:.4f}")
            print(f"   Amount: {amount:.6f}")
            print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"   Opened: {entry_time}")
            print()

    # === GRID BOT P&L SUMMARY ===
    print("=" * 80)
    print("💰 GRID BOT P&L SUMMARY")
    print("=" * 80)

    cursor.execute("""
        SELECT
            strategy,
            COUNT(*) as closed_positions,
            SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
            ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
            ROUND(SUM(unrealized_pnl_usd), 2) as total_pnl,
            ROUND(AVG(unrealized_pnl_usd), 2) as avg_pnl,
            ROUND(MAX(unrealized_pnl_usd), 2) as best_trade,
            ROUND(MIN(unrealized_pnl_usd), 2) as worst_trade
        FROM positions
        WHERE strategy LIKE '%Grid%'
          AND status = 'CLOSED'
        GROUP BY strategy
    """)

    pnl_summary = cursor.fetchall()

    if not pnl_summary:
        print("No closed Grid Bot positions yet")
    else:
        for summary in pnl_summary:
            strategy, closed, wins, losses, win_rate, total_pnl, avg_pnl, best, worst = summary
            print(f"\n📊 {strategy}")
            print(f"   Closed Positions: {closed}")
            print(f"   Wins: {wins} | Losses: {losses}")
            print(f"   Win Rate: {win_rate:.2f}%")
            print(f"   Total P&L: ${total_pnl:.2f}")
            print(f"   Average P&L: ${avg_pnl:.2f}")
            print(f"   Best Trade: ${best:.2f}")
            print(f"   Worst Trade: ${worst:.2f}")

    conn.close()

    # === RECOMMENDATIONS ===
    print(f"\n{'=' * 80}")
    print("📋 ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)

    if not grid_bots:
        print("❌ CRITICAL: No Grid Bots registered")
        print()
        print("Action Required:")
        print("1. Check run_bot.py configuration")
        print("2. Verify engine.add_bot() calls for Grid Bots")
        print("3. Restart the bot service")
    elif not grid_trades_24h:
        print("⚠️  WARNING: Zero trades in last 24 hours")
        print()
        print("Possible Actions:")
        print("1. Check if Grid Bots are RUNNING (not just registered)")
        print("2. Verify price is within grid range (lower_limit to upper_limit)")
        print("3. Check market volatility - Grid Bots need price movement")
        print("4. Review bot logs for errors")
    else:
        print("✅ Grid Bots are trading successfully!")
        print()
        print("Monitor:")
        print("1. Trade frequency should be 2-10 trades per hour in volatile markets")
        print("2. P&L should accumulate from small profits on each grid level")
        print("3. Win rate should be 70-90% for Grid Bots (they profit from volatility)")

    print()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)

def main():
    db_path = find_database()

    if not db_path:
        print("=" * 80)
        print("❌ ERROR: Paper trading database not found")
        print("=" * 80)
        print()
        print("Searched locations:")
        for path in DB_PATHS:
            print(f"  - {path}")
        print()
        print("Solutions:")
        print("1. Create database by running the paper trading bot")
        print("2. Check database path in run_bot.py configuration")
        print("3. Ensure you're running this script from the correct location")
        sys.exit(1)

    analyze_grid_bot_performance(db_path)

if __name__ == "__main__":
    main()
