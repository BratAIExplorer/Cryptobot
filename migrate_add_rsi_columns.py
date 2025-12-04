#!/usr/bin/env python3
"""
Database Migration: Add RSI Tracking Columns
Adds entry_rsi and exit_rsi columns to positions table for better analytics.
Safe to run multiple times.
"""
import sqlite3
import os

DB_PATH = 'data/trades.db'

def migrate_add_rsi_columns():
    """Add entry_rsi and exit_rsi columns to positions table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    print("=" * 60)
    print("🔄 Database Migration: Adding RSI Tracking Columns")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check current schema
        c.execute("PRAGMA table_info(positions)")
        columns = {row[1] for row in c.fetchall()}
        print(f"📊 Current columns: {columns}")
        
        changes_made = False
        
        # Add entry_rsi column if not exists
        if 'entry_rsi' not in columns:
            print("➕ Adding 'entry_rsi' column...")
            c.execute('ALTER TABLE positions ADD COLUMN entry_rsi REAL')
            changes_made = True
            print("✅ Added 'entry_rsi' column")
        else:
            print("⏭️  'entry_rsi' column already exists")
        
        # Add exit_rsi column if not exists
        if 'exit_rsi' not in columns:
            print("➕ Adding 'exit_rsi' column...")
            c.execute('ALTER TABLE positions ADD COLUMN exit_rsi REAL')
            changes_made = True
            print("✅ Added 'exit_rsi' column")
        else:
            print("⏭️  'exit_rsi' column already exists")
        
        if changes_made:
            conn.commit()
            print("\n✅ Migration completed successfully!")
        else:
            print("\n✅ No migration needed - schema already up to date")
        
        # Verify new schema
        c.execute("PRAGMA table_info(positions)")
        new_columns = {row[1] for row in c.fetchall()}
        print(f"\n📊 Updated columns: {new_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_add_rsi_columns()
    exit(0 if success else 1)
