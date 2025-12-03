import sqlite3
import os

db_path = 'data/trades.db'

def enable_wal():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check current mode
        c.execute("PRAGMA journal_mode")
        current_mode = c.fetchone()[0]
        print(f"Current journal mode: {current_mode}")
        
        # Enable WAL
        c.execute("PRAGMA journal_mode=WAL")
        new_mode = c.fetchone()[0]
        print(f"New journal mode: {new_mode}")
        
        if new_mode.upper() == 'WAL':
            print("✅ WAL mode enabled successfully!")
        else:
            print("⚠️ Failed to enable WAL mode.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    enable_wal()
