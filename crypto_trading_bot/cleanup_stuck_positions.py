#!/usr/bin/env python3
"""
Force-close stuck positions that have exceeded their max hold time.
This cleans up the operational state while preserving trade history.
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.exchange import ExchangeInterface

def cleanup_stuck_positions():
    """Force-close positions older than 2x their max hold time"""
    db_path = 'data/trades.db'
    conn = sqlite3.connect(db_path)
    
    # Get all open positions
    df = pd.read_sql_query("SELECT * FROM positions WHERE status='OPEN'", conn)
    
    if df.empty:
        print("No open positions to clean up")
        conn.close()
        return
    
    print(f"Found {len(df)} open positions. Analyzing...")
    
    # Strategy max hold times (in hours)
    max_hold_times = {
        'Hyper-Scalper Bot': 0.5,  # 30 minutes
        'Buy-the-Dip Strategy': 2880,  # 120 days
        'SMA Trend Bot': 24  # 24 hours
    }
    
    exchange = ExchangeInterface(mode='paper')
    closed_count = 0
    
    for _, position in df.iterrows():
        strategy = position['strategy']
        symbol = position['symbol']
        position_id = position['id']
        buy_price = position['buy_price']
        buy_timestamp = pd.to_datetime(position['buy_timestamp'])
        amount = position['amount']
        
        # Calculate position age
        age_hours = (datetime.now() - buy_timestamp).total_seconds() / 3600
        max_hold = max_hold_times.get(strategy, 24)
        
        # Force close if older than 2x max hold time
        if age_hours > (max_hold * 2):
            print(f"\n[CLEANUP] Position #{position_id}: {symbol} ({strategy})")
            print(f"  Age: {age_hours:.1f}h (Max: {max_hold}h)")
            
            # Get current market price
            try:
                current_df = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=1)
                if not current_df.empty:
                    current_price = current_df['close'].iloc[-1]
                else:
                    current_price = buy_price  # Fallback
            except:
                current_price = buy_price  # Fallback
            
            # Calculate profit
            sell_value = current_price * amount
            cost = buy_price * amount
            profit = sell_value - cost
            profit_pct = (profit / cost) * 100
            
            print(f"  Buy: ${buy_price:.4f} → Current: ${current_price:.4f}")
            print(f"  Profit: ${profit:.2f} ({profit_pct:.2f}%)")
            
            # Close position
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE positions 
                SET status = 'CLOSED', sell_price = ?, sell_timestamp = ?, profit = ?
                WHERE id = ?
            ''', (current_price, datetime.now(), profit, position_id))
            conn.commit()
            
            print(f"  ✅ Position closed")
            closed_count += 1
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Cleanup complete: {closed_count} positions force-closed")
    print(f"{'='*60}")

if __name__ == "__main__":
    cleanup_stuck_positions()
