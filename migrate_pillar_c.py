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

    # List of *all* required columns for watchlist table (excluding basic ones)
    watchlist_columns = [
        ("base_symbol", "TEXT"),
        ("listing_date_mexc", "DATETIME"),
        ("first_listing_date_anywhere", "DATETIME"),
        ("coin_type", "TEXT"),
        ("coin_age_days", "INTEGER"),
        ("classification", "TEXT"),
        ("risk_level", "TEXT"),
        ("status", "TEXT DEFAULT 'MONITORING'"),
        ("rejection_reason", "TEXT"),
        ("initial_price", "FLOAT"),
        ("initial_volume_24h", "FLOAT"),
        ("initial_market_cap", "FLOAT"),
        ("initial_liquidity", "FLOAT"),
        ("day_7_price", "FLOAT"),
        ("day_7_volume", "FLOAT"),
        ("day_14_price", "FLOAT"),
        ("day_14_volume", "FLOAT"),
        ("day_30_price", "FLOAT"),
        ("day_30_volume", "FLOAT"),
        ("max_drawdown_pct", "FLOAT DEFAULT 0.0"),
        ("max_pump_pct", "FLOAT DEFAULT 0.0"),
        ("graduated_at", "DATETIME"),
        ("is_active", "BOOLEAN DEFAULT 0"),
        ("manual_allocation_usd", "FLOAT DEFAULT 0.0"),
        ("research_notes", "TEXT"),
        ("metadata_json", "TEXT"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ]

    print(f"🛠️  Starting migration for {db_path}...")
    success_count = 0

    # 1. Migrate new_coin_watchlist
    # Ensure table exists with at least the basic primary key
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS new_coin_watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT UNIQUE)")
        print("✅ Table 'new_coin_watchlist' verified/created.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return

    # Add every column one by one if missing
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
        ("is_open", "BOOLEAN DEFAULT 0"),
        ("consecutive_errors", "INTEGER DEFAULT 0"),
        ("last_error_time", "DATETIME"),
        ("last_error_message", "TEXT"),
        ("last_reset_time", "DATETIME"),
        ("total_trips", "INTEGER DEFAULT 0")
    ]
    
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS circuit_breaker (id INTEGER PRIMARY KEY)")
        # Ensure row 1 exists
        cursor.execute("INSERT OR IGNORE INTO circuit_breaker (id) VALUES (1)")
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
        print(f"🎉 Migration successful! Added/Verified {success_count} columns.")
    else:
        print("✅ Database is already up to date.")

if __name__ == "__main__":
    migrate()
