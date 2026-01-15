#!/bin/bash
# VPS Deployment Script - Critical Fix Deployment
# Run this ON VPS: /root/cryptobot_v3
# Date: 2026-01-15

set -e  # Exit on error

echo "================================"
echo "VPS DEPLOYMENT - CRITICAL FIX"
echo "================================"
echo ""

# Step 1: Kill old bots
echo "1. Stopping old bot processes..."
if pgrep -f "run_bot.py" > /dev/null; then
    pkill -f run_bot.py
    echo "   ✅ Killed old bot processes"
    sleep 2
else
    echo "   ℹ️  No running bots found"
fi

# Step 2: Verify we're in correct directory
if [ "$PWD" != "/root/cryptobot_v3" ]; then
    echo "   ⚠️  Wrong directory! Changing to /root/cryptobot_v3"
    cd /root/cryptobot_v3
fi
echo "   ✅ Current directory: $PWD"

# Step 3: Pull latest code
echo ""
echo "2. Pulling latest code with adapter fix..."
git fetch origin
git pull origin claude/check-dashboard-status-VNa0U
echo "   ✅ Code updated"

# Step 4: Verify adapter fix is present
echo ""
echo "3. Verifying adapter fix..."
if grep -q "get_balance('USDT')" core/engine.py && grep -q "get_current_price" core/engine.py; then
    echo "   ✅ Adapter fix verified in core/engine.py"
else
    echo "   ❌ ERROR: Adapter fix NOT found!"
    echo "   Expected: get_balance('USDT') and get_current_price()"
    exit 1
fi

# Step 5: Test Binance connectivity & latency
echo ""
echo "4. Testing Binance connectivity..."
python3 -c "
import time
import sys
sys.path.insert(0, '/root/cryptobot_v3')
from exchanges.binance_adapter import BinanceAdapter

adapter = BinanceAdapter(mode='paper')
start = time.time()
try:
    price = adapter.get_current_price('BTC/USDT')
    latency = (time.time() - start) * 1000
    print(f'   ✅ Binance connected - BTC: \${price:,.2f}')
    print(f'   ⏱️  Latency: {latency:.0f}ms', end='')

    if latency < 500:
        print(' (GOOD)')
    elif latency < 1000:
        print(' (OK)')
    elif latency < 2000:
        print(' (SLOW)')
    else:
        print(' (CRITICAL - TOO SLOW!)')
        print('   ⚠️  WARNING: Latency >2s may cause trading issues')
except Exception as e:
    print(f'   ❌ ERROR: {e}')
    exit(1)
"

# Step 6: Check ping to Binance
echo ""
echo "5. Checking network latency..."
ping -c 3 api.binance.com | tail -1

# Step 7: Restart bot
echo ""
echo "6. Starting bot in paper mode..."
nohup python3 run_bot.py > bot.log 2>&1 &
BOT_PID=$!
echo "   ✅ Bot started (PID: $BOT_PID)"
sleep 3

# Step 8: Verify bot is running
echo ""
echo "7. Verifying bot status..."
if ps -p $BOT_PID > /dev/null; then
    echo "   ✅ Bot is running"
else
    echo "   ❌ ERROR: Bot failed to start!"
    echo "   Check logs: tail -50 bot.log"
    exit 1
fi

# Step 9: Show initial log
echo ""
echo "8. Initial log output:"
echo "---"
tail -20 bot.log
echo "---"

echo ""
echo "================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Monitor log: tail -f bot.log"
echo "  2. Check after 2 hours: python3 analyze_trades.py"
echo "  3. Check after 6 hours: python3 analyze_trades.py"
echo "  4. After 48h: Make GO/NO-GO decision"
echo ""
echo "Watch for:"
echo "  - No 'fetch_balance' errors"
echo "  - Grid orders placing successfully"
echo "  - Buy-the-Dip monitoring active"
echo ""
