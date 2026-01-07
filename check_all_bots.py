#!/usr/bin/env python3
"""
🤖 COMPREHENSIVE BOT STATUS CHECKER
Checks all parallel bots across all databases and provides unified status view

Usage: python check_all_bots.py
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
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^100}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}\n")

def print_section(title, icon="📊"):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{icon} {title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 100}{Colors.RESET}")

def format_pnl(pnl):
    """Format P&L with color"""
    if pnl > 0:
        return f"{Colors.GREEN}+${pnl:,.2f}{Colors.RESET}"
    elif pnl < 0:
        return f"{Colors.RED}-${abs(pnl):,.2f}{Colors.RESET}"
    else:
        return f"{Colors.YELLOW}${pnl:,.2f}{Colors.RESET}"

def get_health_indicator(pnl, trades):
    """Get health status indicator"""
    if trades == 0:
        return f"{Colors.YELLOW}⚠️  IDLE{Colors.RESET}"
    elif pnl > 100:
        return f"{Colors.GREEN}🟢 EXCELLENT{Colors.RESET}"
    elif pnl > 0:
        return f"{Colors.GREEN}✅ PROFITABLE{Colors.RESET}"
    elif pnl > -100:
        return f"{Colors.YELLOW}🟡 WATCH{Colors.RESET}"
    else:
        return f"{Colors.RED}🔴 CRITICAL{Colors.RESET}"

def check_database(db_path, db_name):
    """Check a single database for bot status"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get bot performance by strategy
        query = """
        SELECT 
            strategy,
            COUNT(*) as total_trades,
            SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sells,
            ROUND(SUM(CASE WHEN side = 'SELL' THEN cost ELSE 0 END) - 
                  SUM(CASE WHEN side = 'BUY' THEN cost ELSE 0 END), 2) as pnl,
            ROUND(100.0 * SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) / 
                  NULLIF(COUNT(*), 0), 1) as sell_rate,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade
        FROM trades
        GROUP BY strategy
        ORDER BY pnl DESC
        """
        
        results = cursor.execute(query).fetchall()
        
        # Get open positions count
        try:
            positions_query = """
            SELECT strategy, COUNT(*) as open_positions
            FROM positions
            WHERE status = 'OPEN'
            GROUP BY strategy
            """
            positions = {row['strategy']: row['open_positions'] 
                        for row in cursor.execute(positions_query).fetchall()}
        except:
            positions = {}
        
        # Get bot status if available
        try:
            status_query = "SELECT strategy, status, wallet_balance FROM bot_status"
            bot_status = {row['strategy']: {
                'status': row['status'], 
                'balance': row['wallet_balance']
            } for row in cursor.execute(status_query).fetchall()}
        except:
            bot_status = {}
        
        conn.close()
        
        return {
            'db_name': db_name,
            'db_path': db_path,
            'bots': results,
            'positions': positions,
            'status': bot_status
        }
        
    except Exception as e:
        print(f"{Colors.RED}Error reading {db_name}: {e}{Colors.RESET}")
        return None

def display_bot_summary(db_info):
    """Display summary for one database"""
    if not db_info or not db_info['bots']:
        return
    
    print_section(f"Database: {db_info['db_name']}", "💾")
    print(f"{Colors.CYAN}Path: {db_info['db_path']}{Colors.RESET}\n")
    
    # Header
    header = f"{'Bot Strategy':<30} {'Trades':<8} {'Buys':<6} {'Sells':<6} {'Open':<6} {'P&L':<15} {'Health':<20}"
    print(f"{Colors.BOLD}{header}{Colors.RESET}")
    print("─" * 100)
    
    total_pnl = 0
    total_trades = 0
    
    for bot in db_info['bots']:
        strategy = bot['strategy']
        trades = bot['total_trades']
        buys = bot['buys']
        sells = bot['sells']
        pnl = bot['pnl'] or 0
        open_pos = db_info['positions'].get(strategy, 0)
        
        total_pnl += pnl
        total_trades += trades
        
        # Get status info if available
        status_info = db_info['status'].get(strategy, {})
        balance = status_info.get('balance', 'N/A')
        
        health = get_health_indicator(pnl, trades)
        pnl_str = format_pnl(pnl)
        
        print(f"{strategy:<30} {trades:<8} {buys:<6} {sells:<6} {open_pos:<6} {pnl_str:<24} {health}")
    
    print("─" * 100)
    print(f"{Colors.BOLD}{'TOTAL':<30} {total_trades:<8} {'':<6} {'':<6} {'':<6} {format_pnl(total_pnl):<24}{Colors.RESET}")

def check_all_databases():
    """Check all known databases"""
    project_root = Path(__file__).parent
    data_dir = project_root / 'data'
    
    # Define all databases to check
    databases = []
    
    # Check main databases
    if (data_dir / 'trades_v3_paper.db').exists():
        databases.append(('trades_v3_paper.db', str(data_dir / 'trades_v3_paper.db')))
    
    if (data_dir / 'trades_v3_live.db').exists():
        databases.append(('trades_v3_live.db', str(data_dir / 'trades_v3_live.db')))
    
    if (data_dir / 'trades_v3.db').exists():
        databases.append(('trades_v3.db', str(data_dir / 'trades_v3.db')))
    
    # Check exchange-specific databases
    for exchange in ['binance', 'mexc', 'multi']:
        exchange_dir = data_dir / exchange
        if exchange_dir.exists():
            for db_file in exchange_dir.glob('*.db'):
                databases.append((f'{exchange}/{db_file.name}', str(db_file)))
    
    # Check old format
    if (data_dir / 'trades_paper.db').exists():
        databases.append(('trades_paper.db (LEGACY)', str(data_dir / 'trades_paper.db')))
    
    if (data_dir / 'trades.db').exists():
        databases.append(('trades.db (LEGACY)', str(data_dir / 'trades.db')))
    
    return databases

def show_warnings(all_db_info):
    """Show warnings and alerts"""
    print_section("⚠️  Warnings & Alerts", "🚨")
    
    warnings_found = False
    
    for db_info in all_db_info:
        if not db_info or not db_info['bots']:
            continue
            
        for bot in db_info['bots']:
            strategy = bot['strategy']
            trades = bot['total_trades']
            buys = bot['buys']
            sells = bot['sells']
            pnl = bot['pnl'] or 0
            
            # Check for issues
            if pnl < -500:
                print(f"{Colors.RED}💀 CRITICAL: {strategy} is down ${abs(pnl):,.2f}!{Colors.RESET}")
                warnings_found = True
            
            if trades > 0 and sells == 0:
                print(f"{Colors.RED}⚠️  WARNING: {strategy} has {buys} buys but ZERO sells (positions stuck!){Colors.RESET}")
                warnings_found = True
            
            if buys > sells * 3 and sells > 0:
                print(f"{Colors.YELLOW}⚠️  ALERT: {strategy} has {buys} buys vs {sells} sells (imbalance!){Colors.RESET}")
                warnings_found = True
            
            if trades > 100:
                print(f"{Colors.YELLOW}⚠️  INFO: {strategy} is very active ({trades} trades - check for overtrading){Colors.RESET}")
                warnings_found = True
    
    if not warnings_found:
        print(f"{Colors.GREEN}✅ No critical warnings detected{Colors.RESET}")

def show_summary_stats(all_db_info):
    """Show overall summary statistics"""
    print_section("📈 Overall Performance Summary", "💰")
    
    total_pnl = 0
    total_trades = 0
    profitable_bots = 0
    losing_bots = 0
    idle_bots = 0
    
    for db_info in all_db_info:
        if not db_info or not db_info['bots']:
            continue
        
        for bot in db_info['bots']:
            pnl = bot['pnl'] or 0
            trades = bot['total_trades']
            
            total_pnl += pnl
            total_trades += trades
            
            if trades == 0:
                idle_bots += 1
            elif pnl > 0:
                profitable_bots += 1
            else:
                losing_bots += 1
    
    print(f"\n{Colors.BOLD}Total P&L:{Colors.RESET} {format_pnl(total_pnl)}")
    print(f"{Colors.BOLD}Total Trades:{Colors.RESET} {total_trades}")
    print(f"{Colors.BOLD}Bot Status:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Profitable: {profitable_bots}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Losing: {losing_bots}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠️  Idle: {idle_bots}{Colors.RESET}")

def main():
    """Main function"""
    print_header(f"🤖 MULTI-BOT STATUS DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find all databases
    databases = check_all_databases()
    
    if not databases:
        print(f"{Colors.RED}❌ No trading databases found!{Colors.RESET}")
        return
    
    print(f"{Colors.CYAN}Found {len(databases)} database(s) to check...{Colors.RESET}\n")
    
    # Check all databases
    all_db_info = []
    for db_name, db_path in databases:
        db_info = check_database(db_path, db_name)
        if db_info:
            all_db_info.append(db_info)
            display_bot_summary(db_info)
    
    # Show summary and warnings
    if all_db_info:
        show_summary_stats(all_db_info)
        show_warnings(all_db_info)
    
    # Tips
    print_section("💡 Quick Actions", "🔧")
    print(f"{Colors.CYAN}• Daily check:{Colors.RESET} python daily_bot_check.py")
    print(f"{Colors.CYAN}• Reset losing bots:{Colors.RESET} python reset_losing_bots_only.py")
    print(f"{Colors.CYAN}• Validate bots:{Colors.RESET} python validate_all_bots.py")
    print(f"{Colors.CYAN}• Live monitor:{Colors.RESET} python monitor.py")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 100}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
