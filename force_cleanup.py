import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'data/trades.db'

def force_cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n--- FORCED DATABASE CLEANUP ---")
    
    # 1. Identify Stuck Positions (older than 24h)
    # We'll just close ALL open positions for the Scalper/HiddenGem/SMA bots to be safe
    # But keep Grid Bot positions if any (though likely none due to 0 trades)
    
    # Check what's open
    df_open = pd.read_sql_query("SELECT * FROM positions WHERE status='OPEN'", conn)
    
    if df_open.empty:
        print("✅ No open positions found. Database is clean.")
        conn.close()
        return

    print(f"Found {len(df_open)} open positions:")
    print(df_open[['id', 'symbol', 'strategy', 'amount', 'buy_timestamp']].to_string())
    
    # 2. Force Close Logic
    print("\nForce closing 'Ghost' positions...")
    
    # Strategies to clean aggressively
    targets = ['Hyper-Scalper Bot', 'Hidden Gem Monitor', 'SMA Trend Bot']
    
    cleanup_count = 0
    for index, row in df_open.iterrows():
        # Clean if strategy is in target list OR if position is very old (>48h)
        # Assuming most of these are the ghosts causing "Exposure Limit Reached"
        should_clean = False
        
        if row['strategy'] in targets:
            should_clean = True
        
        # Check age
        try:
            buy_time = pd.to_datetime(row['buy_timestamp'])
            age_hours = (datetime.now() - buy_time).total_seconds() / 3600
            if age_hours > 24: 
                should_clean = True
        except:
            should_clean = True # If timestamp invalid, definitely clean
            
        if should_clean:
            c.execute("""
                UPDATE positions 
                SET status = 'CLOSED', 
                    sell_timestamp = ?, 
                    sell_price = buy_price, 
                    profit = 0, 
                    exit_rsi = 50 
                WHERE id = ?
            """, (datetime.now(), row['id']))
            print(f"  -> Closed Position #{row['id']} ({row['symbol']})")
            cleanup_count += 1
            
    conn.commit()
    print(f"\n✅ Successfully forced-closed {cleanup_count} stuck positions.")
    print("The bot should now start trading immediately.")
    
    conn.close()

if __name__ == "__main__":
    force_cleanup()
