#!/bin/bash
# Comprehensive Bot Monitoring Script
# Run every 10-15 minutes to check bot health
# Usage: bash monitor_bot.sh

echo "========================================"
echo "🤖 CRYPTOBOT LIVE MONITORING"
echo "========================================"
date
echo ""

cd /root/cryptobot_v3

# Check if test is running
echo "1️⃣  PROCESS STATUS"
echo "----------------------------------------"
PID=$(ps aux | grep "python3 test_adapter_paper.py" | grep -v grep | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ TEST NOT RUNNING!"
    echo ""
    echo "To restart:"
    echo "  cd /root/cryptobot_v3"
    echo "  rm -f STOP_SIGNAL"
    echo "  nohup python3 test_adapter_paper.py > test_proven_config.log 2>&1 &"
    exit 1
else
    echo "✅ Test running (PID: $PID)"

    # Check CPU usage
    CPU=$(ps aux | grep $PID | grep -v grep | awk '{print $3}')
    MEM=$(ps aux | grep $PID | grep -v grep | awk '{print $4}')
    echo "   CPU: ${CPU}% | Memory: ${MEM}%"
fi
echo ""

# Check recent cycles
echo "2️⃣  RECENT CYCLE ACTIVITY"
echo "----------------------------------------"
CYCLES=$(tail -200 test_proven_config.log | grep "Cycle #" | tail -5)
if [ -z "$CYCLES" ]; then
    echo "⚠️  No cycles detected in last 200 lines"
    echo "   Test may have just started (wait 5-10 min)"
else
    echo "$CYCLES"
fi
echo ""

# Check both bots evaluating
echo "3️⃣  BOT EVALUATION STATUS"
echo "----------------------------------------"
BTC_EVAL=$(tail -200 test_proven_config.log | grep -c "Evaluating Test Grid Bot BTC")
ETH_EVAL=$(tail -200 test_proven_config.log | grep -c "Evaluating Test Grid Bot ETH")

if [ $BTC_EVAL -gt 0 ]; then
    echo "✅ BTC Bot: Evaluated $BTC_EVAL times (recent 200 lines)"
else
    echo "❌ BTC Bot: NOT EVALUATED"
fi

if [ $ETH_EVAL -gt 0 ]; then
    echo "✅ ETH Bot: Evaluated $ETH_EVAL times (recent 200 lines)"
else
    echo "❌ ETH Bot: NOT EVALUATED"
fi
echo ""

# Check Grid activity
echo "4️⃣  GRID BOT ACTIVITY"
echo "----------------------------------------"
GRID_DEBUG=$(tail -200 test_proven_config.log | grep "GRID DEBUG" | tail -5)
if [ -z "$GRID_DEBUG" ]; then
    echo "⚠️  No Grid DEBUG messages (may be too early)"
else
    echo "$GRID_DEBUG"
fi
echo ""

# Check for blocking issues
echo "5️⃣  BLOCKING ISSUES CHECK"
echo "----------------------------------------"
RISK_STOP=$(tail -100 test_proven_config.log | grep -c "RISK STOP")
DRAWDOWN=$(tail -100 test_proven_config.log | grep -c "Drawdown limit exceeded")
READONLY=$(tail -100 test_proven_config.log | grep -c "readonly database")

if [ $RISK_STOP -gt 0 ]; then
    echo "❌ RISK STOP detected: $RISK_STOP occurrences"
    tail -100 test_proven_config.log | grep "RISK STOP" | tail -3
else
    echo "✅ No RISK STOP issues"
fi

if [ $DRAWDOWN -gt 0 ]; then
    echo "❌ Drawdown limit exceeded: $DRAWDOWN occurrences"
    tail -100 test_proven_config.log | grep "Drawdown limit" | tail -3
else
    echo "✅ No Drawdown blocks"
fi

if [ $READONLY -gt 0 ]; then
    echo "❌ Database readonly errors: $READONLY occurrences"
else
    echo "✅ No database permission issues"
fi
echo ""

# Check positions
echo "6️⃣  POSITIONS STATUS"
echo "----------------------------------------"
DB="data/test_adapter_binance_paper.db"
if [ -f "$DB" ]; then
    TOTAL=$(sqlite3 $DB "SELECT COUNT(*) FROM positions;" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "Total Positions: $TOTAL"

        if [ $TOTAL -gt 0 ]; then
            echo ""
            echo "Position Breakdown:"
            sqlite3 $DB "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;" 2>/dev/null
        fi
    else
        echo "⚠️  Could not query database (may not be initialized yet)"
    fi
else
    echo "⚠️  Database not found"
fi
echo ""

# Check for errors
echo "7️⃣  ERROR CHECK"
echo "----------------------------------------"
ERRORS=$(tail -100 test_proven_config.log | grep -i "error\|exception" | grep -v "no such column" | wc -l)
if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Found $ERRORS error/exception messages:"
    tail -100 test_proven_config.log | grep -i "error\|exception" | grep -v "no such column" | tail -5
else
    echo "✅ No errors in last 100 lines"
fi
echo ""

# Runtime
echo "8️⃣  TEST RUNTIME"
echo "----------------------------------------"
START_TIME=$(head -50 test_proven_config.log | grep "Cycle #1" | sed 's/.*Cycle #1 - //')
if [ ! -z "$START_TIME" ]; then
    echo "Started: $START_TIME"

    # Calculate runtime (rough estimate)
    CURRENT=$(date +%s)
    echo "Current: $(date)"
fi
echo ""

# Status summary
echo "========================================"
echo "📊 STATUS SUMMARY"
echo "========================================"

# Determine overall status
if [ $BTC_EVAL -gt 0 ] && [ $ETH_EVAL -gt 0 ] && [ $RISK_STOP -eq 0 ] && [ $DRAWDOWN -eq 0 ]; then
    echo "🟢 HEALTHY: Both bots active, no blockers"
elif [ $RISK_STOP -gt 0 ] || [ $DRAWDOWN -gt 0 ] || [ $READONLY -gt 0 ]; then
    echo "🔴 BLOCKED: Critical issue preventing trading"
elif [ $BTC_EVAL -eq 0 ] && [ $ETH_EVAL -eq 0 ]; then
    echo "🟡 STARTING: No bot activity yet (wait 5-10 min)"
elif [ $BTC_EVAL -gt 0 ] || [ $ETH_EVAL -gt 0 ]; then
    echo "🟡 PARTIAL: Only one bot active"
else
    echo "🟡 UNKNOWN: Check logs manually"
fi

echo ""
echo "Next check recommended: 10-15 minutes"
echo "Command: bash monitor_bot.sh"
echo ""
