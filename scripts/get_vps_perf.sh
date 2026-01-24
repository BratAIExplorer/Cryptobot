#!/bin/bash
DB_PATH=~/cryptobot_v3/data/multi/trades_paper.db
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 BOT PERFORMANCE SUMMARY (Last 10 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "--- Trade Activity ---"
sqlite3 -header -column $DB_PATH "SELECT strategy, side, COUNT(*) as count, SUM(pnl) as realized_pnl FROM trades WHERE timestamp >= datetime('now', '-10 hours') GROUP BY strategy, side;" 2>/dev/null || \
sqlite3 -header -column $DB_PATH "SELECT strategy, side, COUNT(*) as count, SUM(cost) as total_cost FROM trades WHERE timestamp >= datetime('now', '-10 hours') GROUP BY strategy, side;"
echo ""
echo "--- Current Bot Status ---"
sqlite3 -header -column $DB_PATH "SELECT strategy, status, wallet_balance, last_heartbeat FROM bot_status;"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
