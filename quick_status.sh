#!/bin/bash
# Quick Bot Status - Run on VPS at /root/cryptobot_v3
# Shows essential bot info in 10 seconds
# Date: 2026-01-15

echo "🤖 QUICK BOT STATUS CHECK"
echo "========================="
echo ""

# Bot running?
if pgrep -f "run_bot.py" > /dev/null; then
    BOT_PID=$(pgrep -f "run_bot.py")
    BOT_UPTIME=$(ps -p $BOT_PID -o etime= | tr -d ' ')
    echo "✅ Bot is RUNNING (PID: $BOT_PID, Uptime: $BOT_UPTIME)"
else
    echo "❌ Bot is NOT RUNNING"
    exit 1
fi

# Database?
if [ -f data/trades_paper.db ]; then
    TRADE_COUNT=$(sqlite3 data/trades_paper.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "✅ Database exists ($TRADE_COUNT trades)"
else
    echo "⚠️  No database yet (will be created on first trade)"
fi

# Recent log
echo ""
echo "📄 LAST 10 LOG LINES:"
echo "---"
if [ -f bot.log ]; then
    tail -10 bot.log
else
    echo "No bot.log found"
fi
echo ""

# Binance test
echo "🌐 Testing Binance..."
python3 -c "
import sys
sys.path.insert(0, '/root/cryptobot_v3')
import time
from core.exchanges.binance_adapter import BinanceAdapter
adapter = BinanceAdapter(mode='paper')
start = time.time()
price = adapter.get_current_price('BTC/USDT')
latency = (time.time() - start) * 1000
print(f'✅ BTC: \${price:,.2f} (Latency: {latency:.0f}ms)')
" 2>&1

echo ""
echo "========================="
echo "Monitor live: tail -f bot.log"
