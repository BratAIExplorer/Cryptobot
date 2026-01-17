#!/bin/bash
# Quick bot status check

echo "🔍 Checking bot status..."
echo ""

# Check if running
RUNNING=$(ps aux | grep "python3 -u run_bot.py" | grep -v grep | wc -l)

if [ $RUNNING -gt 0 ]; then
    echo "✅ Bot is RUNNING"
    ps aux | grep "python3 -u run_bot.py" | grep -v grep
else
    echo "❌ Bot is NOT running"
    echo ""
    echo "📋 Last 30 lines of log:"
    echo "=================================================="
    tail -30 bot.log
fi
