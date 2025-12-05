import sqlite3
import pandas as pd
import os

DB_PATH = 'crypto_trading_bot/data/trades.db'

def fix_ghost_positions():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Checking for ghost positions...")
    
    # 1. Get all positions marked as OPEN
    c.execute("SELECT id, symbol, strategy, amount FROM positions WHERE status = 'OPEN'")
    open_positions = c.fetchall()
    
    print(f"Found {len(open_positions)} OPEN positions in DB.")
    
    # 2. Check for duplicates or invalid entries
    # (Optional: Add logic here if needed)
    
    # 3. Fix specific known ghost positions (like ID #3 from logs)
    # The log said: "[ERROR] Position #3 not found or already closed"
    # This implies the engine THOUGHT it was open (maybe in memory?) but DB said no?
    # OR, the DB has it as OPEN but the SELECT failed?
    
    # Let's just print them for now
    for pos in open_positions:
        print(f"  ID: {pos[0]} | {pos[1]} | {pos[2]} | Amt: {pos[3]}")

    # 4. Check if any positions have invalid data (e.g. None)
    c.execute("SELECT * FROM positions WHERE buy_price IS NULL OR amount IS NULL")
    invalid = c.fetchall()
    if invalid:
        print(f"Found {len(invalid)} invalid positions. Cleaning up...")
        c.execute("DELETE FROM positions WHERE buy_price IS NULL OR amount IS NULL")
        conn.commit()
        print("Cleaned up invalid positions.")
        
    conn.close()
    print("Done.")

if __name__ == "__main__":
    fix_ghost_positions()
