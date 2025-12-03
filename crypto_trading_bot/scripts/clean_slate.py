#!/usr/bin/env python3
"""
Clean Slate Script - Safely reset database with backup
"""
import os
import sys
import shutil
from datetime import datetime
import sqlite3
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.logger import TradeLogger

def main():
    print("=" * 60)
    print("🔄 Clean Slate - Database Reset with Backup")
    print("=" * 60)
    
    db_path = 'data/trades.db'
    
    if not os.path.exists(db_path):
        print(f"✅ No existing database found at {db_path}")
        print("Creating fresh database...")
        logger = TradeLogger(db_path)
        print("✅ Fresh database created successfully")
        return
    
    # Backup existing database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f'data/trades_backup_{timestamp}.db'
    
    print(f"\n📦 Backing up existing database...")
    shutil.copy(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    # Export orphaned trades to CSV
    print(f"\n📊 Exporting orphaned trades to CSV...")
    try:
        conn = sqlite3.connect(db_path)
        trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
        
        if not trades_df.empty:
            export_path = f'data/orphaned_trades_{timestamp}.csv'
            trades_df.to_csv(export_path, index=False)
            print(f"✅ Exported {len(trades_df)} trades to: {export_path}")
        else:
            print("ℹ️  No trades to export")
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not export trades: {e}")
    
    # Delete old database
    print(f"\n🗑️  Deleting old database...")
    os.remove(db_path)
    print("✅ Old database deleted")
    
    # Create fresh database
    print(f"\n🆕 Creating fresh database...")
    logger = TradeLogger(db_path)
    print("✅ Fresh database created with verified schema")
    
    print("\n" + "=" * 60)
    print("✅ Clean Slate Complete!")
    print("=" * 60)
    print(f"Backup saved to: {backup_path}")
    print(f"Fresh database ready at: {db_path}")
    print("\nYou can now start the bot with: python run_bot.py")

if __name__ == "__main__":
    main()
