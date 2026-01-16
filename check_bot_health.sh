#!/bin/bash
# Bot Health Check - Run on VPS at /root/cryptobot_v3
# Checks uptime, database, and recent activity
# Date: 2026-01-16

echo "================================"
echo "🏥 BOT HEALTH CHECK"
echo "================================"
echo ""

cd /root/cryptobot_v3

# 1. Check bot process and uptime
echo "1️⃣  Bot Process & Uptime:"
if pgrep -f "run_bot.py" > /dev/null; then
    BOT_PID=$(pgrep -f "run_bot.py")
    UPTIME=$(ps -p $BOT_PID -o etime= | tr -d ' ')
    START_TIME=$(ps -p $BOT_PID -o lstart= 2>/dev/null)
    echo "   ✅ Bot is RUNNING"
    echo "   PID: $BOT_PID"
    echo "   Uptime: $UPTIME"
    echo "   Started: $START_TIME"
else
    echo "   ❌ Bot is NOT RUNNING!"
    echo ""
    echo "Last 50 lines of log:"
    tail -50 bot.log
    exit 1
fi
echo ""

# 2. Check database files
echo "2️⃣  Database Files:"
echo ""
echo "   Searching for all .db files..."
find data -name "*.db" -type f 2>/dev/null | while read db; do
    SIZE=$(du -h "$db" | cut -f1)
    MODIFIED=$(stat -c %y "$db" | cut -d. -f1)
    echo "   📁 $db"
    echo "      Size: $SIZE"
    echo "      Modified: $MODIFIED"

    # Count trades in each database
    TRADE_COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "      Trades: $TRADE_COUNT"

    if [ "$TRADE_COUNT" -gt 0 ]; then
        echo "      Last trade:"
        sqlite3 -line "$db" "SELECT timestamp, strategy, symbol, side, price FROM trades ORDER BY timestamp DESC LIMIT 1;" 2>/dev/null
    fi
    echo ""
done

if ! find data -name "*.db" -type f 2>/dev/null | grep -q .; then
    echo "   ⚠️  No database files found!"
    echo ""
fi

# 3. Check log file activity
echo "3️⃣  Log Activity:"
if [ -f bot.log ]; then
    LOG_SIZE=$(du -h bot.log | cut -f1)
    LOG_LINES=$(wc -l < bot.log)
    LOG_MODIFIED=$(stat -c %y bot.log | cut -d. -f1)
    echo "   Size: $LOG_SIZE"
    echo "   Lines: $LOG_LINES"
    echo "   Last Modified: $LOG_MODIFIED"
else
    echo "   ❌ No bot.log file!"
fi
echo ""

# 4. Count BUY/SELL signals vs actual trades
echo "4️⃣  Trading Activity Analysis:"
echo ""
if [ -f bot.log ]; then
    BUY_SIGNALS=$(grep -c "BUY Signal" bot.log || echo "0")
    SELL_SIGNALS=$(grep -c "SELL Signal" bot.log || echo "0")
    EXECUTED_BUYS=$(grep -c "EXECUTED.*BUY" bot.log || echo "0")
    EXECUTED_SELLS=$(grep -c "EXECUTED.*SELL" bot.log || echo "0")

    echo "   BUY Signals Generated: $BUY_SIGNALS"
    echo "   SELL Signals Generated: $SELL_SIGNALS"
    echo "   BUYs Executed: $EXECUTED_BUYS"
    echo "   SELLs Executed: $EXECUTED_SELLS"
    echo ""

    if [ "$BUY_SIGNALS" -gt 0 ] && [ "$EXECUTED_BUYS" -eq 0 ]; then
        echo "   ⚠️  WARNING: Signals generated but NO trades executed!"
        echo "      Possible causes:"
        echo "      - Paper mode balance exhausted"
        echo "      - Trade validation failing"
        echo "      - Database write issue"
        echo ""
        echo "   Last 20 lines with 'Signal' or 'EXECUTE':"
        grep -i -E "signal|execute|error" bot.log | tail -20
    fi
fi
echo ""

# 5. Recent log tail (last 50 lines)
echo "5️⃣  Recent Log (Last 50 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -50 bot.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6. Check for errors
echo "6️⃣  Error Check:"
if grep -i "error\|exception\|traceback\|failed" bot.log > /dev/null 2>&1; then
    echo "   ⚠️  ERRORS FOUND in log:"
    echo ""
    grep -i -n "error\|exception\|traceback\|failed" bot.log | tail -20
else
    echo "   ✅ No errors found in log"
fi
echo ""

# 7. Summary
echo "================================"
echo "📊 SUMMARY"
echo "================================"
echo ""

if pgrep -f "run_bot.py" > /dev/null; then
    BOT_PID=$(pgrep -f "run_bot.py")
    UPTIME=$(ps -p $BOT_PID -o etime= | tr -d ' ')
    echo "Bot Status: ✅ RUNNING (PID: $BOT_PID, Uptime: $UPTIME)"
else
    echo "Bot Status: ❌ NOT RUNNING"
fi

# Count total trades across all databases
TOTAL_TRADES=0
find data -name "*.db" -type f 2>/dev/null | while read db; do
    COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    TOTAL_TRADES=$((TOTAL_TRADES + COUNT))
done

echo "Total Trades: $TOTAL_TRADES"
echo ""
echo "Next Steps:"
echo "   - Monitor: tail -f bot.log"
echo "   - Analyze: python3 analyze_trades.py"
echo "   - Quick Check: ./quick_status.sh"
echo ""
