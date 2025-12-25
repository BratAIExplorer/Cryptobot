"""
Verification Script for P&L Calculation Fix

This script compares the old positions-based P&L calculation with the new
trades-based calculation to verify the fix is working correctly.

Run this after deploying the fix to confirm all bot P&L values are now accurate.
"""

import pandas as pd
import sqlite3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import TradeLogger

def calculate_old_pnl(db_path, strategy=None):
    """Old broken method: Sum unrealized_pnl_usd from closed positions"""
    conn = sqlite3.connect(db_path)
    
    query = "SELECT unrealized_pnl_usd FROM positions WHERE status = 'CLOSED'"
    if strategy:
        query += f" AND strategy = '{strategy}'"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return 0.0
    
    return df['unrealized_pnl_usd'].sum()

def calculate_new_pnl(logger, strategy=None):
    """New correct method: Using the fixed get_pnl_summary()"""
    return logger.get_pnl_summary(strategy)

def get_trade_counts(db_path, strategy):
    """Get buy and sell trade counts for a strategy"""
    conn = sqlite3.connect(db_path)
    
    query = f"""
        SELECT side, COUNT(*) as count, SUM(cost) as total_cost
        FROM trades 
        WHERE strategy = '{strategy}'
        GROUP BY side
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return 0, 0, 0.0, 0.0
    
    buys = df[df['side'] == 'BUY']['count'].sum() if 'BUY' in df['side'].values else 0
    sells = df[df['side'] == 'SELL']['count'].sum() if 'SELL' in df['side'].values else 0
    buy_cost = df[df['side'] == 'BUY']['total_cost'].sum() if 'BUY' in df['side'].values else 0.0
    sell_cost = df[df['side'] == 'SELL']['total_cost'].sum() if 'SELL' in df['side'].values else 0.0
    
    return int(buys), int(sells), float(buy_cost), float(sell_cost)

def main():
    print("=" * 80)
    print("P&L CALCULATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Determine database path
    mode = 'paper'  # Change to 'live' if needed
    db_filename = 'trades_v3_live.db' if mode == 'live' else 'trades_v3_paper.db'
    db_path = os.path.join(os.path.dirname(__file__), 'data', db_filename)
    
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database not found at {db_path}")
        print("Please check the database path and try again.")
        return
    
    print(f"📊 Using database: {db_path}")
    print()
    
    # Initialize logger with fixed calculation
    logger = TradeLogger(db_path=db_path)
    
    # Get all unique strategies
    conn = sqlite3.connect(db_path)
    strategies_df = pd.read_sql_query(
        "SELECT DISTINCT strategy FROM trades ORDER BY strategy", 
        conn
    )
    conn.close()
    
    if strategies_df.empty:
        print("⚠️  No trades found in database. Nothing to verify.")
        return
    
    strategies = strategies_df['strategy'].tolist()
    
    # Prepare comparison table
    comparison_data = []
    
    print("Analyzing all bot strategies...")
    print()
    
    for strategy in strategies:
        old_pnl = calculate_old_pnl(db_path, strategy)
        new_pnl = calculate_new_pnl(logger, strategy)
        buys, sells, buy_cost, sell_cost = get_trade_counts(db_path, strategy)
        
        difference = new_pnl - old_pnl
        
        # Determine status emoji
        if abs(difference) < 0.01:
            status = "✅"
        elif new_pnl > 0:
            status = "🟢"  # Actually profitable
        else:
            status = "🔴"  # Actually losing
        
        comparison_data.append({
            'Status': status,
            'Strategy': strategy[:30],  # Truncate long names
            'Buys': buys,
            'Sells': sells,
            'Old P&L': f"${old_pnl:,.2f}",
            'New P&L': f"${new_pnl:,.2f}",
            'Difference': f"${difference:,.2f}",
            'Buy Cost': f"${buy_cost:,.2f}",
            'Sell Revenue': f"${sell_cost:,.2f}"
        })
    
    # Display comparison table
    print("=" * 140)
    print(f"{'Status':<8} {'Strategy':<30} {'Buys':<6} {'Sells':<6} {'Old P&L':<15} {'New P&L':<15} {'Difference':<15} {'Buy Cost':<15} {'Sell Revenue':<15}")
    print("=" * 140)
    
    for row in comparison_data:
        print(f"{row['Status']:<8} {row['Strategy']:<30} {row['Buys']:<6} {row['Sells']:<6} "
              f"{row['Old P&L']:<15} {row['New P&L']:<15} {row['Difference']:<15} "
              f"{row['Buy Cost']:<15} {row['Sell Revenue']:<15}")
    
    print("=" * 140)
    print()
    
    # Summary statistics
    total_old = sum(calculate_old_pnl(db_path, s) for s in strategies)
    total_new = sum(calculate_new_pnl(logger, s) for s in strategies)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total P&L (Old Method):  ${total_old:,.2f}")
    print(f"Total P&L (New Method):  ${total_new:,.2f}")
    print(f"Total Difference:        ${total_new - total_old:,.2f}")
    print()
    
    # Identify problem bots
    print("=" * 80)
    print("ACTION ITEMS")
    print("=" * 80)
    
    losing_bots = [
        (s, calculate_new_pnl(logger, s)) 
        for s in strategies 
        if calculate_new_pnl(logger, s) < -100  # Losing more than $100
    ]
    
    if losing_bots:
        print("🚨 BOTS WITH SIGNIFICANT LOSSES (Recommend stopping):")
        for bot_name, pnl in sorted(losing_bots, key=lambda x: x[1]):
            print(f"   - {bot_name}: ${pnl:,.2f}")
        print()
    else:
        print("✅ No bots with significant losses detected.")
        print()
    
    profitable_bots = [
        (s, calculate_new_pnl(logger, s)) 
        for s in strategies 
        if calculate_new_pnl(logger, s) > 100  # Profit more than $100
    ]
    
    if profitable_bots:
        print("🏆 PROFITABLE BOTS (Keep running):")
        for bot_name, pnl in sorted(profitable_bots, key=lambda x: x[1], reverse=True):
            print(f"   - {bot_name}: ${pnl:,.2f}")
        print()
    
    print("=" * 80)
    print("✅ Verification complete!")
    print()
    print("Next steps:")
    print("1. Review the dashboard to confirm P&L values match the 'New P&L' column")
    print("2. Stop any losing bots listed above")
    print("3. Monitor profitable bots to ensure they continue performing well")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
