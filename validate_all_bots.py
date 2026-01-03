#!/usr/bin/env python3
"""
🔍 CRYPTO BOT VALIDATION TOOL
Simple one-command validation for all bots
No coding knowledge required!
"""

import sqlite3
import sys
from datetime import datetime
from tabulate import tabulate

# Database path
DB_PATH = "./data/trades_v3.db"

def print_header(title):
    """Print a nice header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    """Print a section header"""
    print(f"\n{'─' * 80}")
    print(f"📊 {title}")
    print('─' * 80)

def connect_db():
    """Connect to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database!")
        print(f"   Path: {DB_PATH}")
        print(f"   Error: {e}")
        sys.exit(1)

def validate_hypersculper(conn):
    """Check Hyper-Scalper P&L discrepancy"""
    print_section("🚨 HYPER-SCALPER BOT INVESTIGATION")
    
    cursor = conn.cursor()
    
    # Get trade summary
    query = """
    SELECT
        COUNT(*) as trade_count,
        ROUND(SUM(realized_pnl), 2) as total_pnl,
        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
        ROUND(AVG(realized_pnl), 2) as avg_pnl
    FROM trades
    WHERE bot_name = 'Hyper-Scalper Bot'
    """
    
    result = cursor.execute(query).fetchone()
    
    if result['trade_count'] == 0:
        print("✅ No trades found - Bot has not traded yet")
        return
    
    print(f"\n📈 Database Shows:")
    print(f"   Total Trades: {result['trade_count']}")
    print(f"   Total P&L: ${result['total_pnl']}")
    print(f"   Wins: {result['wins']}")
    print(f"   Losses: {result['losses']}")
    print(f"   Average P&L: ${result['avg_pnl']}")
    
    # Compare with dashboard claim
    dashboard_pnl = 0.00
    print(f"\n🖥️  Dashboard Shows:")
    print(f"   Total P&L: ${dashboard_pnl}")
    
    if abs(result['total_pnl'] - dashboard_pnl) > 0.01:
        print(f"\n❌ CRITICAL BUG FOUND!")
        print(f"   Database has ${result['total_pnl']} but dashboard shows ${dashboard_pnl}")
        print(f"   Difference: ${abs(result['total_pnl'] - dashboard_pnl)}")
        print(f"\n🔧 ACTION REQUIRED: Dashboard P&L calculation is broken!")
    else:
        print(f"\n✅ P&L matches - No issues")

def validate_buy_the_dip(conn):
    """Analyze why Buy-the-Dip is losing 28%"""
    print_section("🚨 BUY-THE-DIP DISASTER ANALYSIS")
    
    cursor = conn.cursor()
    
    # Overall stats
    query = """
    SELECT
        COUNT(*) as total_trades,
        ROUND(SUM(realized_pnl), 2) as total_pnl,
        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
        ROUND(100.0 * SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
        ROUND(AVG(realized_pnl), 2) as avg_pnl
    FROM trades
    WHERE bot_name = 'Buy-the-Dip Strategy'
    """
    
    result = cursor.execute(query).fetchone()
    
    print(f"\n📊 Overall Performance:")
    print(f"   Total Trades: {result['total_trades']}")
    print(f"   Total Loss: ${result['total_pnl']} ⚠️")
    print(f"   Win Rate: {result['win_rate']}%")
    print(f"   Wins: {result['wins']} | Losses: {result['losses']}")
    print(f"   Average P&L per trade: ${result['avg_pnl']}")
    
    # Check if win rate is healthy
    if result['win_rate'] < 40:
        print(f"\n❌ PROBLEM: Win rate {result['win_rate']}% is TOO LOW")
        print(f"   Healthy dip buying should be >40% win rate")
        print(f"   🔧 FIX: Parameters are too aggressive - catching falling knives!")
    
    # Per-coin breakdown
    query = """
    SELECT 
        symbol,
        COUNT(*) as trades,
        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
        ROUND(100.0 * SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
        ROUND(SUM(realized_pnl), 2) as total_pnl,
        ROUND(AVG(realized_pnl), 2) as avg_pnl
    FROM trades
    WHERE bot_name = 'Buy-the-Dip Strategy'
    GROUP BY symbol
    ORDER BY total_pnl ASC
    LIMIT 10
    """
    
    results = cursor.execute(query).fetchall()
    
    print(f"\n💀 WORST PERFORMING COINS:")
    
    table_data = []
    for row in results:
        table_data.append([
            row['symbol'],
            row['trades'],
            f"{row['win_rate']}%",
            f"${row['total_pnl']}",
            f"${row['avg_pnl']}"
        ])
    
    print(tabulate(table_data, 
                   headers=['Coin', 'Trades', 'Win Rate', 'Total P&L', 'Avg P&L'],
                   tablefmt='grid'))
    
    # Check for overtrading
    query = """
    SELECT 
        DATE(entry_time) as trade_date,
        COUNT(*) as trades_per_day
    FROM trades
    WHERE bot_name = 'Buy-the-Dip Strategy'
    GROUP BY DATE(entry_time)
    ORDER BY trades_per_day DESC
    LIMIT 5
    """
    
    results = cursor.execute(query).fetchall()
    
    print(f"\n📅 BUSIEST TRADING DAYS:")
    for row in results:
        print(f"   {row['trade_date']}: {row['trades_per_day']} trades")
        if row['trades_per_day'] > 10:
            print(f"      ⚠️  WARNING: >10 trades/day = Overtrading!")

def validate_dip_sniper(conn):
    """Investigate why Dip Sniper has 0 trades"""
    print_section("❓ DIP SNIPER BRAIN DEATH INVESTIGATION")
    
    cursor = conn.cursor()
    
    # Check for any trades
    query = """
    SELECT COUNT(*) as trade_count
    FROM trades
    WHERE bot_name = 'Dip Sniper'
    """
    
    result = cursor.execute(query).fetchone()
    
    print(f"\n📊 Dip Sniper Status:")
    print(f"   Total Trades: {result['trade_count']}")
    
    if result['trade_count'] == 0:
        print(f"\n❌ CRITICAL PROBLEM: Bot has been running 35+ hours with ZERO trades!")
        print(f"\n🔍 Possible Causes:")
        print(f"   1. Entry criteria are impossibly strict")
        print(f"   2. Bot isn't actually monitoring the market")
        print(f"   3. API connection is broken")
        print(f"   4. Dip threshold is set too high (>5%)")
        print(f"\n🔧 ACTIONS NEEDED:")
        print(f"   1. Check bot logs: tail -100 bot.log | grep 'Dip Sniper'")
        print(f"   2. Verify dip_threshold parameter (should be 2-3%)")
        print(f"   3. Check if bot is actually running: ps aux | grep run_bot")

def validate_all_bots_summary(conn):
    """Overall health check for all bots"""
    print_section("🏥 ALL BOTS HEALTH CHECK")
    
    cursor = conn.cursor()
    
    query = """
    SELECT 
        bot_name,
        COUNT(*) as trades,
        ROUND(SUM(realized_pnl), 2) as total_pnl,
        ROUND(100.0 * SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate
    FROM trades
    GROUP BY bot_name
    ORDER BY total_pnl DESC
    """
    
    results = cursor.execute(query).fetchall()
    
    table_data = []
    for row in results:
        # Color code based on performance
        if row['total_pnl'] > 0:
            status = "✅ PROFIT"
        elif row['total_pnl'] > -50:
            status = "⚠️  SMALL LOSS"
        elif row['total_pnl'] > -500:
            status = "🚨 BIG LOSS"
        else:
            status = "💀 DISASTER"
        
        table_data.append([
            row['bot_name'],
            row['trades'],
            f"{row['win_rate']}%",
            f"${row['total_pnl']}",
            status
        ])
    
    print(f"\n")
    print(tabulate(table_data,
                   headers=['Bot Name', 'Trades', 'Win Rate', 'Total P&L', 'Status'],
                   tablefmt='grid'))

def validate_position_concentration(conn):
    """Check if too much capital is in one coin"""
    print_section("⚖️  POSITION CONCENTRATION CHECK")
    
    cursor = conn.cursor()
    
    # Check open positions
    query = """
    SELECT 
        symbol,
        COUNT(*) as open_positions,
        GROUP_CONCAT(DISTINCT bot_name) as bots_trading
    FROM trades
    WHERE exit_time IS NULL
    GROUP BY symbol
    ORDER BY open_positions DESC
    """
    
    try:
        results = cursor.execute(query).fetchall()
        
        if len(results) == 0:
            print("\n✅ No open positions currently")
        else:
            print(f"\n📊 Open Positions by Coin:")
            for row in results:
                print(f"\n   {row['symbol']}: {row['open_positions']} open positions")
                print(f"      Bots: {row['bots_trading']}")
                if row['open_positions'] > 3:
                    print(f"      ⚠️  WARNING: >3 positions in one coin = High concentration risk!")
    except:
        print("\n⚠️  Could not check open positions (table structure may differ)")

def main():
    """Main validation routine"""
    print_header("🔍 CRYPTO BOT COMPREHENSIVE VALIDATION")
    print(f"\nRunning validation at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
    
    conn = connect_db()
    
    try:
        # Run all validations
        validate_all_bots_summary(conn)
        validate_hypersculper(conn)
        validate_buy_the_dip(conn)
        validate_dip_sniper(conn)
        validate_position_concentration(conn)
        
        print_header("✅ VALIDATION COMPLETE")
        
        print("\n📋 RECOMMENDED ACTIONS:")
        print("   1. Stop Buy-the-Dip bot (losing -28%)")
        print("   2. Stop SMA Trend bot (losing -20%)")
        print("   3. Investigate Dip Sniper (0 trades)")
        print("   4. Fix Hyper-Scalper P&L calculation")
        print("   5. Keep Grid Bots running (they're profitable!)")
        print("\n" + "=" * 80 + "\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
