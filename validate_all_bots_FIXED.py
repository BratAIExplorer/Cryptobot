#!/usr/bin/env python3
"""
🔍 CRYPTO BOT VALIDATION TOOL - FIXED FOR YOUR DATABASE
"""

import sqlite3
from datetime import datetime
from tabulate import tabulate

DB_PATH = "./data/trades_v3.db"

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    print(f"\n{'─' * 80}")
    print(f"📊 {title}")
    print('─' * 80)

def connect_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database!")
        print(f"   Error: {e}")
        return None

def check_positions_table(conn):
    """First, let's see what the positions table looks like"""
    print_section("🔍 CHECKING POSITIONS TABLE STRUCTURE")
    
    cursor = conn.cursor()
    
    # Get positions table structure
    cursor.execute("PRAGMA table_info(positions)")
    columns = cursor.fetchall()
    
    print("\n📋 Positions Table Columns:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Get sample data
    print("\n📊 Sample Position Data:")
    try:
        cursor.execute("SELECT * FROM positions LIMIT 3")
        rows = cursor.fetchall()
        
        if len(rows) == 0:
            print("   No positions found")
        else:
            for row in rows:
                print(f"   {dict(row)}")
    except Exception as e:
        print(f"   Error: {e}")

def validate_all_bots_summary(conn):
    """Overall health check for all bots using POSITIONS table"""
    print_section("🏥 ALL BOTS PERFORMANCE (FROM POSITIONS)")
    
    cursor = conn.cursor()
    
    # Check if positions table has realized_pnl
    try:
        query = """
        SELECT 
            strategy,
            COUNT(*) as total_positions,
            SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed_positions,
            SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_positions
        FROM positions
        GROUP BY strategy
        ORDER BY strategy
        """
        
        results = cursor.execute(query).fetchall()
        
        if len(results) == 0:
            print("\n⚠️  No positions found in database")
            return
        
        print("\n📊 Bot Activity:")
        table_data = []
        for row in results:
            table_data.append([
                row['strategy'],
                row['total_positions'],
                row['closed_positions'],
                row['open_positions']
            ])
        
        print(tabulate(table_data,
                      headers=['Bot/Strategy', 'Total Pos', 'Closed', 'Open'],
                      tablefmt='grid'))
        
        # Now try to calculate P&L from positions
        print_section("💰 P&L CALCULATION (if available)")
        
        # Check what columns exist in positions
        cursor.execute("PRAGMA table_info(positions)")
        pos_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📋 Available P&L columns: {', '.join([c for c in pos_columns if 'pnl' in c.lower() or 'profit' in c.lower()])}")
        
    except Exception as e:
        print(f"\n❌ Error analyzing positions: {e}")

def analyze_by_trades(conn):
    """Analyze bot performance from individual trades"""
    print_section("📈 BOT ACTIVITY FROM TRADES")
    
    cursor = conn.cursor()
    
    query = """
    SELECT 
        strategy,
        COUNT(*) as total_trades,
        SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buys,
        SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sells,
        SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END) as total_bought,
        SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END) as total_sold
    FROM trades
    GROUP BY strategy
    ORDER BY total_trades DESC
    """
    
    results = cursor.execute(query).fetchall()
    
    if len(results) == 0:
        print("\n⚠️  No trades found")
        return
    
    print("\n")
    table_data = []
    for row in results:
        # Rough P&L estimate (sold - bought)
        rough_pnl = row['total_sold'] - row['total_bought']
        
        table_data.append([
            row['strategy'],
            row['total_trades'],
            row['buys'],
            row['sells'],
            f"${row['total_bought']:.2f}",
            f"${row['total_sold']:.2f}",
            f"${rough_pnl:.2f}"
        ])
    
    print(tabulate(table_data,
                  headers=['Strategy', 'Trades', 'Buys', 'Sells', 'Total Bought', 'Total Sold', 'Rough P&L'],
                  tablefmt='grid'))

def check_dip_sniper(conn):
    """Check Dip Sniper activity"""
    print_section("❓ DIP SNIPER INVESTIGATION")
    
    cursor = conn.cursor()
    
    query = """
    SELECT COUNT(*) as trade_count
    FROM trades
    WHERE strategy = 'Dip Sniper'
    """
    
    result = cursor.execute(query).fetchone()
    
    print(f"\n📊 Dip Sniper Trades: {result['trade_count']}")
    
    if result['trade_count'] == 0:
        print("\n❌ CONFIRMED: Dip Sniper has 0 trades!")
        print("\n🔍 Possible Causes:")
        print("   1. Entry criteria too strict")
        print("   2. Not monitoring market")
        print("   3. API connection broken")
        print("\n🔧 Check bot logs:")
        print("   tail -100 bot.log | grep -i 'dip sniper'")

def check_buy_the_dip(conn):
    """Analyze Buy-the-Dip performance"""
    print_section("🚨 BUY-THE-DIP ANALYSIS")
    
    cursor = conn.cursor()
    
    # Get trade activity
    query = """
    SELECT 
        symbol,
        COUNT(*) as trades,
        SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END) as bought,
        SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END) as sold
    FROM trades
    WHERE strategy = 'Buy-the-Dip Strategy'
    GROUP BY symbol
    ORDER BY trades DESC
    LIMIT 10
    """
    
    results = cursor.execute(query).fetchall()
    
    if len(results) == 0:
        print("\n✅ No Buy-the-Dip trades found")
        return
    
    print("\n📊 Most Traded Coins:")
    table_data = []
    for row in results:
        pnl = row['sold'] - row['bought']
        table_data.append([
            row['symbol'],
            row['trades'],
            f"${row['bought']:.2f}",
            f"${row['sold']:.2f}",
            f"${pnl:.2f}"
        ])
    
    print(tabulate(table_data,
                  headers=['Symbol', 'Trades', 'Bought', 'Sold', 'P&L'],
                  tablefmt='grid'))
    
    # Check trade frequency
    query = """
    SELECT 
        DATE(timestamp) as trade_date,
        COUNT(*) as trades_per_day
    FROM trades
    WHERE strategy = 'Buy-the-Dip Strategy'
    GROUP BY DATE(timestamp)
    ORDER BY trades_per_day DESC
    LIMIT 5
    """
    
    results = cursor.execute(query).fetchall()
    
    print("\n📅 Busiest Days:")
    for row in results:
        print(f"   {row['trade_date']}: {row['trades_per_day']} trades")
        if row['trades_per_day'] > 10:
            print(f"      ⚠️  WARNING: Overtrading!")

def check_open_positions(conn):
    """Check current open positions"""
    print_section("📍 OPEN POSITIONS")
    
    cursor = conn.cursor()
    
    query = """
    SELECT 
        strategy,
        symbol,
        COUNT(*) as count
    FROM positions
    WHERE status = 'OPEN'
    GROUP BY strategy, symbol
    ORDER BY count DESC
    """
    
    try:
        results = cursor.execute(query).fetchall()
        
        if len(results) == 0:
            print("\n✅ No open positions")
        else:
            print("\n📊 Current Open Positions:")
            for row in results:
                print(f"   {row['strategy']}: {row['symbol']} ({row['count']} positions)")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")

def check_bot_status(conn):
    """Check bot_status table"""
    print_section("🤖 BOT STATUS TABLE")
    
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM bot_status ORDER BY last_update DESC LIMIT 10"
        results = cursor.execute(query).fetchall()
        
        if len(results) == 0:
            print("\n⚠️  Bot status table is empty")
        else:
            print("\n📊 Recent Bot Status Updates:")
            for row in results:
                print(f"   {dict(row)}")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")

def main():
    print_header("🔍 CRYPTO BOT COMPREHENSIVE VALIDATION")
    print(f"\nRunning at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        check_positions_table(conn)
        validate_all_bots_summary(conn)
        analyze_by_trades(conn)
        check_dip_sniper(conn)
        check_buy_the_dip(conn)
        check_open_positions(conn)
        check_bot_status(conn)
        
        print_header("✅ VALIDATION COMPLETE")
        
        print("\n📋 NEXT STEPS:")
        print("   1. Check the dashboard P&L calculations")
        print("   2. Investigate Dip Sniper (0 trades)")
        print("   3. Review Buy-the-Dip parameters")
        print("   4. Check bot.log for errors")
        print("\n" + "=" * 80 + "\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
