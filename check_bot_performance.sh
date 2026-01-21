#!/bin/bash
# Bot Performance Check Script
# Run on VPS: bash check_bot_performance.sh

echo "========================================="
echo "🤖 BOT PERFORMANCE CHECK (Last 24 Hours)"
echo "========================================="
echo ""
echo "Database: data/test_adapter_binance_paper.db"
echo "Date: $(date)"
echo ""

DB="data/test_adapter_binance_paper.db"

# Check if database exists
if [ ! -f "$DB" ]; then
    echo "❌ Database not found at $DB"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  POSITION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    status,
    COUNT(*) as count,
    ROUND(AVG(buy_price), 2) as avg_buy_price,
    ROUND(SUM(buy_price * amount), 2) as total_value_usd
FROM positions
GROUP BY symbol, status
ORDER BY symbol, status;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  TOTAL POSITIONS (All Time)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
SELECT 'Total Positions Created: ' || COUNT(*) FROM positions;
SELECT 'Open Positions: ' || COUNT(*) FROM positions WHERE status='OPEN';
SELECT 'Closed Positions: ' || COUNT(*) FROM positions WHERE status='CLOSED';
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  PROFIT/LOSS SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as closed_trades,
    ROUND(SUM(unrealized_pnl_usd), 2) as total_profit_usd,
    ROUND(AVG(unrealized_pnl_usd), 2) as avg_profit_usd,
    ROUND(MIN(unrealized_pnl_usd), 2) as worst_trade,
    ROUND(MAX(unrealized_pnl_usd), 2) as best_trade
FROM positions
WHERE status='CLOSED'
GROUP BY symbol;
EOF
echo ""

sqlite3 "$DB" <<EOF
SELECT 'Overall Total P&L: $' || ROUND(SUM(unrealized_pnl_usd), 2) FROM positions WHERE status='CLOSED';
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  WIN RATE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as total_closed,
    SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) || '%' as win_rate
FROM positions
WHERE status='CLOSED'
GROUP BY symbol;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  RECENT POSITIONS (Last 10)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    id,
    symbol,
    status,
    ROUND(buy_price, 2) as buy_price,
    ROUND(amount, 4) as amount,
    datetime(buy_timestamp) as bought_at,
    ROUND(unrealized_pnl_usd, 2) as pnl
FROM positions
ORDER BY buy_timestamp DESC
LIMIT 10;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  BOT STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    name,
    status,
    total_trades,
    ROUND(total_pnl, 2) as pnl_usd,
    ROUND(wallet_balance, 2) as balance_usd,
    datetime(last_updated) as last_update
FROM bots;
EOF
echo ""

echo "========================================="
echo "✅ Performance Check Complete"
echo "========================================="
