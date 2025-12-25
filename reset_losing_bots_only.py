#!/usr/bin/env python3
"""
🎯 SELECTIVE RESET - Only Losing Bot Strategies

Keeps Grid Bot history intact
Resets only the failing strategies for fresh testing

CRITICAL: This creates backups before resetting!
"""

import sqlite3
import shutil
from datetime import datetime
import os

# Determine correct database path based on mode
MODE = 'paper'  # Change to 'live' if needed
DB_FILENAME = 'trades_v3_live.db' if MODE == 'live' else 'trades_v3_paper.db'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', DB_FILENAME)
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

# Strategies to RESET (losing bots - getting fresh start)
RESET_STRATEGIES = [
    "Buy-the-Dip Strategy",
    "Hyper-Scalper Bot",
    "SMA Trend Bot"
]

# Strategies to KEEP (winning bots - preserve history)
KEEP_STRATEGIES = [
    "Grid Bot BTC",
    "Grid Bot ETH",
    "Hidden Gem Monitor"
]

def selective_reset():
    """Reset only losing strategies, keep winners intact"""
    
    print("=" * 80)
    print("🎯 SELECTIVE RESET - Losing Bots Only")
    print("=" * 80)
    print()
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Backup database first (CRITICAL)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'trades_v3_{MODE}_BEFORE_RESET_{timestamp}.db')
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ BACKUP CREATED: {backup_path}")
        print()
    except Exception as e:
        print(f"❌ ERROR: Could not create backup: {e}")
        print("ABORTING - Will not reset without backup!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🗑️  RESETTING LOSING BOTS")
    print("-" * 80)
    
    # Delete trades for losing strategies
    for strategy in RESET_STRATEGIES:
        cursor.execute("DELETE FROM trades WHERE strategy = ?", (strategy,))
        deleted = cursor.rowcount
        print(f"   ❌ {strategy}: Deleted {deleted} trades")
    
    print()
    
    # Delete positions for losing strategies
    for strategy in RESET_STRATEGIES:
        cursor.execute("DELETE FROM positions WHERE strategy = ?", (strategy,))
        deleted = cursor.rowcount
        print(f"   ❌ {strategy}: Deleted {deleted} positions")
    
    print()
    
    # Reset bot status for losing strategies
    for strategy in RESET_STRATEGIES:
        cursor.execute("DELETE FROM bot_status WHERE strategy = ?", (strategy,))
    
    # Initialize fresh wallets for reset bots
    fresh_balances = {
        "Buy-the-Dip Strategy": 5000.0,
        "Hyper-Scalper Bot": 3000.0,  # Will be renamed to Momentum Swing
        "SMA Trend Bot": 4000.0
    }
    
    print("💰 INITIALIZING FRESH WALLETS")
    print("-" * 80)
    for strategy, balance in fresh_balances.items():
        cursor.execute("""
            INSERT INTO bot_status 
            (strategy, status, total_trades, total_pnl, wallet_balance, started_at, last_heartbeat)
            VALUES (?, 'READY', 0, 0.0, ?, datetime('now'), datetime('now'))
        """, (strategy, balance))
        print(f"   {strategy}: ${balance:,.2f}")
    
    print()
    print("=" * 80)
    print("✅ KEEPING INTACT (Winners - History Preserved)")
    print("=" * 80)
    
    # Show what we're keeping
    for strategy in KEEP_STRATEGIES:
        cursor.execute("""
            SELECT COUNT(*) as trades, 
                   SUM(CASE WHEN side='SELL' THEN cost ELSE 0 END) - 
                   SUM(CASE WHEN side='BUY' THEN cost ELSE 0 END) as pnl
            FROM trades WHERE strategy = ?
        """, (strategy,))
        
        result = cursor.fetchone()
        trades, pnl = result[0], result[1] or 0
        print(f"   ✅ {strategy}: {trades} trades, ${pnl:,.2f} P&L (PRESERVED)")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ SELECTIVE RESET COMPLETE!")
    print("=" * 80)
    print()
    print("📋 SUMMARY:")
    print(f"   Reset: {', '.join(RESET_STRATEGIES)}")
    print(f"   Kept: {', '.join(KEEP_STRATEGIES)}")
    print(f"   Backup: {backup_path}")
    print()
    print("🚀 NEXT STEPS:")
    print("   1. Push code changes to Git")
    print("   2. Pull on VPS")
    print("   3. Restart bots: pm2 restart crypto-bot")
    print("   4. Monitor with daily_bot_check.py")
    print()
    
    return True

if __name__ == "__main__":
    print()
    print("⚠️  This will reset ONLY the losing bot strategies.")
    print("   Grid Bots will keep their history and continue running.")
    print()
    print(f"   Database: {DB_PATH}")
    print(f"   Mode: {MODE.upper()}")
    print()
    
    response = input("Continue with selective reset? (yes/no): ")
    
    if response.lower() == 'yes':
        success = selective_reset()
        if success:
            print("✅ Safe to proceed with testing!")
    else:
        print("❌ Reset cancelled - no changes made")
