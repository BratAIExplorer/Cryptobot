#!/usr/bin/env python3
"""
🚀 BINANCE GRID PULSE
Pinpoint stats for Binance Grid Bots:
1. Duration (How long running)
2. 48-Hour Volume (Recent transactions)

Usage: python3 binance_grid_pulse.py
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^100}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}\n")

def get_binance_grid_stats(db_path):
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check schema
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        has_exchange = 'exchange' in columns
        
        # Build strict Binance filter
        where_clause = "WHERE strategy LIKE 'Grid Bot%'"
        if has_exchange:
            where_clause += " AND UPPER(exchange) LIKE '%BINANCE%'"
        else:
            # If no exchange column, we check if the db path suggests it's a binance db
            if 'binance' not in str(db_path).lower() and 'trades.db' not in str(db_path).lower():
                return None

        # 1. First trade to calculate duration
        duration_query = f"""
        SELECT 
            strategy,
            MIN(timestamp) as first_trade,
            COUNT(*) as grand_total
        FROM trades
        {where_clause}
        GROUP BY strategy
        """
        
        # 2. Trades in last 48 hours
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
        if not durations:
            conn.close()
            return None
            
        recents = {row['strategy']: row['recent_trades'] for row in cursor.execute(recent_query, (forty_eight_h_ago,)).fetchall()}
        
        conn.close()
        return {'durations': durations, 'recents': recents}
    except Exception:
        return None

def format_runtime(start_time_str):
    try:
        # Standardize timestamp removing fractional seconds if present
        clean_time = start_time_str.split('.')[0].replace('T', ' ')
        start_dt = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
        diff = datetime.now() - start_dt
        
        days = diff.days
        hours = diff.seconds // 3600
        
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h"
    except:
        return "N/A"

def main():
    print_header("BINANCE GRID BOT PULSE CHECK")
    
    data_dir = Path('./data')
    dbs = list(data_dir.rglob('*.db'))
    
    header = f"{'Database':<25} {'Strategy':<18} {'First Trade':<20} {'Runtime':<12} {'48h Trades':<10}"
    print(f"{Colors.BOLD}{header}{Colors.RESET}")
    print("─" * 100)
    
    found = False
    for db_path in dbs:
        db_name = os.path.relpath(db_path, data_dir)
        stats = get_binance_grid_stats(str(db_path))
        
        if stats:
            for bot in stats['durations']:
                strategy = bot['strategy']
                first = bot['first_trade']
                runtime = format_runtime(first)
                recent = stats['recents'].get(strategy, 0)
                
                # Highlight active bots
                count_color = Colors.GREEN if recent > 0 else Colors.RESET
                
                print(f"{db_name:<25} {strategy:<18} {first[:19]:<20} {runtime:<12} {count_color}{recent:<10}{Colors.RESET}")
                found = True
                
    if not found:
        print(f"{Colors.YELLOW}No Binance-tagged Grid Bot transactions found in any database.{Colors.RESET}")
        print(f"Tip: If your Binance bots aren't explicitly tagged 'BINANCE' in the 'exchange' column,")
        print(f"they may be missing from this filtered report.")

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
