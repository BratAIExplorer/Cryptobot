import sqlite3
import pandas as pd
import time
import os

db_path = 'data/trades.db'

while True:
    try:
        os.system('clear')
        print(f"=== 🕒 LIVE MONITOR {time.strftime('%H:%M:%S')} ===")
        
        if not os.path.exists(db_path):
            print("Waiting for database...")
            time.sleep(5)
            continue

        conn = sqlite3.connect(db_path)
        
        # Show Open Positions
        print("\n📊 OPEN POSITIONS:")
        pos = pd.read_sql("SELECT strategy, symbol, buy_price, (strftime('%s','now') - strftime('%s',buy_timestamp))/3600.0 as age_hours FROM positions WHERE status='OPEN'", conn)
        if not pos.empty:
            print(pos.to_string(index=False))
        else:
            print("No open positions.")

        # Show Recent Trades (Fixed Query)
        print("\n📈 LAST 5 TRADES:")
        query = """
            SELECT t.timestamp, t.symbol, t.side, t.price, p.profit 
            FROM trades t 
            LEFT JOIN positions p ON t.position_id = p.id 
            ORDER BY t.timestamp DESC LIMIT 5
        """
        trades = pd.read_sql(query, conn)
        if not trades.empty:
            print(trades.to_string(index=False))
        else:
            print("No trades yet.")
            
        conn.close()
        time.sleep(10)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
