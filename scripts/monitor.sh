#!/bin/bash
# Quick monitoring dashboard

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$BOT_DIR/data/trades_v3_paper.db"

clear
echo "========================================================================"
echo "📊 CRYPTO BOT MONITORING DASHBOARD"
echo "========================================================================"
echo "Time: $(date)"
echo ""

# Check if bot is running
if pgrep -f "run_bot.py" > /dev/null; then
    echo "✅ Bot Status: RUNNING (PID: $(pgrep -f run_bot.py))"
else
    echo "❌ Bot Status: NOT RUNNING"
fi

# Check systemd status
if systemctl is-active --quiet cryptobot; then
    echo "✅ Systemd Service: ACTIVE"
else
    echo "⚠️  Systemd Service: INACTIVE"
fi

echo ""
echo "========================================================================"
echo "📈 PERFORMANCE (Today)"
echo "========================================================================"

if [ -f "$DB_FILE" ]; then
    sqlite3 "$DB_FILE" <<SQL
.mode column
.headers on
SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(SUM(profit), 2) as total_profit
FROM trades
WHERE date(entry_time) = date('now');
SQL

    echo ""
    echo "========================================================================"
    echo "📊 BY STRATEGY (All Time)"
    echo "========================================================================"

    sqlite3 "$DB_FILE" <<SQL
.mode column
.headers on
SELECT
    bot_name,
    COUNT(*) as trades,
    ROUND(SUM(profit), 2) as profit
FROM trades
WHERE exit_time IS NOT NULL
GROUP BY bot_name
ORDER BY profit DESC;
SQL

    echo ""
    echo "========================================================================"
    echo "🔓 OPEN POSITIONS"
    echo "========================================================================"

    sqlite3 "$DB_FILE" <<SQL
.mode column
.headers on
SELECT
    bot_name,
    symbol,
    ROUND(entry_price, 2) as entry,
    ROUND((SELECT close FROM (SELECT 1 as close)) - entry_price, 2) as unrealized_pnl,
    datetime(entry_time) as opened
FROM trades
WHERE exit_time IS NULL
LIMIT 10;
SQL

else
    echo "No database found. Bot hasn't traded yet."
fi

echo ""
echo "========================================================================"
echo "📝 RECENT LOG ENTRIES (Last 10)"
echo "========================================================================"
tail -10 "$BOT_DIR/logs/bot_$(date +%Y%m%d).log" 2>/dev/null || echo "No logs for today"

echo ""
echo "========================================================================"
echo "🔧 QUICK COMMANDS:"
echo "   sudo systemctl status cryptobot    # Detailed status"
echo "   tail -f logs/bot_*.log             # Live logs"
echo "   watch -n 60 '$MONITOR_SCRIPT'      # Auto-refresh every 60s"
echo "========================================================================"
