#!/bin/bash
# MEXC Live Trading Monitor - Quick Status Check
# Run this frequently: watch -n 300 ./monitor_mexc_live.sh  (every 5 min)

cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

echo "========================================================"
echo "🔴 MEXC LIVE BOT STATUS @ $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================"

# 1. Check if bot is running
echo ""
echo "1️⃣  BOT PROCESS:"
if pgrep -f "run_bot_mexc.*py" > /dev/null; then
    PID=$(pgrep -f "run_bot_mexc.*py")
    echo "   ✅ Bot is RUNNING (PID: $PID)"
    # Check how long it's been running
    ps -p $PID -o etime= | xargs echo "   ⏱️  Uptime:"
else
    echo "   ❌ Bot is NOT running!"
    echo "   🔍 Check logs: tail -50 logs/live_*.log"
fi

# 2. Check live balance
echo ""
echo "2️⃣  MEXC BALANCE:"
python3 << 'EOF' 2>/dev/null
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
try:
    m = ccxt.mexc({'apiKey': os.getenv('MEXC_API_KEY'), 'secret': os.getenv('MEXC_SECRET')})
    b = m.fetch_balance()
    usdt = b['USDT']['total']
    free = b['USDT']['free']
    used = b['USDT']['used']
    print(f"   Total: ${usdt:.2f} | Free: ${free:.2f} | In Orders: ${used:.2f}")
except Exception as e:
    print(f"   ❌ Cannot fetch balance: {e}")
EOF

# 3. Database quick stats
echo ""
echo "3️⃣  TRADE STATISTICS:"
if [ -f "data/trades_mexc_live.db" ]; then
    sqlite3 data/trades_mexc_live.db << 'SQL' 2>/dev/null
.mode column
SELECT
    COUNT(*) as 'Total Trades',
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as 'Buys',
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as 'Sells',
    ROUND(SUM(CASE WHEN side='SELL' THEN profit ELSE 0 END), 2) as 'Total P&L'
FROM trades;
SQL

    # Recent trades (last 5)
    echo ""
    echo "4️⃣  RECENT TRADES (Last 5):"
    sqlite3 data/trades_mexc_live.db << 'SQL' 2>/dev/null
.mode column
SELECT
    substr(timestamp, 12, 8) as 'Time',
    symbol,
    side,
    ROUND(price, 2) as 'Price',
    ROUND(amount, 4) as 'Amount'
FROM trades
ORDER BY timestamp DESC
LIMIT 5;
SQL
else
    echo "   ⚠️  Database not created yet (no trades)"
fi

# 5. Check for recent errors
echo ""
echo "5️⃣  RECENT ERRORS (Last 10 lines):"
if [ -f "logs/live_$(date +%Y%m%d).log" ]; then
    grep -i "error\|exception\|failed" logs/live_$(date +%Y%m%d).log 2>/dev/null | tail -3 || echo "   ✅ No errors found"
else
    echo "   ⚠️  No log file yet"
fi

# 6. Open positions
echo ""
echo "6️⃣  OPEN POSITIONS:"
if [ -f "data/trades_mexc_live.db" ]; then
    sqlite3 data/trades_mexc_live.db << 'SQL' 2>/dev/null
.mode column
SELECT
    bot_id as 'Bot',
    symbol,
    ROUND(entry_price, 2) as 'Entry',
    ROUND(current_price, 2) as 'Current',
    ROUND(unrealized_pnl_pct, 2) as 'P&L%',
    ROUND(unrealized_pnl_usd, 2) as 'P&L$'
FROM positions
WHERE status='OPEN'
LIMIT 10;
SQL

    OPEN_COUNT=$(sqlite3 data/trades_mexc_live.db "SELECT COUNT(*) FROM positions WHERE status='OPEN';" 2>/dev/null)
    if [ "$OPEN_COUNT" -eq 0 ]; then
        echo "   ℹ️  No open positions"
    fi
else
    echo "   ⚠️  Database not created yet"
fi

echo ""
echo "========================================================"
echo "✅ Status check complete"
echo "========================================================"
echo ""
echo "💡 TIP: Run 'tail -f logs/live_$(date +%Y%m%d).log' for live updates"
echo "🛑 STOP BOT: touch STOP_SIGNAL"
echo ""
