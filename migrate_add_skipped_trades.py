"""
Migration: Add skipped_trades table for tracking missed trading opportunities
"""
import sqlite3
import os

DB_PATH = 'data/trades.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skipped_trades'")
    if c.fetchone():
        print("✅ skipped_trades table already exists")
        conn.close()
        return
    
    # Create skipped_trades table
    c.execute('''
        CREATE TABLE skipped_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            strategy TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            intended_amount REAL,
            skip_reason TEXT NOT NULL,
            details TEXT,
            current_exposure REAL,
            max_exposure REAL,
            available_balance REAL
        )
    ''')
    
    # Create indexes for quick queries
    c.execute('CREATE INDEX idx_skipped_timestamp ON skipped_trades(timestamp)')
    c.execute('CREATE INDEX idx_skipped_strategy ON skipped_trades(strategy)')
    c.execute('CREATE INDEX idx_skipped_reason ON skipped_trades(skip_reason)')
    
    conn.commit()
    conn.close()
    
    print("✅ Created skipped_trades table with indexes")
    print("   - Tracks all missed trading opportunities")
    print("   - Captures exposure limits, insufficient funds, etc.")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        exit(1)
    
    migrate()
    print("\n🎉 Migration complete!")
