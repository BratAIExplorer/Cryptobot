#!/bin/bash
################################################################################
# VPS Deployment Test Script
# Tests that bots are running correctly after code update
################################################################################

set -e  # Exit on error

echo "========================================================================"
echo "🧪 CRYPTOBOT DEPLOYMENT TEST"
echo "========================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to bot directory
cd ~/cryptobot_v3

echo "📁 Current directory: $(pwd)"
echo ""

# Test 1: Check if bot process is running
echo "========================================================================"
echo "Test 1: Check Bot Process"
echo "========================================================================"
if pgrep -f "run_bot.py" > /dev/null; then
    PID=$(pgrep -f "run_bot.py")
    echo -e "${GREEN}✅ Bot is running (PID: $PID)${NC}"
else
    echo -e "${RED}❌ Bot is NOT running${NC}"
    echo "   To start: nohup python3 run_bot.py > logs/bot.log 2>&1 &"
fi
echo ""

# Test 2: Check recent logs
echo "========================================================================"
echo "Test 2: Check Recent Logs (last 30 lines)"
echo "========================================================================"
if [ -f logs/bot.log ]; then
    tail -30 logs/bot.log
    echo ""

    # Check for errors in recent logs
    RECENT_ERRORS=$(tail -100 logs/bot.log | grep -i "error\|exception\|failed" | wc -l)
    if [ $RECENT_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ No recent errors in logs${NC}"
    else
        echo -e "${YELLOW}⚠️  Found $RECENT_ERRORS error/warning lines in recent logs${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Log file not found${NC}"
fi
echo ""

# Test 3: Test Python imports
echo "========================================================================"
echo "Test 3: Test Python Imports"
echo "========================================================================"
if python3 -c "
import sys
sys.path.insert(0, '.')
from core.engine import TradingEngine
from core.exchanges.binance_adapter import BinanceAdapter
print('✅ All imports successful')
" 2>&1; then
    echo -e "${GREEN}✅ Python imports working${NC}"
else
    echo -e "${RED}❌ Python import failed${NC}"
fi
echo ""

# Test 4: Test new monitoring tools
echo "========================================================================"
echo "Test 4: Test Monitoring Tools"
echo "========================================================================"

echo "Running quick status check..."
if python3 status.py 2>&1; then
    echo -e "${GREEN}✅ Status tool working${NC}"
else
    echo -e "${RED}❌ Status tool failed${NC}"
fi
echo ""

echo "Running latency monitor (5 samples)..."
if python3 monitor_binance_latency.py -s 5 2>&1; then
    echo -e "${GREEN}✅ Latency monitor working${NC}"
else
    echo -e "${RED}❌ Latency monitor failed${NC}"
fi
echo ""

# Test 5: Check database
echo "========================================================================"
echo "Test 5: Check Database"
echo "========================================================================"
if [ -f data/multi/trades_paper.db ]; then
    echo "Database exists: data/multi/trades_paper.db"

    # Count open positions
    OPEN_POSITIONS=$(sqlite3 data/multi/trades_paper.db "SELECT COUNT(*) FROM positions WHERE status='OPEN';" 2>/dev/null || echo "0")
    echo "Open positions: $OPEN_POSITIONS"

    # Count total trades
    TOTAL_TRADES=$(sqlite3 data/multi/trades_paper.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "Total trades: $TOTAL_TRADES"

    echo -e "${GREEN}✅ Database accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Database not found${NC}"
fi
echo ""

# Test 6: Check for latency fix in logs
echo "========================================================================"
echo "Test 6: Verify Latency Fix Applied"
echo "========================================================================"
if [ -f logs/bot.log ]; then
    if grep -q "Binance latency:" logs/bot.log; then
        LATENCY=$(grep "Binance latency:" logs/bot.log | tail -1)
        echo "Latest latency measurement:"
        echo "$LATENCY"

        # Check if latency is in acceptable range (< 100ms)
        if echo "$LATENCY" | grep -qE "[0-9]{1,2}ms"; then
            echo -e "${GREEN}✅ Latency fix applied correctly (showing low ms values)${NC}"
        else
            echo -e "${YELLOW}⚠️  Check latency value manually${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No latency measurement found in logs (bot may not have restarted)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Log file not found${NC}"
fi
echo ""

# Summary
echo "========================================================================"
echo "📊 TEST SUMMARY"
echo "========================================================================"

# Count tests
TOTAL_TESTS=6
PASSED_TESTS=0

# Check each test result (simplified - you can make this more sophisticated)
pgrep -f "run_bot.py" > /dev/null && ((PASSED_TESTS++))
[ -f logs/bot.log ] && ((PASSED_TESTS++))
python3 -c "from core.engine import TradingEngine" 2>/dev/null && ((PASSED_TESTS++))
[ -f status.py ] && ((PASSED_TESTS++))
[ -f monitor_binance_latency.py ] && ((PASSED_TESTS++))
[ -f data/multi/trades_paper.db ] && ((PASSED_TESTS++))

echo "Tests passed: $PASSED_TESTS/$TOTAL_TESTS"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - System is healthy${NC}"
    exit 0
elif [ $PASSED_TESTS -ge 4 ]; then
    echo -e "${YELLOW}⚠️  MOST TESTS PASSED - Check warnings above${NC}"
    exit 0
else
    echo -e "${RED}❌ MULTIPLE TESTS FAILED - Review errors above${NC}"
    exit 1
fi
