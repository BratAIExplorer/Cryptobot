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

    # List of new columns for watchlist table
    watchlist_columns = [
        ("is_active", "BOOLEAN DEFAULT 0"),
        ("manual_allocation_usd", "FLOAT DEFAULT 0.0"),
        ("research_notes", "TEXT")
    ]

    print(f"🛠️  Starting migration for {db_path}...")
    success_count = 0

    # 1. Migrate new_coin_watchlist
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
    for col_name, col_type in watchlist_columns:
        try:
            cursor.execute(f"ALTER TABLE new_coin_watchlist ADD COLUMN {col_name} {col_type}")
            print(f"✅ [Watchlist] Added column: {col_name}")
            success_count += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Already exists
            else:
                print(f"❌ Error adding {col_name} to watchlist: {e}")

    # 2. Migrate circuit_breaker
    cb_columns = [
        ("last_error_message", "TEXT"),
        ("last_reset_time", "DATETIME"),
        ("total_trips", "INTEGER DEFAULT 0")
    ]
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circuit_breaker (
                id INTEGER PRIMARY KEY,
                is_open BOOLEAN DEFAULT 0,
                consecutive_errors INTEGER DEFAULT 0,
                last_error_time DATETIME
            )
        """)
        # Ensure row 1 exists
        cursor.execute("INSERT OR IGNORE INTO circuit_breaker (id, is_open, consecutive_errors) VALUES (1, 0, 0)")
        print("✅ Table 'circuit_breaker' verified/created.")
    except Exception as e:
        print(f"❌ Error with circuit_breaker table: {e}")

    for col_name, col_type in cb_columns:
        try:
            cursor.execute(f"ALTER TABLE circuit_breaker ADD COLUMN {col_name} {col_type}")
            print(f"✅ [CircuitBreaker] Added column: {col_name}")
            success_count += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Already exists
            else:
                print(f"❌ Error adding {col_name} to circuit_breaker: {e}")

    conn.commit()
    conn.close()
    
    if success_count > 0:
        print(f"🎉 Migration successful! Added/Verified columns.")
    else:
        print("✅ Database is already up to date.")

if __name__ == "__main__":
    migrate()
