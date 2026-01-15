#!/bin/bash
# Bot Diagnostics - Find out why bot isn't initializing
# Run on VPS at /root/cryptobot_v3
# Date: 2026-01-15

echo "================================"
echo "🔍 BOT DIAGNOSTICS"
echo "================================"
echo ""

cd /root/cryptobot_v3

# 1. Check bot process
echo "1️⃣  Bot Process Status:"
if pgrep -f "run_bot.py" > /dev/null; then
    BOT_PID=$(pgrep -f "run_bot.py")
    echo "   ✅ Running (PID: $BOT_PID)"
    echo "   Uptime: $(ps -p $BOT_PID -o etime= | tr -d ' ')"
else
    echo "   ❌ NOT RUNNING"
fi
echo ""

# 2. Check log file size
echo "2️⃣  Log File Status:"
if [ -f bot.log ]; then
    SIZE=$(wc -c < bot.log)
    LINES=$(wc -l < bot.log)
    echo "   Size: $SIZE bytes"
    echo "   Lines: $LINES"
    echo ""

    if [ $LINES -lt 10 ]; then
        echo "   ⚠️  WARNING: Only $LINES lines - bot may be stuck!"
    fi
else
    echo "   ❌ No bot.log file!"
fi
echo ""

# 3. Show FULL log (not just last 50)
echo "3️⃣  FULL Bot Log:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f bot.log ]; then
    cat bot.log
else
    echo "   No log file found"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Check for Python errors
echo "4️⃣  Check for Python errors:"
if [ -f bot.log ]; then
    if grep -i "error\|exception\|traceback" bot.log > /dev/null; then
        echo "   ⚠️  ERRORS FOUND:"
        grep -i "error\|exception\|traceback" bot.log
    else
        echo "   ✅ No obvious errors in log"
    fi
else
    echo "   ❌ No log file to check"
fi
echo ""

# 5. Try to run bot in foreground to see errors
echo "5️⃣  Test Run (Foreground - 5 seconds):"
echo "   Killing background bot if running..."
pkill -f run_bot.py 2>/dev/null || true
sleep 2

echo ""
echo "   Starting bot in foreground..."
echo "   (Press Ctrl+C after 5 seconds if it hangs)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

timeout 10 python3 run_bot.py 2>&1 || {
    EXIT_CODE=$?
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    if [ $EXIT_CODE -eq 124 ]; then
        echo "   ⚠️  Bot timed out after 10 seconds"
        echo "      This might mean:"
        echo "      - Bot is waiting for user input"
        echo "      - Bot is stuck in initialization"
        echo "      - Bot is running an infinite loop without output"
    else
        echo "   ❌ Bot exited with code: $EXIT_CODE"
    fi
}

echo ""
echo "================================"
echo "6️⃣  RECOMMENDATIONS"
echo "================================"
echo ""

# Check if run_bot.py exists
if [ ! -f run_bot.py ]; then
    echo "❌ CRITICAL: run_bot.py not found!"
    echo "   Check if you're in correct directory: /root/cryptobot_v3"
    exit 1
fi

# Check Python version
echo "Python version: $(python3 --version)"
echo ""

# Check critical imports
echo "Testing critical imports..."
python3 -c "
import sys
sys.path.insert(0, '/root/cryptobot_v3')
try:
    from core.engine import TradingEngine
    print('   ✅ TradingEngine imports OK')
except Exception as e:
    print(f'   ❌ TradingEngine import failed: {e}')

try:
    from core.exchanges.binance_adapter import BinanceAdapter
    print('   ✅ BinanceAdapter imports OK')
except Exception as e:
    print(f'   ❌ BinanceAdapter import failed: {e}')

try:
    import ccxt
    print(f'   ✅ CCXT version: {ccxt.__version__}')
except Exception as e:
    print(f'   ❌ CCXT import failed: {e}')
" 2>&1

echo ""
echo "================================"
echo "✅ DIAGNOSTICS COMPLETE"
echo "================================"
echo ""
