#!/usr/bin/env python3
"""
VPS Bot Performance Check
Connects to VPS database and analyzes trading performance
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys

def analyze_performance(db_path='data/trades.db'):
    """Analyze bot performance metrics"""
    
    try:
        conn = sqlite3.connect(db_path)
        
        print("=" * 100)
        print(f"BOT PERFORMANCE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        print()
        
        # 1. BOT STATUS (Dashboard values)
        print("📊 BOT STATUS (Current State)")
        print("-" * 100)
        df_status = pd.read_sql_query("SELECT * FROM bot_status", conn)
        if not df_status.empty:
            for _, row in df_status.iterrows():
                print(f"  {row['strategy']}")
                print(f"    Status: {row['status']}")
                print(f"    Total Trades: {row['total_trades']}")
                print(f"    Total P&L: ${row['total_pnl']:.2f}")
                print(f"    Wallet Balance: ${row['wallet_balance']:.2f}")
                print(f"    Last Heartbeat: {row['last_heartbeat']}")
                print()
        else:
            print("  No bot status data found\n")
        
        # 2. CLOSED POSITIONS (Realized P&L)
        print("💰 REALIZED P&L (Closed Positions)")
        print("-" * 100)
        query_closed = """
        SELECT 
            strategy,
            COUNT(*) as trades,
            SUM(profit) as total_pnl,
            AVG(profit) as avg_pnl,
            MIN(profit) as worst_trade,
            MAX(profit) as best_trade,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as losses
        FROM positions 
        WHERE status='CLOSED'
        GROUP BY strategy
        """
        df_closed = pd.read_sql_query(query_closed, conn)
        
        if not df_closed.empty:
            total_pnl = 0
            for _, row in df_closed.iterrows():
                win_rate = (row['wins'] / row['trades'] * 100) if row['trades'] > 0 else 0
                print(f"  {row['strategy']}")
                print(f"    Total P&L: ${row['total_pnl']:.2f}")
                print(f"    Trades: {row['trades']} (Wins: {row['wins']}, Losses: {row['losses']})")
                print(f"    Win Rate: {win_rate:.1f}%")
                print(f"    Avg P&L/Trade: ${row['avg_pnl']:.2f}")
                print(f"    Best Trade: ${row['best_trade']:.2f} | Worst: ${row['worst_trade']:.2f}")
                print()
                total_pnl += row['total_pnl']
            
            print(f"  📈 OVERALL REALIZED P&L: ${total_pnl:.2f}")
            print()
        else:
            print("  No closed positions yet\n")
        
        # 3. OPEN POSITIONS
        print("📂 OPEN POSITIONS (Unrealized)")
        print("-" * 100)
        query_open = """
        SELECT 
            strategy,
            symbol,
            buy_price,
            amount,
            cost,
            buy_timestamp,
            ROUND((julianday('now') - julianday(buy_timestamp)) * 24, 1) as age_hours
        FROM positions 
        WHERE status='OPEN'
        ORDER BY buy_timestamp DESC
        """
        df_open = pd.read_sql_query(query_open, conn)
        
        if not df_open.empty:
            print(f"  Total Open: {len(df_open)} positions | Capital Locked: ${df_open['cost'].sum():.2f}")
            print()
            print(df_open[['strategy', 'symbol', 'buy_price', 'cost', 'age_hours']].to_string(index=False))
            print()
        else:
            print("  No open positions\n")
        
        # 4. RECENT ACTIVITY (Last 24 hours)
        print("🕐 RECENT ACTIVITY (Last 24 Hours)")
        print("-" * 100)
        query_recent = """
        SELECT 
            strategy,
            symbol,
            side,
            price,
            cost,
            timestamp
        FROM trades
        WHERE datetime(timestamp) > datetime('now', '-24 hours')
        ORDER BY timestamp DESC
        LIMIT 15
        """
        df_recent = pd.read_sql_query(query_recent, conn)
        
        if not df_recent.empty:
            print(f"  Trades in last 24h: {len(df_recent)}")
            print()
            print(df_recent.to_string(index=False))
            print()
        else:
            print("  No trades in last 24 hours\n")
        
        # 5. CIRCUIT BREAKER STATUS
        print("🔴 CIRCUIT BREAKER STATUS")
        print("-" * 100)
        query_cb = "SELECT * FROM circuit_breaker WHERE id = 1"
        df_cb = pd.read_sql_query(query_cb, conn)
        
        if not df_cb.empty:
            cb = df_cb.iloc[0]
            status = "🔴 OPEN (PAUSED)" if cb['is_open'] else "✅ CLOSED (ACTIVE)"
            print(f"  Status: {status}")
            print(f"  Consecutive Errors: {cb['consecutive_errors']}")
            print(f"  Total Trips: {cb['total_trips']}")
            if cb['last_error_time']:
                print(f"  Last Error: {cb['last_error_time']}")
            print()
        
        # 6. PERFORMANCE METRICS
        print("📈 KEY PERFORMANCE METRICS")
        print("-" * 100)
        
        # Total equity calculation
        query_equity = "SELECT SUM(profit) FROM positions WHERE status='CLOSED'"
        total_realized_pnl = pd.read_sql_query(query_equity, conn).iloc[0, 0] or 0
        
        query_exposure = "SELECT SUM(cost) FROM positions WHERE status='OPEN'"
        total_exposure = pd.read_sql_query(query_exposure, conn).iloc[0, 0] or 0
        
        starting_balance = 50000.0
        current_equity = starting_balance + total_realized_pnl
        available_balance = current_equity - total_exposure
        
        print(f"  Starting Balance: ${starting_balance:,.2f}")
        print(f"  Realized P&L: ${total_realized_pnl:,.2f}")
        print(f"  Current Equity: ${current_equity:,.2f} ({(total_realized_pnl/starting_balance*100):+.2f}%)")
        print(f"  Capital Locked: ${total_exposure:,.2f}")
        print(f"  Available Balance: ${available_balance:,.2f}")
        print()
        
        conn.close()
        
        print("=" * 100)
        print("✅ Report Complete")
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Error analyzing performance: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Default to local path, but can be overridden
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/trades.db'
    analyze_performance(db_path)
