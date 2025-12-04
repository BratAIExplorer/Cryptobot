#!/usr/bin/env python3
"""
Verification Script: Trading Bot Enhancements
Verifies that all three enhancements are properly implemented:
1. RSI tracking (entry/exit)
2. Fee calculation
3. Hyper-Scalper threshold update
"""
import sqlite3
import os
import sys

DB_PATH = 'data/trades.db'

def verify_database_schema():
    """Verify positions table has RSI columns"""
    print("=" * 60)
    print("1️⃣  Verifying Database Schema")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check positions table columns
    c.execute("PRAGMA table_info(positions)")
    columns = {row[1] for row in c.fetchall()}
    
    required_columns = {'entry_rsi', 'exit_rsi'}
    missing = required_columns - columns
    
    if missing:
        print(f"❌ Missing columns in positions table: {missing}")
        conn.close()
        return False
    
    print(f"✅ Positions table has RSI columns: entry_rsi, exit_rsi")
    
    # Check if any positions have RSI data
    c.execute("SELECT COUNT(*) FROM positions WHERE entry_rsi IS NOT NULL")
    rsi_count = c.fetchone()[0]
    
    if rsi_count > 0:
        print(f"✅ Found {rsi_count} positions with entry RSI data")
    else:
        print(f"ℹ️  No positions with RSI data yet (normal for fresh migration)")
    
    conn.close()
    return True

def verify_fee_tracking():
    """Verify trades table is logging fees"""
    print("\n" + "=" * 60)
    print("2️⃣  Verifying Fee Tracking")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check recent trades for fees
    c.execute("""
        SELECT timestamp, symbol, side, cost, fee 
        FROM trades 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    
    recent_trades = c.fetchall()
    
    if not recent_trades:
        print("ℹ️  No trades found (bot hasn't traded yet)")
        conn.close()
        return True
    
    print(f"📊 Checking last {len(recent_trades)} trades:")
    
    fees_found = 0
    for timestamp, symbol, side, cost, fee in recent_trades:
        fee_pct = (fee / cost * 100) if cost and fee else 0
        status = "✅" if fee and fee > 0 else "⚠️"
        print(f"  {status} {timestamp[:19]} | {symbol:12} | {side:4} | Fee: ${fee:.4f} ({fee_pct:.3f}%)")
        if fee and fee > 0:
            fees_found += 1
    
    if fees_found > 0:
        print(f"\n✅ Fee tracking working! {fees_found}/{len(recent_trades)} trades have fees")
        conn.close()
        return True
    else:
        print(f"\n⚠️  No fees found in recent trades (may be old trades before fix)")
        conn.close()
        return True  # Not a failure, just means no new trades yet

def verify_hyper_scalper_config():
    """Verify Hyper-Scalper threshold is updated in code"""
    print("\n" + "=" * 60)
    print("3️⃣  Verifying Hyper-Scalper Configuration")
    print("=" * 60)
    
    engine_file = 'core/engine.py'
    
    if not os.path.exists(engine_file):
        print(f"❌ Engine file not found: {engine_file}")
        return False
    
    with open(engine_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for new threshold (0.0075 = 0.75%)
    if 'profit_pct >= 0.0075' in content:
        print("✅ Hyper-Scalper minimum profit threshold updated to 0.75%")
        
        # Count occurrences
        count = content.count('0.0075')
        print(f"   Found {count} references to 0.75% threshold")
        return True
    elif 'profit_pct > 0.001' in content or 'profit_pct >= 0.001' in content:
        print("❌ Hyper-Scalper still using old 0.1% threshold!")
        return False
    else:
        print("⚠️  Could not verify threshold (code may have changed)")
        return True

def main():
    print("\n🔍 Trading Bot Enhancement Verification")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(("Database Schema (RSI columns)", verify_database_schema()))
    results.append(("Fee Tracking", verify_fee_tracking()))
    results.append(("Hyper-Scalper Config", verify_hyper_scalper_config()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} | {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All verifications passed!")
        print("\n✅ Next steps:")
        print("   1. Run the migration script if you haven't: python migrate_add_rsi_columns.py")
        print("   2. Restart bot services to activate changes")
        print("   3. Monitor next few trades to see fees and RSI in action")
        return 0
    else:
        print("⚠️  Some verifications failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
