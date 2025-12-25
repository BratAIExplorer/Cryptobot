#!/usr/bin/env python3
"""
📊 DAILY BOT PERFORMANCE CHECK

Simple summary you run every morning to track bot performance
Shows 24-hour and 7-day metrics for all strategies

Usage: python daily_bot_check.py
"""

import sqlite3
from datetime import datetime, timedelta
import os

# Database configuration
MODE = 'paper'  # Change to 'live' if needed
DB_FILENAME = 'trades_v3_live.db' if MODE == 'live' else 'trades_v3_paper.db'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', DB_FILENAME)

def format_table(data, headers):
    """Simple table formatting without external dependencies"""
    if not data:
        return ""
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] =max(widths[i], len(str(cell)))
    
    # Create separator
    separator = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    
    # Create header
    header = "|" + "|".join([f" {h:<{widths[i]}} " for i, h in enumerate(headers)]) + "|"
    
    # Create rows
    rows = []
    for row in data:
        rows.append("|" + "|".join([f" {str(cell):<{widths[i]}} " for i, cell in enumerate(row)]) + "|")
    
    return "\n".join([separator, header, separator] + rows + [separator])

def daily_summary():
    """Show last 24 hours performance"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print("=" * 100)
    print(f"📊 DAILY BOT PERFORMANCE - Last 24 Hours")
    print(f"   Date: {yesterday} to {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 100)
    print()
    
    query = """
    SELECT 
        strategy,
        COUNT(*) as trades,
        SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buys,
        SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sells,
        ROUND(SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END), 2) as bought,
        ROUND(SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END), 2) as sold,
        ROUND(SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END) - 
              SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END), 2) as pnl_24h
    FROM trades
    WHERE timestamp >= datetime('now', '-1 day')
    GROUP BY strategy
    ORDER BY pnl_24h DESC
    """
    
    results = cursor.execute(query).fetchall()
    
    if len(results) == 0:
        print("⚠️  No trades in last 24 hours")
        conn.close()
        return
    
    table_data = []
    total_pnl = 0
    
    for row in results:
        pnl = row[6]
        total_pnl += pnl
        
        # Status indicator
        if pnl > 0:
            status = "✅ PROFIT"
        elif pnl == 0:
            status = "➖ NEUTRAL"
        else:
            status = "❌ LOSS"
        
        table_data.append([
            row[0],  # strategy
            row[1],  # trades
            row[2],  # buys
            row[3],  # sells
            f"${pnl:.2f}",
            status
        ])
    
    headers = ['Strategy', 'Trades', 'Buys', 'Sells', '24h P&L', 'Status']
    print(format_table(table_data, headers))
    print()
    print(f"💰 TOTAL 24h P&L: ${total_pnl:.2f}")
    
    # Warning indicators
    print()
    print("⚠️  WARNINGS:")
    warning_found = False
    for row in results:
        if row[2] > row[3] * 2 and row[3] > 0:  # More than 2x buys vs sells
            print(f"   - {row[0]}: More buys than sells (positions piling up!)")
            warning_found = True
        if row[1] > 15:  # More than 15 trades
            print(f"   - {row[0]}: High trade frequency ({row[1]} trades - check for overtrading)")
            warning_found = True
    
    if not warning_found:
        print("   No warnings detected ✅")
    
    conn.close()

def weekly_summary():
    """Show last 7 days performance"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print()
    print("=" * 100)
    print(f"📊 WEEKLY BOT PERFORMANCE - Last 7 Days")
    print("=" * 100)
    print()
    
    query = """
    SELECT 
        strategy,
        COUNT(*) as trades,
        ROUND(SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END) - 
              SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END), 2) as pnl_7d,
        ROUND(100.0 * SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) / 
              NULLIF(COUNT(*), 0), 1) as sell_rate
    FROM trades
    WHERE timestamp >= datetime('now', '-7 days')
    GROUP BY strategy
    ORDER BY pnl_7d DESC
    """
    
    results = cursor.execute(query).fetchall()
    
    if len(results) == 0:
        print("⚠️  No trades in last 7 days")
        conn.close()
        return
    
    table_data = []
    for row in results:
        # Health check
        pnl = row[2]
        if pnl > 0 and row[3] > 40:  # Profitable and good sell rate
            health = "🟢 HEALTHY"
        elif pnl > -100:
            health = "🟡 WATCH"
        else:
            health = "🔴 FAILING"
        
        table_data.append([
            row[0],  # strategy
            row[1],  # trades
            f"{row[3]:.1f}%",  # sell rate
            f"${pnl:.2f}",
            health
        ])
    
    headers = ['Strategy', 'Trades (7d)', 'Sell Rate', '7d P&L', 'Health']
    print(format_table(table_data, headers))
    
    conn.close()

if __name__ == "__main__":
    try:
        daily_summary()
        weekly_summary()
        
        print()
        print("=" * 100)
        print("💡 TIP: Run this every morning to track bot performance!")
        print("   Command: python daily_bot_check.py")
        print("=" * 100)
        print()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nMake sure database exists at: {DB_PATH}")
