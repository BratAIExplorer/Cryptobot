#!/bin/bash
# Live Bot Monitoring Script - Confluence 50 Edition
# Shows real-time trade activity and signal evaluation

VPS_USER="root"
VPS_IP="72.60.40.29"
DB_PATH="~/cryptobot_v3/data/multi/trades_paper.db"
LOG_PATH="~/cryptobot_v3/logs/bot_engine.log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 LIVE BOT MONITOR - Confluence=50 (Optimized)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Check if bot is running
echo "🤖 Bot Process Status:"
ssh ${VPS_USER}@${VPS_IP} "pgrep -f 'run_bot.py' && echo '✅ RUNNING' || echo '❌ NOT RUNNING'"
echo ""

# 2. Last 10 log lines (shows recent dip detections and confluence scores)
echo "📜 Recent Activity (Last 10 Lines):"
ssh ${VPS_USER}@${VPS_IP} "tail -10 ${LOG_PATH}"
echo ""

# 3. Trades in last hour
echo "📊 Trades (Last Hour):"
ssh ${VPS_USER}@${VPS_IP} "sqlite3 -header -column ${DB_PATH} \"SELECT timestamp, strategy, symbol, side, price, pnl FROM trades WHERE timestamp >= datetime('now', '-1 hours') ORDER BY timestamp DESC LIMIT 10;\" 2>/dev/null || echo 'No trades yet'"
echo ""

# 4. Current open positions
echo "💼 Open Positions:"
ssh ${VPS_USER}@${VPS_IP} "sqlite3 -header -column ${DB_PATH} \"SELECT strategy, symbol, entry_price, current_price, unrealized_pnl, hold_time_hours FROM positions WHERE status='open' ORDER BY entry_time DESC;\" 2>/dev/null || echo 'No open positions'"
echo ""

# 5. Performance summary (all time)
echo "🎯 All-Time Performance:"
ssh ${VPS_USER}@${VPS_IP} "sqlite3 -header -column ${DB_PATH} \"SELECT COUNT(*) as total_trades, SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins, ROUND(SUM(pnl), 2) as total_pnl FROM trades;\" 2>/dev/null || echo 'No trades yet'"
echo ""

# 6. Bot health status
echo "💚 Bot Health:"
ssh ${VPS_USER}@${VPS_IP} "sqlite3 -header -column ${DB_PATH} \"SELECT strategy, status, ROUND(wallet_balance, 2) as balance, last_heartbeat FROM bot_status ORDER BY last_heartbeat DESC;\" 2>/dev/null || echo 'Status unavailable'"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Monitoring complete. Run with 'watch -n 60' for auto-refresh."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
