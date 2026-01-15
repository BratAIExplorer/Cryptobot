#!/bin/bash
# Bot Status Checker - Run this on VPS at /root/cryptobot_v3
# Shows comprehensive bot activity and status
# Date: 2026-01-15

set -e

echo "================================"
echo "🤖 CRYPTOBOT V3 STATUS CHECK"
echo "================================"
echo ""
echo "📍 Location: $(pwd)"
echo "⏰ Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# ========================================
# 1. BOT PROCESS STATUS
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  BOT PROCESS STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if pgrep -f "run_bot.py" > /dev/null; then
    BOT_PID=$(pgrep -f "run_bot.py")
    BOT_UPTIME=$(ps -p $BOT_PID -o etime= | tr -d ' ')
    echo "✅ Bot is RUNNING"
    echo "   PID: $BOT_PID"
    echo "   Uptime: $BOT_UPTIME"
    echo "   Command: $(ps -p $BOT_PID -o cmd= | head -c 80)"
else
    echo "❌ Bot is NOT RUNNING"
    echo ""
    echo "To start bot:"
    echo "   cd /root/cryptobot_v3"
    echo "   nohup python3 run_bot.py > bot.log 2>&1 &"
    exit 1
fi
echo ""

# ========================================
# 2. RECENT LOG OUTPUT (Last 50 lines)
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  RECENT BOT LOG (Last 50 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f bot.log ]; then
    echo "📄 Log file: bot.log"
    echo "📊 Size: $(du -h bot.log | cut -f1)"
    echo ""
    echo "--- START LOG ---"
    tail -50 bot.log
    echo "--- END LOG ---"
else
    echo "⚠️  No bot.log found!"
fi
echo ""

# ========================================
# 3. ACTIVE STRATEGIES
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  ACTIVE STRATEGIES (from run_bot.py)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f run_bot.py ]; then
    echo "Searching for add_bot() calls..."
    grep -A 3 "engine.add_bot" run_bot.py | grep -E "name|type|symbols|initial_balance" | head -20
else
    echo "⚠️  run_bot.py not found!"
fi
echo ""

# ========================================
# 4. DATABASE STATUS
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  DATABASE STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DB_PATH="data/trades_paper.db"
if [ -f "$DB_PATH" ]; then
    echo "✅ Database exists: $DB_PATH"
    echo "📊 Size: $(du -h $DB_PATH | cut -f1)"
    echo "📅 Modified: $(stat -c %y $DB_PATH | cut -d. -f1)"
    echo ""

    # Count trades
    TRADE_COUNT=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "📈 Total trades: $TRADE_COUNT"

    if [ "$TRADE_COUNT" -gt 0 ]; then
        echo ""
        echo "Last 5 trades:"
        sqlite3 -header -column $DB_PATH "SELECT timestamp, strategy, symbol, side, price, amount FROM trades ORDER BY timestamp DESC LIMIT 5;" 2>/dev/null || echo "Error reading trades"
    else
        echo "   (No trades yet - bot just started)"
    fi
else
    echo "⚠️  Database not found: $DB_PATH"
    echo "   (Normal if bot just started - will be created on first trade)"
fi
echo ""

# ========================================
# 5. BINANCE CONNECTIVITY TEST
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  BINANCE CONNECTIVITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing connection to Binance API..."

# Quick ping test
PING_RESULT=$(ping -c 3 api.binance.com 2>&1 | tail -1 || echo "Ping failed")
echo "🌐 Network Ping: $PING_RESULT"

# Python CCXT test
echo ""
echo "🐍 Python CCXT Test:"
python3 -c "
import sys
sys.path.insert(0, '/root/cryptobot_v3')
import time
try:
    from core.exchanges.binance_adapter import BinanceAdapter
    adapter = BinanceAdapter(mode='paper')
    start = time.time()
    price = adapter.get_current_price('BTC/USDT')
    latency = (time.time() - start) * 1000
    print(f'   ✅ BTC/USDT: \${price:,.2f}')
    print(f'   ⏱️  Latency: {latency:.0f}ms', end='')
    if latency < 500:
        print(' (GOOD)')
    elif latency < 1000:
        print(' (OK)')
    elif latency < 2000:
        print(' (SLOW)')
    else:
        print(' (CRITICAL)')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)
" 2>&1
echo ""

# ========================================
# 6. SYSTEM RESOURCES
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  SYSTEM RESOURCES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💻 CPU & Memory:"
if [ -n "$BOT_PID" ]; then
    ps -p $BOT_PID -o %cpu,%mem,rss | tail -1 | awk '{printf "   CPU: %s%%  Memory: %s%% (%s KB)\n", $1, $2, $3}'
fi
echo ""
echo "💾 Disk Space:"
df -h . | tail -1 | awk '{printf "   Used: %s / %s (%s used)\n", $3, $2, $5}'
echo ""

# ========================================
# 7. LIVE LOG MONITORING (Last 20 lines updating)
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  LIVE LOG (Last 20 lines - Updates every 5s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop watching..."
echo ""
sleep 2

# Watch log for 30 seconds (6 updates)
for i in {1..6}; do
    clear
    echo "================================"
    echo "🤖 LIVE BOT LOG (Update $i/6)"
    echo "================================"
    echo "⏰ $(date '+%H:%M:%S')"
    echo ""
    if [ -f bot.log ]; then
        tail -20 bot.log
    else
        echo "⚠️  No bot.log found"
    fi
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Press Ctrl+C to stop watching..."
    echo "Next update in 5 seconds..."

    if [ $i -lt 6 ]; then
        sleep 5
    fi
done

echo ""
echo "================================"
echo "✅ STATUS CHECK COMPLETE"
echo "================================"
echo ""
echo "📊 Next Steps:"
echo "   1. Monitor log: tail -f bot.log"
echo "   2. Check trades after 4-6 hours: python3 analyze_trades.py"
echo "   3. Dashboard: http://<VPS_IP>:8501"
echo ""
