"""
Analyze skipped trades to understand why the bot isn't trading
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = 'data/trades.db'

def analyze_skipped_trades():
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*80)
    print("🚫 SKIPPED TRADES ANALYSIS")
    print("="*80)
    print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skipped_trades'")
    if not cursor.fetchone():
        print("❌ No skipped_trades table found. Run migrate_add_skipped_trades.py first.")
        conn.close()
        return
    
    # Total skipped trades
    cursor.execute("SELECT COUNT(*) FROM skipped_trades")
    total_skipped = cursor.fetchone()[0]
    
    if total_skipped == 0:
        print("✅ No skipped trades recorded yet!")
        print("   Bot is either executing all signals or hasn't run with the new logging yet.\n")
        conn.close()
        return
    
    print(f"📊 Total Skipped: {total_skipped} opportunities\n")
    
    # Breakdown by reason
    print("🔍 SKIP REASONS:")
    print("-" * 80)
    query = """
    SELECT 
        skip_reason, 
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM skipped_trades), 1) as pct
    FROM skipped_trades
    GROUP BY skip_reason
    ORDER BY count DESC
    """
    df_reasons = pd.read_sql_query(query, conn)
    print(df_reasons.to_string(index=False))
    print()
    
    # Breakdown by strategy
    print("📈 BY STRATEGY:")
    print("-" * 80)
    query = """
    SELECT 
        strategy,
        COUNT(*) as skipped,
        skip_reason,
        COUNT(*) as count
    FROM skipped_trades
    GROUP BY strategy, skip_reason
    ORDER BY strategy, count DESC
    """
    df_strategy = pd.read_sql_query(query, conn)
    print(df_strategy.to_string(index=False))
    print()
    
    # Most affected symbols
    print("🎯 MOST BLOCKED SYMBOLS:")
    print("-" * 80)
    query = """
    SELECT 
        symbol,
        COUNT(*) as times_skipped,
        GROUP_CONCAT(DISTINCT skip_reason) as reasons
    FROM skipped_trades
    GROUP BY symbol
    ORDER BY times_skipped DESC
    LIMIT 10
    """
    df_symbols = pd.read_sql_query(query, conn)
    print(df_symbols.to_string(index=False))
    print()
    
    # Recent skips (last 24h)
    print("⏰ LAST 10 SKIPPED TRADES:")
    print("-" * 80)
    query = """
    SELECT 
        timestamp,
        strategy,
        symbol,
        skip_reason,
        details
    FROM skipped_trades
    ORDER BY timestamp DESC
    LIMIT 10
    """
    df_recent = pd.read_sql_query(query, conn)
    print(df_recent.to_string(index=False))
    print()
    
    # Exposure analysis
    print("💰 EXPOSURE LIMIT ANALYSIS:")
    print("-" * 80)
    query = """
    SELECT 
        symbol,
        strategy,
        ROUND(AVG(current_exposure), 2) as avg_current,
        MAX(max_exposure) as limit,
        COUNT(*) as times_blocked
    FROM skipped_trades
    WHERE skip_reason = 'EXPOSURE_LIMIT'
    GROUP BY symbol, strategy
    ORDER BY times_blocked DESC
    LIMIT 10
    """
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        for row in results:
            symbol, strategy, avg_current, limit, times_blocked = row
            print(f"{symbol:<12} ({strategy:<25}) ${avg_current:>8.2f} / ${limit:>8.2f}  ({times_blocked} blocks)")
    else:
        print("   No exposure limit blocks recorded")
    
    print("\n" + "="*80)
    
    conn.close()

if __name__ == "__main__":
    analyze_skipped_trades()
