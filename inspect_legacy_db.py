import sqlite3
import pandas as pd
import os

LEGACY_DB = 'data/trades.db'

def inspect():
    if not os.path.exists(LEGACY_DB):
        print(f"❌ Legacy DB not found: {LEGACY_DB}")
        return

    conn = sqlite3.connect(LEGACY_DB)
    try:
        print(f"--- Legacy Schema: {LEGACY_DB} ---")
        
        # Check positions table
        try:
            pos_df = pd.read_sql_query("SELECT * FROM positions LIMIT 5", conn)
            print("\nColumns in 'positions' table:")
            print(pos_df.columns.tolist())
            print("\nSample Position Data:")
            print(pos_df)
        except Exception as e:
            print(f"Error reading positions: {e}")

        # Check trades table
        try:
            trades_df = pd.read_sql_query("SELECT * FROM trades LIMIT 5", conn)
            print("\nColumns in 'trades' table:")
            print(trades_df.columns.tolist())
        except Exception as e:
            print(f"Error reading trades: {e}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    inspect()
