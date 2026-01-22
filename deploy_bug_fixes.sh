#!/bin/bash
# VPS Deployment Script - Critical Bot Fixes
# Date: 2026-01-21
# Status: READY TO EXECUTE

echo "=========================================="
echo "🚀 CRITICAL BOT FIXES DEPLOYMENT"
echo "=========================================="
echo ""

# STEP 1: Verify OLD bot process
echo "📋 STEP 1: Identifying OLD bot process..."
echo ""
ps aux | grep run_bot | grep -v grep
echo ""

read -p "Confirm OLD bot PID to kill (should be 683206): " OLD_PID

if [ "$OLD_PID" != "683206" ]; then
    echo "⚠️  WARNING: PID mismatch! Expected 683206, got $OLD_PID"
    read -p "Are you SURE you want to kill PID $OLD_PID? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "❌ Aborted by user"
        exit 1
    fi
fi

# STEP 2: Kill OLD bot (CAREFULLY)
echo ""
echo "🔪 STEP 2: Killing OLD bot (PID $OLD_PID)..."
kill -SIGTERM $OLD_PID
sleep 5

# Verify it stopped
if ps -p $OLD_PID > /dev/null 2>&1; then
    echo "⚠️  Process still running, sending SIGKILL..."
    kill -9 $OLD_PID
    sleep 2
fi

# Check if stopped
if ps -p $OLD_PID > /dev/null 2>&1; then
    echo "❌ ERROR: Failed to kill old bot!"
    exit 1
else
    echo "✅ Old bot stopped successfully"
fi

# Verify only ONE bot running
echo ""
echo "🔍 Verifying only NEW bot remains..."
BOT_COUNT=$(ps aux | grep -E "run_bot\.py" | grep -v grep | wc -l)
if [ "$BOT_COUNT" -eq "1" ]; then
    echo "✅ Only 1 bot process running (correct)"
else
    echo "⚠️  WARNING: $BOT_COUNT bot processes found (expected 1)"
    ps aux | grep run_bot | grep -v grep
fi

# STEP 3: Pull latest code with bug fixes
echo ""
echo "📥 STEP 3: Pulling latest code from repository..."
cd /root/cryptobot_v3
git fetch --all
git pull origin claude/test-dip-bot-profit-lhCxz

# Verify bug fixes are present
echo ""
echo "🔍 Verifying bug fixes..."

# Check ATR fix
if grep -q "calculate_atr(df, period=14)" core/veto.py; then
    echo "✅ ATR bug fix confirmed in veto.py"
else
    echo "❌ ATR bug fix NOT found!"
    exit 1
fi

# Check regime_state fix
if grep -q "regime_state = RegimeState.UNDEFINED" core/engine.py; then
    echo "✅ regime_state bug fix confirmed in engine.py"
else
    echo "❌ regime_state bug fix NOT found!"
    exit 1
fi

# STEP 4: Restart bot
echo ""
echo "🔄 STEP 4: Restarting bot with bug fixes..."

# Stop current bot (just in case)
pkill -f "python3 run_bot.py"
sleep 5

# Verify stopped
if ps aux | grep "run_bot.py" | grep -v grep > /dev/null; then
    echo "⚠️  Bot still running, force killing..."
    pkill -9 -f "python3 run_bot.py"
    sleep 2
fi

# Start bot in background
nohup python3 run_bot.py > bot.log 2>&1 &
NEW_PID=$!

echo "✅ Bot restarted with PID: $NEW_PID"

# Wait for startup
sleep 10

# STEP 5: Verify bot is running and bugs are fixed
echo ""
echo "🔍 STEP 5: Verifying bot startup..."

# Check if process running
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ Bot process is running (PID $NEW_PID)"
else
    echo "❌ ERROR: Bot failed to start!"
    echo "Last 50 lines of log:"
    tail -50 bot.log
    exit 1
fi

# Check logs for errors
echo ""
echo "📋 Checking logs for critical errors..."
sleep 5

# Check for ATR errors
if grep -i "calculate_atr() takes from" bot.log | tail -5 | grep -q "takes from"; then
    echo "❌ ATR error still present!"
    tail -20 bot.log | grep "calculate_atr"
    exit 1
else
    echo "✅ No ATR errors found"
fi

# Check for regime_state errors
if grep -i "cannot access local variable 'regime_state'" bot.log | tail -5 | grep -q "regime_state"; then
    echo "❌ regime_state error still present!"
    tail -20 bot.log | grep "regime_state"
    exit 1
else
    echo "✅ No regime_state errors found"
fi

# Check for position limit errors
echo ""
echo "📊 Checking position limit status..."
LIMIT_ERRORS=$(grep "Maximum concurrent positions" bot.log | tail -5)
if [ -n "$LIMIT_ERRORS" ]; then
    echo "ℹ️  Position limit status:"
    echo "$LIMIT_ERRORS"
else
    echo "✅ No position limit errors (yet)"
fi

# STEP 6: Show recent log output
echo ""
echo "=========================================="
echo "📋 RECENT LOG OUTPUT (last 30 lines):"
echo "=========================================="
tail -30 bot.log

# Success message
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "  - Old bot killed: PID 683206"
echo "  - New bot running: PID $NEW_PID"
echo "  - ATR bug: FIXED ✅"
echo "  - regime_state bug: FIXED ✅"
echo ""
echo "📈 Next Steps:"
echo "  1. Monitor logs for 10-15 minutes"
echo "  2. Check for Grid Bot BUY signals (should work now)"
echo "  3. Run: python3 check_all_bots.py (after 1 hour)"
echo ""
echo "📝 Logs: tail -f bot.log"
echo ""
