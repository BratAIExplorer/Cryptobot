#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

def get_grid_stats(db_path):
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get duration
        duration_query = """
        SELECT 
            strategy,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade,
            COUNT(*) as total_trades
        FROM trades
        WHERE strategy LIKE 'Grid Bot%'
        GROUP BY strategy
        """
        
        # Get last 48h trades
        forty_eight_h_ago = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
        recent_query = """
        SELECT 
            strategy,
            COUNT(*) as recent_trades
        FROM trades
        WHERE strategy LIKE 'Grid Bot%' AND timestamp >= ?
        GROUP BY strategy
        """
        
        durations = cursor.execute(duration_query).fetchall()
        recents = {row['strategy']: row['recent_trades'] for row in cursor.execute(recent_query, (forty_eight_h_ago,)).fetchall()}
        
        conn.close()
        return {'durations': durations, 'recents': recents}
    except Exception as e:
        print(f"Error reading {db_path}: {e}")
        return None

def main():
    data_dir = Path('c:/CryptoBot_Project/data')
    dbs = list(data_dir.rglob('*.db'))
    
    print(f"{'Database':<30} {'Strategy':<20} {'First Trade':<20} {'Trades (48h)':<15}")
    print("-" * 85)
    
    for db_path in dbs:
        stats = get_grid_stats(str(db_path))
        if stats and stats['durations']:
            db_rel = os.path.relpath(db_path, data_dir)
            for row in stats['durations']:
                strategy = row['strategy']
                first = row['first_trade']
                recent = stats['recents'].get(strategy, 0)
                print(f"{db_rel:<30} {strategy:<20} {first:<20} {recent:<15}")

if __name__ == "__main__":
    main()
