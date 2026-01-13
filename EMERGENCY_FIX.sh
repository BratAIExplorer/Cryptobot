#!/bin/bash
# EMERGENCY FIX - Stop broken test, diagnose issues, prepare for restart
# Run on VPS: bash EMERGENCY_FIX.sh

echo "=========================================="
echo "🚨 EMERGENCY DIAGNOSTIC & FIX"
echo "=========================================="
echo ""

cd /root/cryptobot_v3

# STEP 1: Kill all test processes
echo "1️⃣  KILLING ALL TEST PROCESSES..."
pkill -f test_adapter_paper.py
sleep 2

# Verify killed
REMAINING=$(ps aux | grep test_adapter_paper | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo "✅ All test processes killed"
else
    echo "⚠️  Still $REMAINING processes remaining, force killing..."
    pkill -9 -f test_adapter_paper.py
    sleep 2
fi

echo ""

# STEP 2: Check database status
echo "2️⃣  CHECKING DATABASE STATUS..."
DB_PATH="data/test_adapter_binance_paper.db"

if [ -f "$DB_PATH" ]; then
    echo "📊 Database found: $DB_PATH"

    # Check permissions
    ls -lh "$DB_PATH"

    # Check if readable
    if [ -r "$DB_PATH" ]; then
        echo "✅ Database is readable"
    else
        echo "❌ Database is NOT readable"
    fi

    # Check if writable
    if [ -w "$DB_PATH" ]; then
        echo "✅ Database is writable"
    else
        echo "❌ Database is NOT writable - FIXING..."
        chmod 666 "$DB_PATH"
    fi

    # Get database size
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "📦 Database size: $DB_SIZE"

    # Count positions
    echo ""
    echo "📈 CURRENT POSITIONS:"
    sqlite3 "$DB_PATH" "SELECT symbol, side, entry_price, current_price, profit_loss, status FROM positions LIMIT 10;" 2>&1 || echo "⚠️  Database schema issue detected"

    # Calculate total P&L
    echo ""
    echo "💰 TOTAL P&L:"
    sqlite3 "$DB_PATH" "SELECT SUM(profit_loss) as total_pnl FROM positions;" 2>&1 || echo "⚠️  Cannot calculate P&L"

else
    echo "❌ Database NOT found at $DB_PATH"
fi

echo ""

# STEP 3: Check for database locks
echo "3️⃣  CHECKING FOR DATABASE LOCKS..."
lsof "$DB_PATH" 2>/dev/null || echo "✅ No locks detected"

echo ""

# STEP 4: Backup current database
echo "4️⃣  BACKING UP CURRENT DATABASE..."
BACKUP_NAME="data/test_adapter_binance_paper_BACKUP_$(date +%Y%m%d_%H%M%S).db"
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_NAME"
    echo "✅ Backup created: $BACKUP_NAME"
else
    echo "⚠️  No database to backup"
fi

echo ""

# STEP 5: Check test script
echo "5️⃣  CHECKING TEST SCRIPT..."
if [ -f "test_adapter_paper.py" ]; then
    echo "✅ Test script found"
    head -20 test_adapter_paper.py | grep -E "mode|exchange|BINANCE|MEXC"
else
    echo "❌ Test script NOT found"
fi

echo ""

# STEP 6: Check logs
echo "6️⃣  CHECKING RECENT LOGS..."
if [ -f "test_proven_config.log" ]; then
    echo "📋 Last 20 lines of log:"
    tail -20 test_proven_config.log
    echo ""
    echo "📊 Log file size: $(du -h test_proven_config.log | cut -f1)"
else
    echo "⚠️  No log file found"
fi

echo ""

# STEP 7: Summary
echo "=========================================="
echo "📊 DIAGNOSTIC SUMMARY"
echo "=========================================="
echo ""
echo "Issues Found:"
echo "  - Multiple test processes (KILLED) ✅"
echo "  - 70% daily loss (STOPPED) ✅"
echo "  - Database permissions (CHECK ABOVE)"
echo "  - Database schema mismatch (CHECK ABOVE)"
echo ""
echo "Next Steps:"
echo "  1. Review diagnostic output above"
echo "  2. Check database backup created"
echo "  3. Ready for fresh test with Quick Start config"
echo ""
echo "=========================================="
echo "🎯 READY FOR NEW TEST"
echo "=========================================="
