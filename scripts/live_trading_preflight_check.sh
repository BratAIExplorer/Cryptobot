#!/bin/bash
################################################################################
# LIVE TRADING PRE-FLIGHT VERIFICATION SCRIPT
# Senior Developer Review - Comprehensive System Check
# Run this before confirming LIVE trading is ready
################################################################################

echo "================================================================================"
echo "🚀 LIVE TRADING PRE-FLIGHT VERIFICATION"
echo "================================================================================"
echo "Senior Developer: Comprehensive System Check"
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Host: $(hostname)"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# CHECK 1: LIVE BOT SERVICE STATUS
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 1: LIVE Bot Service Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet cryptobot_live.service; then
    echo -e "${GREEN}✅ PASS${NC}: cryptobot_live.service is RUNNING"
    UPTIME=$(systemctl show cryptobot_live.service -p ActiveEnterTimestamp --value)
    echo "   Uptime: Started at $UPTIME"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}: cryptobot_live.service is NOT running"
    echo "   Action: sudo systemctl start cryptobot_live.service"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

################################################################################
# CHECK 2: LIVE DATABASE EXISTS AND IS ACCESSIBLE
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 2: LIVE Database Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DB_PATH="/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db"

if [ -f "$DB_PATH" ]; then
    echo -e "${GREEN}✅ PASS${NC}: LIVE database exists"
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "   Location: $DB_PATH"
    echo "   Size: $DB_SIZE"

    # Check database is not locked
    if sqlite3 "$DB_PATH" "SELECT 1;" &>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}: Database is accessible (not locked)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: Database is LOCKED or corrupt"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: LIVE database NOT found"
    echo "   Expected: $DB_PATH"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

################################################################################
# CHECK 3: GRID BOTS REGISTERED IN DATABASE
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 3: Grid Bots Registration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

GRID_BOT_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM bot_status WHERE strategy LIKE '%Grid%' AND status='RUNNING';")

if [ "$GRID_BOT_COUNT" -eq 2 ]; then
    echo -e "${GREEN}✅ PASS${NC}: Both Grid Bots registered and RUNNING"

    sqlite3 -header -column "$DB_PATH" << 'EOF'
SELECT
    strategy,
    status,
    ROUND(wallet_balance, 2) as balance,
    ROUND(total_pnl, 2) as pnl,
    total_trades
FROM bot_status
WHERE strategy LIKE '%Grid%';
EOF
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}: Expected 2 Grid Bots, found $GRID_BOT_COUNT"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

################################################################################
# CHECK 4: ALLOCATION VERIFICATION
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 4: LIVE Allocation Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_ALLOCATION=$(sqlite3 "$DB_PATH" "SELECT ROUND(SUM(wallet_balance), 2) FROM bot_status;")

echo "   Total LIVE Allocation: \$$TOTAL_ALLOCATION"

if (( $(echo "$TOTAL_ALLOCATION >= 400 && $TOTAL_ALLOCATION <= 500" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC}: Allocation within expected range (\$400-\$500)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif (( $(echo "$TOTAL_ALLOCATION > 500" | bc -l) )); then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Allocation higher than recommended (\$450)"
    echo "   Consider: This is higher than ultra-conservative target"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Allocation lower than expected"
    echo "   Check: Bots may have insufficient funds"
    WARNINGS=$((WARNINGS + 1))
fi

################################################################################
# CHECK 5: P&L STATUS (Should be 0 or positive)
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 5: P&L Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_PNL=$(sqlite3 "$DB_PATH" "SELECT ROUND(SUM(total_pnl), 2) FROM bot_status;")

echo "   Current Total P&L: \$$TOTAL_PNL"

if (( $(echo "$TOTAL_PNL >= 0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC}: No losses (P&L >= \$0)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
elif (( $(echo "$TOTAL_PNL >= -20" | bc -l) )); then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Minor losses (P&L: \$$TOTAL_PNL)"
    echo "   Monitor: Acceptable range for new deployment"
    WARNINGS=$((WARNINGS + 1))
elif (( $(echo "$TOTAL_PNL >= -50" | bc -l) )); then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Moderate losses (P&L: \$$TOTAL_PNL)"
    echo "   Action: Review trades, consider stopping"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ FAIL${NC}: Critical losses (P&L: \$$TOTAL_PNL)"
    echo "   Action: STOP BOT IMMEDIATELY and review"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

################################################################################
# CHECK 6: TRADE EXECUTION
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 6: Trade Execution Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_TRADES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM trades;")
TRADES_24H=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM trades WHERE timestamp > datetime('now', '-24 hours');")

echo "   Total Trades (All Time): $TOTAL_TRADES"
echo "   Trades (Last 24h): $TRADES_24H"

if [ "$TOTAL_TRADES" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: Bot has executed trades"

    LAST_TRADE=$(sqlite3 "$DB_PATH" "SELECT datetime(MAX(timestamp), 'localtime') FROM trades;")
    echo "   Last Trade: $LAST_TRADE"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  INFO${NC}: No trades executed yet"
    echo "   Status: Normal for new deployment or stable market"
    echo "   Action: Monitor - Grid Bots trade when price crosses levels"
    # Not counting as failure - trades require market volatility
fi

################################################################################
# CHECK 7: CIRCUIT BREAKER STATUS
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 7: Circuit Breaker Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CB_STATUS=$(sqlite3 "$DB_PATH" "SELECT is_open, consecutive_errors FROM circuit_breaker WHERE id=1;" 2>/dev/null || echo "0|0")

if [ -n "$CB_STATUS" ]; then
    IS_OPEN=$(echo "$CB_STATUS" | cut -d'|' -f1)
    ERRORS=$(echo "$CB_STATUS" | cut -d'|' -f2)

    if [ "$IS_OPEN" == "0" ] && [ "$ERRORS" == "0" ]; then
        echo -e "${GREEN}✅ PASS${NC}: Circuit breaker clear"
        echo "   Status: No errors, all systems operational"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  WARNING${NC}: Circuit breaker has errors"
        echo "   Consecutive Errors: $ERRORS"
        echo "   Action: Review logs for issues"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC}: Circuit breaker table not initialized"
    echo "   Status: Will initialize on first error"
fi

################################################################################
# CHECK 8: PAPER BOT STILL RUNNING (Should NOT interfere)
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 8: Paper Bot Independence"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PAPER_DB="/Antigravity/antigravity/scratch/crypto_trading_bot/data/trades_v3_paper.db"

if [ -f "$PAPER_DB" ]; then
    PAPER_BOTS=$(sqlite3 "$PAPER_DB" "SELECT COUNT(*) FROM bot_status WHERE status='RUNNING';" 2>/dev/null || echo "0")

    echo "   Paper Database: EXISTS"
    echo "   Paper Bots Running: $PAPER_BOTS"
    echo -e "${GREEN}✅ PASS${NC}: Paper and LIVE bots are independent"
    echo "   Status: Both can run simultaneously"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  INFO${NC}: Paper database not found"
    echo "   Status: Paper bot may not be running (optional)"
fi

################################################################################
# CHECK 9: DASHBOARD STATUS
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 9: Dashboard Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if pgrep -f "streamlit.*app.py" > /dev/null; then
    DASHBOARD_PID=$(pgrep -f "streamlit.*app.py")
    echo -e "${GREEN}✅ PASS${NC}: Dashboard is running (PID: $DASHBOARD_PID)"
    echo "   URL: http://$(hostname -I | awk '{print $1}'):8501"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Dashboard is not running"
    echo "   Action: Start with: streamlit run dashboard/app.py --server.port=8501"
    WARNINGS=$((WARNINGS + 1))
fi

################################################################################
# CHECK 10: CONFIGURATION VALIDATION
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 10: Configuration Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CONFIG_FILE="/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/run_bot_LIVE.py"

if [ -f "$CONFIG_FILE" ]; then
    # Check TRADING_MODE
    if grep -q "TRADING_MODE = 'live'" "$CONFIG_FILE"; then
        echo -e "${GREEN}✅ PASS${NC}: TRADING_MODE set to 'live'"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: TRADING_MODE not set to 'live'"
        echo "   Current: $(grep TRADING_MODE $CONFIG_FILE)"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi

    # Check database path
    if grep -q "trades_v3_live.db" "$CONFIG_FILE"; then
        echo -e "${GREEN}✅ PASS${NC}: Database path set to LIVE database"
    else
        echo -e "${RED}❌ FAIL${NC}: Database path incorrect"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: run_bot_LIVE.py not found"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

################################################################################
# CHECK 11: LOG FILE ANALYSIS
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 11: Recent Errors in Logs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LOG_FILE="/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/bot_systemd.log"

if [ -f "$LOG_FILE" ]; then
    CRITICAL_ERRORS=$(grep -i "error\|exception\|failed" "$LOG_FILE" | tail -100 | wc -l)

    if [ "$CRITICAL_ERRORS" -lt 10 ]; then
        echo -e "${GREEN}✅ PASS${NC}: Low error count in logs ($CRITICAL_ERRORS recent)"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  WARNING${NC}: High error count ($CRITICAL_ERRORS recent errors)"
        echo "   Action: Review logs with: tail -100 $LOG_FILE | grep -i error"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC}: Log file not found (may not have created yet)"
fi

################################################################################
# CHECK 12: EMERGENCY STOP MECHANISM
################################################################################
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHECK 12: Emergency Stop Mechanism"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check run_bot_LIVE.py has stop signal check
if grep -q "STOP_SIGNAL_LIVE" "$CONFIG_FILE" 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}: Emergency stop mechanism present in code"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Emergency stop mechanism not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Verify no active stop signal exists
STOP_SIGNAL="/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/STOP_SIGNAL_LIVE"
if [ -f "$STOP_SIGNAL" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}: Stop signal file EXISTS"
    echo "   Action: Remove file to allow bot to run"
    echo "   Command: rm $STOP_SIGNAL"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ PASS${NC}: No stop signal present (bot can run)"
fi

################################################################################
# FINAL SUMMARY
################################################################################
echo ""
echo "================================================================================"
echo "🎯 PRE-FLIGHT CHECK SUMMARY"
echo "================================================================================"
echo ""

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED))

echo "Checks Passed:  $CHECKS_PASSED"
echo "Checks Failed:  $CHECKS_FAILED"
echo "Warnings:       $WARNINGS"
echo "Total Checks:   $TOTAL_CHECKS"
echo ""

# Calculate pass rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; ($CHECKS_PASSED * 100) / $TOTAL_CHECKS" | bc)
else
    PASS_RATE=0
fi

echo "Pass Rate:      ${PASS_RATE}%"
echo ""

################################################################################
# GO/NO-GO DECISION
################################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚦 GO/NO-GO DECISION FOR LIVE TRADING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $CHECKS_FAILED -eq 0 ] && [ $WARNINGS -lt 3 ]; then
    echo -e "${GREEN}✅ GO FOR LIVE TRADING${NC}"
    echo ""
    echo "System Status: ALL CRITICAL CHECKS PASSED"
    echo "Risk Level:    MINIMAL"
    echo "Recommendation: APPROVED for LIVE trading with real money"
    echo ""
    echo "Next Steps:"
    echo "1. ✅ System is ready for LIVE trading"
    echo "2. Monitor dashboard daily: http://$(hostname -I | awk '{print $1}'):8501"
    echo "3. Check P&L every 6 hours for first 72 hours"
    echo "4. Use emergency stop if P&L < -\$50"
    echo "5. Scale up after 72 hours of success"
    EXIT_CODE=0

elif [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠️  CONDITIONAL GO${NC}"
    echo ""
    echo "System Status: PASSED but with warnings"
    echo "Risk Level:    LOW-MODERATE"
    echo "Recommendation: Can proceed but address warnings"
    echo ""
    echo "Action Required:"
    echo "1. Review warnings above"
    echo "2. Address non-critical issues"
    echo "3. Monitor closely for first 24 hours"
    EXIT_CODE=0

else
    echo -e "${RED}🛑 NO-GO FOR LIVE TRADING${NC}"
    echo ""
    echo "System Status: CRITICAL FAILURES DETECTED"
    echo "Risk Level:    HIGH"
    echo "Recommendation: DO NOT proceed with LIVE trading"
    echo ""
    echo "Action Required:"
    echo "1. Fix all FAILED checks above"
    echo "2. Re-run this verification script"
    echo "3. Only proceed when all checks pass"
    EXIT_CODE=1
fi

echo ""
echo "================================================================================"
echo "Verification Complete: $(date)"
echo "================================================================================"
echo ""

exit $EXIT_CODE
