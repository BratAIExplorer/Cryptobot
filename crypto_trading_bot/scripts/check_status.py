#!/usr/bin/env python3
"""
Status Checker for Crypto Bot
Run this on the VPS to get the REAL status of your bot.
"""
import os
import sys
import time
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_service_status(service_name):
    """Check systemd service status"""
    if os.name == 'nt':
        return "N/A (Windows)"
    
    try:
        result = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "Unknown"

def check_process(process_name):
    """Check if a python process is running"""
    try:
        if os.name == 'nt':
            # Simple Windows check
            cmd = f'tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            return "Running" if result.stdout else "Stopped"
        else:
            # Linux check
            cmd = f"pgrep -f {process_name}"
            result = subprocess.run(cmd.split(), capture_output=True)
            return "Running" if result.returncode == 0 else "Stopped"
    except:
        return "Unknown"

def check_db_heartbeat():
    """Check the last heartbeat in the database"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'trades.db')
    
    if not os.path.exists(db_path):
        return "❌ Database not found"
        
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT strategy, status, last_heartbeat FROM bot_status", conn)
        conn.close()
        
        if df.empty:
            return "⚠️ No bot status found in DB"
            
        status_lines = []
        for _, row in df.iterrows():
            last_beat = pd.to_datetime(row['last_heartbeat'])
            minutes_ago = (datetime.now() - last_beat).total_seconds() / 60
            
            status_icon = "🟢" if row['status'] == 'RUNNING' and minutes_ago < 5 else "🔴"
            if minutes_ago > 5:
                status_icon = "💀" # Dead/Stale
                
            status_lines.append(f"{status_icon} {row['strategy']}: {row['status']} (Last signal: {minutes_ago:.1f} min ago)")
            
        return "\n".join(status_lines)
    except Exception as e:
        return f"❌ DB Error: {e}"

def check_recent_trades():
    """Check last 5 transactions"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'trades.db')
    
    if not os.path.exists(db_path):
        return "❌ Database not found"
        
    try:
        conn = sqlite3.connect(db_path)
        # Removed 'profit' as it is not in the trades table
        df = pd.read_sql_query("SELECT timestamp, strategy, symbol, side, price FROM trades ORDER BY timestamp DESC LIMIT 5", conn)
        conn.close()
        
        if df.empty:
            return "⚠️ No trades found"
            
        return df.to_string(index=False)
    except Exception as e:
        return f"❌ DB Error: {e}"

def main():
    print("="*50)
    print("🔍 CRYPTO BOT DIAGNOSTIC TOOL")
    print("="*50)
    
    print(f"\n[1] SYSTEM SERVICES (Linux Only)")
    print(f"• Bot Runner: {check_service_status('crypto_bot_runner.service')}")
    print(f"• Dashboard:  {check_service_status('crypto_bot.service')}")
    
    print(f"\n[2] PROCESS CHECK")
    print(f"• run_bot.py: {check_process('run_bot.py')}")
    print(f"• app.py:     {check_process('dashboard/app.py')}")
    
    print(f"\n[3] DATABASE HEARTBEAT")
    print(check_db_heartbeat())
    
    print(f"\n[4] LAST 5 TRANSACTIONS")
    print(check_recent_trades())
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
