#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

def get_binance_grid_stats(db_path):
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if exchange column exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        has_exchange = 'exchange' in columns
        
        where_clause = "WHERE strategy LIKE 'Grid Bot%'"
        if has_exchange:
            where_clause += " AND UPPER(exchange) LIKE '%BINANCE%'"
        elif 'binance' not in str(db_path).lower() and 'trades.db' not in str(db_path).lower():
            # If no exchange column, only check if path implies binance
            return None

        # Get duration
        duration_query = f"""
        SELECT 
            strategy,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade,
            COUNT(*) as total_trades,
            {"exchange" if has_exchange else "'Unknown'"} as exchange
        FROM trades
        {where_clause}
        GROUP BY strategy
        """
        
        # Get last 48h trades
        forty_eight_h_ago = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
        recent_query = f"""
        SELECT 
            strategy,
            COUNT(*) as recent_trades
        FROM trades
        {where_clause} AND timestamp >= ?
        GROUP BY strategy
        """
        
        durations = cursor.execute(duration_query).fetchall()
        recents = {row['strategy']: row['recent_trades'] for row in cursor.execute(recent_query, (forty_eight_h_ago,)).fetchall()}
        
        conn.close()
        return {'durations': durations, 'recents': recents}
    except Exception as e:
        # print(f"Error reading {db_path}: {e}")
        return None

def main():
    data_dir = Path('c:/CryptoBot_Project/data')
    dbs = list(data_dir.rglob('*.db'))
    
    output = []
    output.append("=" * 100)
    output.append(f"{'BINANCE GRID BOT PERFORMANCE (Last 48h & Duration)':^100}")
    output.append("=" * 100 + "\n")
    
    header = f"{'Database':<25} {'Strategy':<15} {'First Trade':<20} {'Runtime':<15} {'48h Trades':<10}"
    output.append(header)
    output.append("-" * 100)
    
    now = datetime.now()
    found = False
    
    for db_path in dbs:
        stats = get_binance_grid_stats(str(db_path))
        if stats and stats['durations']:
            db_rel = os.path.relpath(db_path, data_dir)
            for row in stats['durations']:
                strategy = row['strategy']
                first_str = row['first_trade']
                
                try:
                    # Handle possible different timestamp formats
                    first_dt = datetime.strptime(first_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    runtime = now - first_dt
                    days = runtime.days
                    hours = runtime.seconds // 3600
                    runtime_str = f"{days}d {hours}h"
                except:
                    runtime_str = "Unknown"
                
                recent = stats['recents'].get(strategy, 0)
                output.append(f"{db_rel:<25} {strategy:<15} {first_str[:19]:<20} {runtime_str:<15} {recent:<10}")
                found = True
    
    if not found:
        output.append("No Binance Grid trades found across databases.")
    
    output.append("\n" + "=" * 100 + "\n")
    
    final_output = "\n".join(output)
    print(final_output)
    with open('grid_stats.txt', 'w') as f:
        f.write(final_output)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

if __name__ == "__main__":
    main()
