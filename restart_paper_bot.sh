#!/bin/bash
#
# Restart Binance Paper Trading Bot with Crash Veto Fix
#

echo "========================================================================"
echo "🔄 RESTARTING BINANCE PAPER TRADING BOT"
echo "========================================================================"

# 1. Stop existing bot
echo ""
echo "1️⃣  Stopping existing bot..."
if [ -f bot.pid ]; then
    OLD_PID=$(cat bot.pid)
    if ps -p $OLD_PID > /dev/null; then
        echo "   Sending stop signal to PID $OLD_PID..."
        kill $OLD_PID
        sleep 3

        # Force kill if still running
        if ps -p $OLD_PID > /dev/null; then
            echo "   Force killing..."
            kill -9 $OLD_PID
        fi
        echo "   ✅ Bot stopped"
    else
        echo "   Bot not running (PID $OLD_PID not found)"
    fi
else
    echo "   No PID file found, checking for process..."
    pkill -f "run_bot_binance_SAFE_PAPER.py" && echo "   ✅ Bot stopped" || echo "   No bot running"
fi

# 2. Pull latest fixes
echo ""
echo "2️⃣  Pulling latest fixes from git..."
git pull origin claude/bot-launch-checklist-SmLAH
if [ $? -eq 0 ]; then
    echo "   ✅ Code updated"
else
    echo "   ⚠️  Git pull failed, using existing code"
fi

# 3. Quick verification
echo ""
echo "3️⃣  Running pre-launch verification..."
python3 verify_binance_paper.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Verification failed! Fix errors before launching."
    exit 1
fi

# 4. Check for screen session
echo ""
echo "4️⃣  Checking for existing screen session..."
if screen -list | grep -q "binance-paper"; then
    echo "   Found existing session, killing it..."
    screen -S binance-paper -X quit
    sleep 1
fi

# 5. Launch in new screen session
echo ""
echo "5️⃣  Launching bot in screen session 'binance-paper'..."
screen -dmS binance-paper python3 run_bot_binance_SAFE_PAPER.py
sleep 2

# 6. Verify launch
echo ""
echo "6️⃣  Verifying bot is running..."
if screen -list | grep -q "binance-paper"; then
    echo "   ✅ Bot running in screen session"
    echo ""
    echo "========================================================================"
    echo "✅ BINANCE PAPER BOT RESTARTED SUCCESSFULLY"
    echo "========================================================================"
    echo ""
    echo "📊 Monitor bot:"
    echo "   screen -r binance-paper     # Attach to bot (Ctrl+A, D to detach)"
    echo "   tail -f logs/live_*.log     # View logs"
    echo "   cat bot.pid                 # Check PID"
    echo ""
    echo "🛑 Stop bot:"
    echo "   touch STOP_SIGNAL           # Graceful stop"
    echo "   screen -S binance-paper -X quit  # Force stop"
    echo ""
    echo "📝 Expected Changes:"
    echo "   ✅ No more crash warnings (disabled for paper mode)"
    echo "   ✅ No more CryptoPanic 404s (disabled for paper mode)"
    echo "   ✅ Trades should execute when grid conditions met"
    echo ""
    echo "========================================================================"
else
    echo "   ❌ Bot failed to start"
    echo "   Check for errors in screen session:"
    echo "   screen -r binance-paper"
    exit 1
fi
