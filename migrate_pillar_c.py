"""
Database Migration - Pillar C: Manual Activation
Adds missing columns (is_active, manual_allocation_usd, research_notes) to NewCoinWatchlist table.
"""
import sqlite3
import os

# Possible database locations - we check them in order
POSSIBLE_PATHS = [
    "data/trades_v3_paper.db",       # Current standard
    "data/trades_v3_live.db",        # Live mode
    "data/trades_v3_mexc_paper.db",  # Legacy
    "data/trades_v3.db"              # V3 default
]

def migrate():
    db_path = None
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            db_path = p
            break
            
    if not db_path:
        print(f"❌ No database file found in any expected location: {POSSIBLE_PATHS}")
        print("💡 Hint: Run the bot once first to create the initial database file.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ... rest of the script using db_path ...

    # List of new columns to add
    new_columns = [
        ("is_active", "BOOLEAN DEFAULT 0"),
        ("manual_allocation_usd", "FLOAT DEFAULT 0.0"),
        ("research_notes", "TEXT")
    ]

    print(f"🛠️  Starting migration for {db_path}...")
    success_count = 0

    # Ensure table exists first
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS new_coin_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                coin_type TEXT,
                coin_age_days INTEGER,
                classification TEXT,
                risk_level TEXT,
                initial_price FLOAT,
                initial_volume_24h FLOAT,
                last_price FLOAT,
                max_drawdown_pct FLOAT DEFAULT 0.0,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                day_30_price FLOAT,
                status TEXT DEFAULT 'MONITORING',
                is_active BOOLEAN DEFAULT 0,
                manual_allocation_usd FLOAT DEFAULT 0.0,
                research_notes TEXT,
                graduated_at DATETIME
            )
        """)
        print("✅ Table 'new_coin_watchlist' verified/created.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return

    # List of new columns to add (for existing tables)
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE new_coin_watchlist ADD COLUMN {col_name} {col_type}")
            print(f"✅ Added column: {col_name}")
            success_count += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"ℹ️  Column {col_name} already exists. Skipping.")
            else:
                print(f"❌ Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    
    if success_count > 0:
        print(f"🎉 Migration successful! Added {success_count} new columns.")
    else:
        print("✅ Database is already up to date.")

if __name__ == "__main__":
    migrate()
