#!/bin/bash
# Start Bot with Unbuffered Output - Run on VPS at /root/cryptobot_v3
# Ensures all log output is captured properly
# Date: 2026-01-16

set -e

cd /root/cryptobot_v3

echo "================================"
echo "🚀 STARTING CRYPTO BOT"
echo "================================"
echo ""

# 1. Kill any existing bot processes
echo "1️⃣  Checking for existing bot processes..."
if pgrep -f "run_bot.py" > /dev/null; then
    OLD_PID=$(pgrep -f "run_bot.py")
    echo "   Found existing bot (PID: $OLD_PID)"
    echo "   Killing..."
    pkill -f "run_bot.py"
    sleep 2
    echo "   ✅ Killed"
else
    echo "   No existing bots found"
fi
echo ""

# 2. Backup old log if it exists
echo "2️⃣  Managing log file..."
if [ -f bot.log ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mv bot.log "bot_${TIMESTAMP}.log"
    echo "   Backed up old log to: bot_${TIMESTAMP}.log"
else
    echo "   No existing log file"
fi
echo ""

# 3. Start bot with unbuffered Python output
echo "3️⃣  Starting bot with unbuffered output..."
echo "   Command: nohup python3 -u run_bot.py > bot.log 2>&1 &"
echo ""

nohup python3 -u run_bot.py > bot.log 2>&1 &
BOT_PID=$!

echo "   ✅ Bot started!"
echo "   PID: $BOT_PID"
echo ""

# 4. Wait 5 seconds and show first output
echo "4️⃣  Waiting 5 seconds for initialization..."
sleep 5
echo ""

# 5. Show recent log output
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 RECENT LOG OUTPUT (Last 30 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -30 bot.log
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6. Final status
echo "================================"
echo "✅ BOT STARTED SUCCESSFULLY"
echo "================================"
echo ""
echo "📊 Monitor Commands:"
echo "   tail -f bot.log              # Watch live log"
echo "   ps aux | grep run_bot        # Check process"
echo "   ./quick_status.sh            # Quick status"
echo "   python3 analyze_trades.py    # After 4-6 hours"
echo ""
echo "🛑 Stop Bot:"
echo "   pkill -f run_bot.py"
echo ""
