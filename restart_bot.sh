#!/bin/bash
# Restart Trading Bot Script
# Usage: bash restart_bot.sh

echo "=================================================="
echo "🔄 RESTARTING CRYPTO TRADING BOT (V2 - WITH FIXES)"
echo "=================================================="
echo ""

# Step 1: Stop existing bot processes
echo "1️⃣  Stopping existing bot processes..."
pkill -f "python3 -u run_bot.py"
pkill -f "python.*run_bot"
sleep 3

# Verify stopped
RUNNING=$(ps aux | grep "run_bot" | grep -v grep | grep -v "restart_bot" | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "⚠️  Some processes still running. Force killing..."
    pkill -9 -f "run_bot"
    sleep 2
fi

echo "   ✅ All bot processes stopped"
echo ""

# Step 2: Pull latest code
echo "2️⃣  Pulling latest code from Git..."
git pull origin claude/review-handover-bot-performance-Rwv92

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi

echo "   ✅ Code updated"
echo ""

# Step 3: Start bot
echo "3️⃣  Starting bot in background..."
nohup python3 -u run_bot.py > bot.log 2>&1 &
BOT_PID=$!

echo "   ✅ Bot started (PID: $BOT_PID)"
echo ""

# Step 4: Wait and show initial logs
echo "4️⃣  Waiting 3 seconds for initialization..."
sleep 3
echo ""

echo "📊 INITIAL LOG OUTPUT:"
echo "=================================================="
tail -20 bot.log
echo "=================================================="
echo ""

# Step 5: Verify running
RUNNING=$(ps aux | grep "run_bot.py" | grep -v grep | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "✅ Bot is running!"
    echo ""
    echo "📋 Next Steps:"
    echo "   • Monitor logs:  tail -f bot.log"
    echo "   • Check status:  python3 check_all_bots.py"
    echo "   • Run diagnostic: python3 diagnose_bots_simple.py"
    echo ""
    echo "🎯 EXPECTED BEHAVIOR:"
    echo "   • XRP, ADA, DOGE should buy within 5-10 minutes"
    echo "   • Grid Bot ETH should trigger (already in buy zone)"
    echo "   • Grid Bot BTC should start catching $256 moves"
    echo ""
else
    echo "❌ Bot failed to start!"
    echo "Check bot.log for errors:"
    tail -50 bot.log
    exit 1
fi
