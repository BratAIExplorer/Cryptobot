#!/bin/bash
#
# Grid Bot Diagnostic Collection Script
# Run this on your VPS and share the output for analysis
#
# Usage: bash collect_grid_bot_diagnostics.sh > grid_bot_report.txt
#

echo "================================================================================"
echo "🔍 GRID BOT COMPREHENSIVE DIAGNOSTIC REPORT"
echo "================================================================================"
echo "Generated: $(date)"
echo "Hostname: $(hostname)"
echo ""

# Navigate to bot directory
cd /Antigravity/antigravity/scratch/crypto_trading_bot 2>/dev/null || {
    echo "❌ ERROR: Cannot access /Antigravity/antigravity/scratch/crypto_trading_bot"
    echo "Current directory: $(pwd)"
    exit 1
}

echo "Working Directory: $(pwd)"
echo ""

# ============================================================================
# 1. SERVICE STATUS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 1: SERVICE STATUS"
echo "================================================================================"
echo ""

echo "--- Paper Trading Service ---"
systemctl is-active cryptobot 2>/dev/null || systemctl is-active cryptobot_paper 2>/dev/null || echo "Service not found"
echo ""

echo "--- Process Check ---"
ps aux | grep -E "run_bot\.py|python.*crypto" | grep -v grep || echo "No bot processes found"
echo ""

# ============================================================================
# 2. DATABASE CONNECTIVITY
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 2: DATABASE CHECK"
echo "================================================================================"
echo ""

DB_PATH="data/trades_v3_paper.db"

if [ -f "$DB_PATH" ]; then
    echo "✅ Database found: $DB_PATH"
    echo "   Size: $(du -h $DB_PATH | cut -f1)"
    echo "   Modified: $(stat -c %y $DB_PATH 2>/dev/null || stat -f %Sm $DB_PATH 2>/dev/null)"
else
    echo "❌ Database not found: $DB_PATH"
    echo "Available databases:"
    find data/ -name "*.db" -type f 2>/dev/null || echo "  None found"
    exit 1
fi
echo ""

# ============================================================================
# 3. BOT STATUS TABLE
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 3: REGISTERED BOTS"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    strategy,
    status,
    total_trades,
    ROUND(total_pnl, 2) as total_pnl,
    ROUND(wallet_balance, 2) as wallet,
    last_heartbeat
FROM bot_status
ORDER BY strategy;
EOF

BOT_COUNT=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM bot_status WHERE strategy LIKE '%Grid%';")
echo ""
echo "Grid Bots Registered: $BOT_COUNT"
echo ""

# ============================================================================
# 4. GRID BOT TRADES - LAST 24 HOURS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 4: GRID BOT TRADES (LAST 24 HOURS)"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    strategy,
    COUNT(*) as trades_24h,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    ROUND(SUM(cost), 2) as volume_usd,
    MIN(timestamp) as first_trade,
    MAX(timestamp) as last_trade
FROM trades
WHERE strategy LIKE '%Grid%'
  AND timestamp > datetime('now', '-24 hours')
GROUP BY strategy;
EOF

TRADES_24H=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM trades WHERE strategy LIKE '%Grid%' AND timestamp > datetime('now', '-24 hours');")
echo ""
echo "Total Grid Bot Trades (24h): $TRADES_24H"
echo ""

# ============================================================================
# 5. GRID BOT TRADES - ALL TIME
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 5: GRID BOT TRADES (ALL TIME)"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    strategy,
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    ROUND(SUM(cost), 2) as total_volume,
    MIN(timestamp) as first_ever,
    MAX(timestamp) as last_trade
FROM trades
WHERE strategy LIKE '%Grid%'
GROUP BY strategy, symbol
ORDER BY total_trades DESC;
EOF

TRADES_ALL=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM trades WHERE strategy LIKE '%Grid%';")
echo ""
echo "Total Grid Bot Trades (All Time): $TRADES_ALL"
echo ""

# ============================================================================
# 6. LAST 10 TRADES
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 6: RECENT GRID BOT TRADES (LAST 10)"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    datetime(timestamp, 'localtime') as trade_time,
    strategy,
    symbol,
    side,
    ROUND(price, 2) as price,
    ROUND(amount, 6) as amount,
    ROUND(cost, 2) as cost_usd
FROM trades
WHERE strategy LIKE '%Grid%'
ORDER BY timestamp DESC
LIMIT 10;
EOF
echo ""

# ============================================================================
# 7. OPEN POSITIONS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 7: GRID BOT OPEN POSITIONS"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    symbol,
    strategy,
    ROUND(entry_price, 4) as entry,
    ROUND(current_price, 4) as current,
    ROUND(amount, 6) as amount,
    ROUND(unrealized_pnl_usd, 2) as pnl_usd,
    ROUND(unrealized_pnl_pct, 2) as pnl_pct,
    datetime(entry_date, 'localtime') as opened
FROM positions
WHERE strategy LIKE '%Grid%'
  AND status = 'OPEN'
ORDER BY entry_date DESC;
EOF

OPEN_POS=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM positions WHERE strategy LIKE '%Grid%' AND status='OPEN';")
echo ""
echo "Open Grid Bot Positions: $OPEN_POS"
echo ""

# ============================================================================
# 8. CLOSED POSITIONS P&L
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 8: GRID BOT P&L SUMMARY"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    strategy,
    COUNT(*) as closed_positions,
    SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
    ROUND(SUM(unrealized_pnl_usd), 2) as total_pnl,
    ROUND(AVG(unrealized_pnl_usd), 2) as avg_pnl,
    ROUND(MAX(unrealized_pnl_usd), 2) as best_trade,
    ROUND(MIN(unrealized_pnl_usd), 2) as worst_trade
FROM positions
WHERE strategy LIKE '%Grid%'
  AND status = 'CLOSED'
GROUP BY strategy;
EOF
echo ""

# ============================================================================
# 9. CURRENT MARKET PRICES
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 9: CURRENT MARKET PRICES (for Grid Range Check)"
echo "================================================================================"
echo ""

echo "Getting current BTC/ETH prices from database recent trades..."
sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    symbol,
    ROUND(price, 2) as last_price,
    datetime(timestamp, 'localtime') as price_time
FROM trades
WHERE symbol IN ('BTC/USDT', 'ETH/USDT')
  AND timestamp = (
      SELECT MAX(timestamp)
      FROM trades t2
      WHERE t2.symbol = trades.symbol
  );
EOF
echo ""

# ============================================================================
# 10. CIRCUIT BREAKER STATUS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 10: CIRCUIT BREAKER STATUS"
echo "================================================================================"
echo ""

sqlite3 -header -column $DB_PATH << 'EOF'
SELECT
    is_open,
    consecutive_errors,
    total_trips,
    datetime(last_error_time, 'localtime') as last_error,
    last_error_message
FROM circuit_breaker
WHERE id = 1;
EOF
echo ""

# ============================================================================
# 11. RECENT LOG ERRORS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 11: RECENT LOG ERRORS (Last 20 lines with 'Grid' or 'error')"
echo "================================================================================"
echo ""

if [ -f "logs/bot_systemd.log" ]; then
    echo "--- Checking logs/bot_systemd.log ---"
    grep -i -E "grid|error" logs/bot_systemd.log | tail -20 || echo "No errors found"
else
    echo "Log file not found: logs/bot_systemd.log"
    echo "Available log files:"
    ls -la logs/ 2>/dev/null || echo "No logs directory"
fi
echo ""

# ============================================================================
# 12. RUN_BOT.PY CONFIGURATION CHECK
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 12: GRID BOT CONFIGURATION (from run_bot.py)"
echo "================================================================================"
echo ""

if [ -f "run_bot.py" ]; then
    echo "--- Grid Bot BTC Configuration ---"
    sed -n "/engine.add_bot({/,/^    })/p" run_bot.py | grep -A 20 "Grid Bot BTC" || echo "Not found"
    echo ""

    echo "--- Grid Bot ETH Configuration ---"
    sed -n "/engine.add_bot({/,/^    })/p" run_bot.py | grep -A 20 "Grid Bot ETH" || echo "Not found"
    echo ""
else
    echo "run_bot.py not found in current directory"
fi

# ============================================================================
# 13. SUMMARY & DIAGNOSTICS
# ============================================================================
echo "================================================================================"
echo "📊 SECTION 13: DIAGNOSTIC SUMMARY"
echo "================================================================================"
echo ""

# Calculate time since last trade
LAST_TRADE_TS=$(sqlite3 $DB_PATH "SELECT MAX(timestamp) FROM trades WHERE strategy LIKE '%Grid%';")

if [ -n "$LAST_TRADE_TS" ]; then
    echo "Last Grid Bot Trade: $LAST_TRADE_TS"

    # Try to calculate hours ago (works on both Linux and macOS)
    LAST_EPOCH=$(date -d "$LAST_TRADE_TS" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_TRADE_TS" +%s 2>/dev/null)
    NOW_EPOCH=$(date +%s)

    if [ -n "$LAST_EPOCH" ] && [ -n "$NOW_EPOCH" ]; then
        HOURS_AGO=$(( ($NOW_EPOCH - $LAST_EPOCH) / 3600 ))
        echo "Hours Since Last Trade: $HOURS_AGO hours"

        if [ $HOURS_AGO -gt 12 ]; then
            echo "⚠️  WARNING: No Grid Bot trades in $HOURS_AGO hours!"
        elif [ $HOURS_AGO -gt 6 ]; then
            echo "⚠️  NOTICE: No Grid Bot trades in $HOURS_AGO hours (monitor closely)"
        else
            echo "✅ Recent trading activity (within last 6 hours)"
        fi
    fi
else
    echo "❌ NO GRID BOT TRADES FOUND (EVER)"
fi

echo ""

# Summary stats
echo "--- Quick Stats ---"
echo "Total Grid Bot Trades (All Time): $TRADES_ALL"
echo "Grid Bot Trades (Last 24h): $TRADES_24H"
echo "Registered Grid Bots: $BOT_COUNT"
echo "Open Positions: $OPEN_POS"

echo ""
echo "================================================================================"
echo "📋 END OF DIAGNOSTIC REPORT"
echo "================================================================================"
echo ""
echo "Next Steps:"
echo "1. Save this output to a file: bash $0 > grid_bot_report.txt"
echo "2. Share grid_bot_report.txt with Claude for analysis"
echo "3. Claude will analyze:"
echo "   - Why trades stopped (if applicable)"
echo "   - Grid configuration issues"
echo "   - Performance vs expected benchmarks"
echo "   - Recommended fixes"
echo ""
