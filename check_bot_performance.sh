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
echo "3️⃣  POSITIONS BY SYMBOL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as total,
    SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END) as open,
    SUM(CASE WHEN status='CLOSED' THEN 1 ELSE 0 END) as closed
FROM positions
GROUP BY symbol;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  PROFIT/LOSS SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as closed_trades,
    ROUND(SUM(profit), 2) as total_profit_usd,
    ROUND(AVG(profit), 2) as avg_profit_usd,
    ROUND(MIN(profit), 2) as worst_trade,
    ROUND(MAX(profit), 2) as best_trade
FROM positions
WHERE status='CLOSED'
GROUP BY symbol;
EOF
echo ""

sqlite3 "$DB" <<EOF
SELECT 'Overall Total P&L: $' || ROUND(SUM(profit), 2) FROM positions WHERE status='CLOSED';
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  WIN RATE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as total_closed,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) || '%' as win_rate
FROM positions
WHERE status='CLOSED'
GROUP BY symbol;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  RECENT POSITIONS (Last 10)"
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
    ROUND(profit, 2) as profit
FROM positions
ORDER BY buy_timestamp DESC
LIMIT 10;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  POSITIONS IN LAST 24 HOURS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    COUNT(*) as positions_24h,
    ROUND(SUM(buy_price * amount), 2) as total_invested_24h
FROM positions
WHERE datetime(buy_timestamp) > datetime('now', '-24 hours')
GROUP BY symbol;
EOF
echo ""

sqlite3 "$DB" <<EOF
SELECT 'Total Positions (24h): ' || COUNT(*) FROM positions WHERE datetime(buy_timestamp) > datetime('now', '-24 hours');
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  TRADES EXECUTED (Last 24 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    symbol,
    side,
    COUNT(*) as count,
    ROUND(AVG(price), 2) as avg_price
FROM trades
WHERE datetime(timestamp) > datetime('now', '-24 hours')
GROUP BY symbol, side;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  BOT STATUS"
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

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟  OPEN POSITIONS DETAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    id,
    symbol,
    strategy,
    ROUND(buy_price, 2) as buy_price,
    ROUND(amount, 6) as amount,
    datetime(buy_timestamp) as opened_at,
    ROUND((julianday('now') - julianday(buy_timestamp)) * 24, 1) || 'h' as age
FROM positions
WHERE status='OPEN'
ORDER BY buy_timestamp DESC;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣1️⃣  HOURLY ACTIVITY (Last 24 Hours)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    strftime('%Y-%m-%d %H:00', buy_timestamp) as hour,
    COUNT(*) as positions_created
FROM positions
WHERE datetime(buy_timestamp) > datetime('now', '-24 hours')
GROUP BY strftime('%Y-%m-%d %H:00', buy_timestamp)
ORDER BY hour DESC;
EOF
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣2️⃣  EXCHANGE VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sqlite3 "$DB" <<EOF
.mode column
.headers on
SELECT
    exchange,
    COUNT(*) as positions
FROM positions
GROUP BY exchange;
EOF
echo ""

echo "========================================="
echo "✅ Performance Check Complete"
echo "========================================="
echo ""
echo "Test Started: 2026-01-11 08:54 UTC"
echo "Current Time: $(date -u)"
echo ""
echo "Expected Results (after 48 hours):"
echo "  - Total Positions: 10-20"
echo "  - Closed Trades: 5-10"
echo "  - Win Rate: 80%+"
echo "  - Total P&L: +\$5 to +\$20"
echo ""
