#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE BOT ANALYSIS
Investigates:
1. Buy-the-Dip Strategy - Why positions aren't closing
2. Database discrepancy analysis
3. Detailed P&L breakdown
4. Open position analysis with current market prices
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = 'data/trades_v3_paper.db'

def analyze_databases():
    """Compare all database files"""
    print("=" * 100)
    print("🗄️  DATABASE ANALYSIS")
    print("=" * 100)

    db_files = ['data/trades.db', 'data/trades_v3_paper.db', 'data/trades_v3_live.db']

    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"\n❌ {db_file}: NOT FOUND")
            continue

        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Check if trades table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            if not cursor.fetchone():
                print(f"\n⚠️  {db_file}: No 'trades' table found")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                if tables:
                    print(f"   Available tables: {', '.join([t[0] for t in tables])}")
                conn.close()
                continue

            # Get trade counts
            cursor.execute("SELECT COUNT(*) FROM trades")
            total_trades = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades WHERE side='BUY'")
            total_buys = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades WHERE side='SELL'")
            total_sells = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT strategy) FROM trades")
            unique_strategies = cursor.fetchone()[0]

            # Get date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM trades")
            date_range = cursor.fetchone()

            print(f"\n✅ {db_file}")
            print(f"   Total Trades: {total_trades} ({total_buys} buys, {total_sells} sells)")
            print(f"   Strategies: {unique_strategies}")
            print(f"   Date Range: {date_range[0] or 'N/A'} to {date_range[1] or 'N/A'}")

            conn.close()

        except Exception as e:
            print(f"\n❌ {db_file}: ERROR - {e}")

def analyze_buy_the_dip():
    """Deep dive into Buy-the-Dip strategy positions"""
    print("\n" + "=" * 100)
    print("🛍️  BUY-THE-DIP STRATEGY DEEP DIVE")
    print("=" * 100)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check for open positions
        query = """
        SELECT
            t.symbol,
            t.price as buy_price,
            t.amount,
            t.cost,
            t.timestamp as buy_time,
            t.position_id,
            t.rsi as entry_rsi
        FROM trades t
        WHERE t.strategy = 'Buy-the-Dip Strategy'
            AND t.side = 'BUY'
            AND t.position_id NOT IN (
                SELECT position_id FROM trades WHERE side = 'SELL' AND strategy = 'Buy-the-Dip Strategy'
            )
        ORDER BY t.timestamp ASC
        """

        cursor.execute(query)
        open_positions = cursor.fetchall()

        if not open_positions:
            print("\n✅ No open Buy-the-Dip positions found")
            conn.close()
            return

        print(f"\n📊 OPEN POSITIONS: {len(open_positions)}")
        print("-" * 100)

        total_capital_locked = 0
        now = datetime.now()

        for pos in open_positions:
            symbol, buy_price, amount, cost, buy_time, position_id, entry_rsi = pos
            total_capital_locked += cost

            # Calculate position age
            buy_datetime = datetime.fromisoformat(buy_time)
            age_days = (now - buy_datetime).total_seconds() / 86400

            print(f"\n{symbol}")
            print(f"  Position ID: {position_id}")
            print(f"  Buy Price: ${buy_price:.6f}")
            print(f"  Amount: {amount:.4f}")
            print(f"  Cost: ${cost:.2f}")
            print(f"  Age: {age_days:.1f} days ({age_days * 24:.1f} hours)")
            print(f"  Entry RSI: {entry_rsi if entry_rsi else 'N/A'}")
            print(f"  Buy Time: {buy_time}")

            # Calculate what would trigger exit based on config
            tp_price = buy_price * 1.06  # 6% TP from config
            sl_price = buy_price * 0.96  # 4% SL from config
            stagnation_hours = 72
            max_hold_hours = 1440  # 60 days from config

            print(f"  Take Profit Trigger: ${tp_price:.6f} (+6%)")
            print(f"  Stop Loss Trigger: ${sl_price:.6f} (-4%)")
            print(f"  Stagnation Check: {stagnation_hours}h with <1% profit")
            print(f"  Max Hold: {max_hold_hours}h ({max_hold_hours/24:.0f} days)")

            # Check if position should have exited
            if age_days * 24 > max_hold_hours:
                print(f"  ⚠️  ALERT: Position exceeds max hold time!")
            if age_days * 24 > stagnation_hours:
                print(f"  ⚠️  ALERT: Position exceeds stagnation threshold!")

        print(f"\n💰 TOTAL CAPITAL LOCKED: ${total_capital_locked:.2f}")

        # Get all trades for this strategy
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
                SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
                SUM(CASE WHEN side='BUY' THEN cost ELSE 0 END) as buy_cost,
                SUM(CASE WHEN side='SELL' THEN cost ELSE 0 END) as sell_revenue
            FROM trades
            WHERE strategy='Buy-the-Dip Strategy'
        """)

        stats = cursor.fetchone()
        total, buys, sells, buy_cost, sell_revenue = stats

        print(f"\n📈 STRATEGY STATS")
        print(f"  Total Trades: {total} ({buys} buys, {sells} sells)")
        print(f"  Total Bought: ${buy_cost:.2f}")
        print(f"  Total Sold: ${sell_revenue:.2f}")
        print(f"  Realized P&L: ${sell_revenue - buy_cost:.2f}")
        print(f"  Open Positions: {buys - sells}")

        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def analyze_all_strategies():
    """Comprehensive P&L breakdown by strategy"""
    print("\n" + "=" * 100)
    print("📊 STRATEGY PERFORMANCE BREAKDOWN")
    print("=" * 100)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
        SELECT
            strategy,
            COUNT(*) as total_trades,
            SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
            SUM(CASE WHEN side='BUY' THEN cost ELSE 0 END) as buy_cost,
            SUM(CASE WHEN side='SELL' THEN cost ELSE 0 END) as sell_revenue,
            ROUND(SUM(CASE WHEN side='SELL' THEN cost ELSE 0 END) -
                  SUM(CASE WHEN side='BUY' THEN cost ELSE 0 END), 2) as net_pnl
        FROM trades
        GROUP BY strategy
        ORDER BY net_pnl DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("\n⚠️  No trades found in database")
            conn.close()
            return

        print(f"\n{'Strategy':<30} {'Trades':<10} {'Buys':<10} {'Sells':<10} {'Buy $':<15} {'Sell $':<15} {'P&L':<15}")
        print("-" * 100)

        total_pnl = 0
        for row in results:
            strategy, total, buys, sells, buy_cost, sell_revenue, net_pnl = row
            total_pnl += net_pnl

            status = "✅" if net_pnl > 0 else "❌" if net_pnl < 0 else "➖"
            print(f"{strategy:<30} {total:<10} {buys:<10} {sells:<10} ${buy_cost:<14.2f} ${sell_revenue:<14.2f} {status} ${net_pnl:<13.2f}")

        print("-" * 100)
        print(f"{'TOTAL':<30} {'':<10} {'':<10} {'':<10} {'':<15} {'':<15} {'$'}{total_pnl:.2f}")

        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def analyze_recent_activity():
    """Show recent trading activity"""
    print("\n" + "=" * 100)
    print("🕐 RECENT TRADING ACTIVITY (Last 7 Days)")
    print("=" * 100)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
        SELECT
            timestamp,
            strategy,
            symbol,
            side,
            price,
            amount,
            cost
        FROM trades
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp DESC
        LIMIT 20
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("\n⚠️  No trades in last 7 days")
            conn.close()
            return

        print(f"\n{'Time':<20} {'Strategy':<25} {'Symbol':<12} {'Side':<6} {'Price':<15} {'Amount':<15} {'Cost':<12}")
        print("-" * 100)

        for row in results:
            timestamp, strategy, symbol, side, price, amount, cost = row
            side_emoji = "🟢" if side == "BUY" else "🔴"
            print(f"{timestamp:<20} {strategy:<25} {symbol:<12} {side_emoji} {side:<4} ${price:<14.6f} {amount:<15.4f} ${cost:<11.2f}")

        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def main():
    print("\n" + "=" * 100)
    print("🔍 COMPREHENSIVE CRYPTO BOT ANALYSIS")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    # Run all analyses
    analyze_databases()
    analyze_all_strategies()
    analyze_buy_the_dip()
    analyze_recent_activity()

    print("\n" + "=" * 100)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 100)
    print()

if __name__ == '__main__':
    main()
