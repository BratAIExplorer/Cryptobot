#!/bin/bash
# 24-Hour Bot Performance Analysis
# Run this to evaluate if bot is ready for live trading

cd /Antigravity/antigravity/scratch/crypto_trading_bot

echo "========================================================================"
echo "🤖 BOT PERFORMANCE ANALYSIS - LAST 24 HOURS"
echo "========================================================================"
echo "Generated: $(date)"
echo ""

# ============================================================================
# 1. TOTAL TRADES BY STRATEGY
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 1. TRADE VOLUME (Last 24 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    ROUND(SUM(cost), 2) as total_volume_usd
FROM trades
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY strategy
ORDER BY total_trades DESC;
EOF

TOTAL_TRADES=$(sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) FROM trades WHERE timestamp > datetime('now', '-24 hours');")
echo ""
echo "   ✅ Total Trades (24h): $TOTAL_TRADES"
echo "   📌 Minimum Required: 10"
if [ $TOTAL_TRADES -ge 10 ]; then
    echo "   ✓ PASS"
else
    echo "   ✗ FAIL - Need more trading activity"
fi

# ============================================================================
# 2. OPEN POSITIONS
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💼 2. CURRENT OPEN POSITIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    symbol,
    ROUND(entry_price, 2) as entry_price,
    ROUND(current_price, 2) as current_price,
    ROUND(amount, 4) as amount,
    ROUND(unrealized_pnl_usd, 2) as unrealized_pnl,
    ROUND(unrealized_pnl_pct, 2) as pnl_pct,
    status,
    datetime(entry_date) as entry_time
FROM positions
WHERE status='OPEN'
ORDER BY unrealized_pnl_pct DESC;
EOF

OPEN_POSITIONS=$(sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) FROM positions WHERE status='OPEN';")
echo ""
echo "   📊 Open Positions: $OPEN_POSITIONS"

# ============================================================================
# 3. CLOSED POSITIONS P&L (Last 24 Hours)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💰 3. REALIZED P&L (Last 24 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    COUNT(*) as closed_positions,
    SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
    ROUND(SUM(unrealized_pnl_usd), 2) as total_pnl_usd,
    ROUND(AVG(unrealized_pnl_usd), 2) as avg_pnl_per_trade
FROM positions
WHERE status='CLOSED'
  AND updated_at > datetime('now', '-24 hours')
GROUP BY strategy
ORDER BY total_pnl_usd DESC;
EOF

NET_PNL=$(sqlite3 data/trades_v3_paper.db "SELECT ROUND(SUM(unrealized_pnl_usd), 2) FROM positions WHERE status='CLOSED' AND updated_at > datetime('now', '-24 hours');")
echo ""
echo "   💵 Net P&L (24h): \$$NET_PNL"
echo "   📌 Minimum Required: > \$0"
if (( $(echo "$NET_PNL > 0" | bc -l) )); then
    echo "   ✓ PASS - Bot is profitable"
else
    echo "   ✗ FAIL - Bot is losing money"
fi

# ============================================================================
# 4. WIN RATE ANALYSIS
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 4. WIN RATE ANALYSIS (All Time)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    COUNT(*) as total_closed,
    SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
    ROUND(MAX(unrealized_pnl_usd), 2) as best_trade,
    ROUND(MIN(unrealized_pnl_usd), 2) as worst_trade,
    ROUND(SUM(unrealized_pnl_usd), 2) as total_pnl
FROM positions
WHERE status='CLOSED'
GROUP BY strategy
HAVING COUNT(*) >= 5
ORDER BY win_rate_pct DESC;
EOF

# Check if any strategy has win rate > 60%
WIN_RATE_CHECK=$(sqlite3 data/trades_v3_paper.db "SELECT MAX(win_rate) FROM (SELECT ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate FROM positions WHERE status='CLOSED' GROUP BY strategy HAVING COUNT(*) >= 5);")

echo ""
echo "   🎯 Best Win Rate: ${WIN_RATE_CHECK}%"
echo "   📌 Minimum Required: 60%"
if (( $(echo "$WIN_RATE_CHECK >= 60" | bc -l) )); then
    echo "   ✓ PASS"
else
    echo "   ✗ FAIL - Win rate too low"
fi

# ============================================================================
# 5. CIRCUIT BREAKER STATUS
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 5. CIRCUIT BREAKER STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    id,
    is_open,
    consecutive_errors,
    datetime(last_error_time) as last_error,
    total_trips,
    last_error_message
FROM circuit_breaker;
EOF

CIRCUIT_BREAKER_ERRORS=$(sqlite3 data/trades_v3_paper.db "SELECT consecutive_errors FROM circuit_breaker WHERE id=1;")
echo ""
echo "   🔴 Current Errors: $CIRCUIT_BREAKER_ERRORS"
echo "   📌 Maximum Allowed: 0"
if [ "$CIRCUIT_BREAKER_ERRORS" -eq 0 ]; then
    echo "   ✓ PASS - No errors"
else
    echo "   ✗ FAIL - Circuit breaker active"
fi

# ============================================================================
# 6. ERROR COUNT (Last 24 Hours)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  6. ERROR ANALYSIS (Last 24 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count critical errors (excluding known harmless ones)
ERROR_COUNT=$(grep -i "error processing" logs/bot_systemd.log 2>/dev/null | \
              grep -v "CODEX\|HODL\|Failed to update.*NoneType" | \
              tail -1000 | wc -l)

echo "   Critical Errors (last 1000 lines): $ERROR_COUNT"
echo "   📌 Maximum Allowed: 10"

if [ $ERROR_COUNT -le 10 ]; then
    echo "   ✓ PASS"
else
    echo "   ✗ FAIL - Too many errors"
    echo ""
    echo "   Recent Errors:"
    grep -i "error processing" logs/bot_systemd.log | \
    grep -v "CODEX\|HODL\|Failed to update.*NoneType" | \
    tail -5
fi

# ============================================================================
# 7. BOT STATUS & BALANCES
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💼 7. CURRENT BALANCES & STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    status,
    total_trades,
    ROUND(total_pnl, 2) as total_pnl,
    ROUND(wallet_balance, 2) as balance,
    datetime(last_heartbeat) as last_active
FROM bot_status
ORDER BY wallet_balance DESC;
EOF

# ============================================================================
# 8. RECENT TRADE HISTORY
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📜 8. RECENT TRADES (Last 10)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    datetime(timestamp) as time,
    strategy,
    symbol,
    side,
    ROUND(price, 2) as price,
    ROUND(amount, 4) as amount,
    ROUND(cost, 2) as cost_usd,
    exchange
FROM trades
ORDER BY timestamp DESC
LIMIT 10;
EOF

# ============================================================================
# 9. SYSTEM HEALTH
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 9. SYSTEM HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check systemd status
if systemctl is-active --quiet cryptobot; then
    echo "   ✓ Bot Process: RUNNING"
else
    echo "   ✗ Bot Process: STOPPED"
fi

# Check process count
PROCESS_COUNT=$(ps aux | grep run_bot.py | grep -v grep | wc -l)
echo "   📊 Process Count: $PROCESS_COUNT"
if [ $PROCESS_COUNT -eq 1 ]; then
    echo "   ✓ PASS - Single process"
elif [ $PROCESS_COUNT -eq 0 ]; then
    echo "   ✗ FAIL - No process running"
else
    echo "   ⚠️  WARNING - Multiple processes ($PROCESS_COUNT)"
fi

# Check log file age
LAST_LOG_UPDATE=$(stat -c %Y logs/bot_systemd.log 2>/dev/null || echo 0)
NOW=$(date +%s)
LOG_AGE=$((NOW - LAST_LOG_UPDATE))

echo "   📝 Last Log Update: ${LOG_AGE}s ago"
if [ $LOG_AGE -lt 300 ]; then
    echo "   ✓ PASS - Bot actively logging"
else
    echo "   ⚠️  WARNING - No recent log activity"
fi

# ============================================================================
# FINAL GO/NO-GO DECISION
# ============================================================================
echo ""
echo "========================================================================"
echo "🚦 GO/NO-GO DECISION FOR LIVE TRADING"
echo "========================================================================"
echo ""

# Count passes
PASSES=0

# Check 1: Trades
if [ $TOTAL_TRADES -ge 10 ]; then
    echo "   ✓ Trade Volume: $TOTAL_TRADES trades (>= 10 required)"
    PASSES=$((PASSES + 1))
else
    echo "   ✗ Trade Volume: $TOTAL_TRADES trades (< 10 required)"
fi

# Check 2: Profitability
if (( $(echo "$NET_PNL > 0" | bc -l) )); then
    echo "   ✓ Profitability: \$$NET_PNL (> \$0 required)"
    PASSES=$((PASSES + 1))
else
    echo "   ✗ Profitability: \$$NET_PNL (must be > \$0)"
fi

# Check 3: Win Rate
if (( $(echo "$WIN_RATE_CHECK >= 60" | bc -l) )); then
    echo "   ✓ Win Rate: ${WIN_RATE_CHECK}% (>= 60% required)"
    PASSES=$((PASSES + 1))
else
    echo "   ✗ Win Rate: ${WIN_RATE_CHECK}% (< 60% required)"
fi

# Check 4: Circuit Breaker
if [ "$CIRCUIT_BREAKER_ERRORS" -eq 0 ]; then
    echo "   ✓ Circuit Breaker: Clear (0 errors)"
    PASSES=$((PASSES + 1))
else
    echo "   ✗ Circuit Breaker: $CIRCUIT_BREAKER_ERRORS errors"
fi

# Check 5: Error Count
if [ $ERROR_COUNT -le 10 ]; then
    echo "   ✓ Error Count: $ERROR_COUNT (< 10 allowed)"
    PASSES=$((PASSES + 1))
else
    echo "   ✗ Error Count: $ERROR_COUNT (> 10 threshold)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Score: $PASSES / 5 checks passed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $PASSES -eq 5 ]; then
    echo "   🟢 RECOMMENDATION: GO LIVE ✅"
    echo "   Bot meets all safety criteria for live trading."
    echo ""
    echo "   Next Steps:"
    echo "   1. Review LIVE_TRADING_TRANSITION_GUIDE.md"
    echo "   2. Set up separate Telegram alerts for live bot"
    echo "   3. Start with 10% of paper trading position sizes"
    echo "   4. Monitor closely for first 24-48 hours"
elif [ $PASSES -ge 3 ]; then
    echo "   🟡 RECOMMENDATION: CAUTION ⚠️"
    echo "   Bot shows promise but has some issues."
    echo ""
    echo "   Action Required:"
    echo "   1. Address failed checks above"
    echo "   2. Monitor for another 24-48 hours"
    echo "   3. Re-run this analysis"
else
    echo "   🔴 RECOMMENDATION: DO NOT GO LIVE ❌"
    echo "   Bot is not ready for live trading."
    echo ""
    echo "   Action Required:"
    echo "   1. Fix critical issues (failed checks above)"
    echo "   2. Continue paper trading for 72+ hours"
    echo "   3. Re-run this analysis daily"
fi

echo ""
echo "========================================================================"
echo "Analysis Complete: $(date)"
echo "========================================================================"
