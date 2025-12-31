#!/bin/bash
# 🔧 INFRASTRUCTURE SCRIPT 4/4: Monitoring Dashboard

echo "========================================================================"
echo "🔧 INFRASTRUCTURE SETUP #4: Monitoring Dashboard"
echo "========================================================================"
echo ""
echo "📖 WHAT THIS DOES:"
echo "   • Creates simple monitoring commands"
echo "   • Shows live bot status, trades, P&L"
echo "   • Easy to check from terminal"
echo ""
echo "⏱️  Time needed: 1 minute"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create monitoring script
MONITOR_SCRIPT="$BOT_DIR/scripts/monitor.sh"
mkdir -p "$BOT_DIR/scripts"

cat > "$MONITOR_SCRIPT" <<'EOF'
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
EOF

chmod +x "$MONITOR_SCRIPT"

# Create convenient aliases
ALIAS_FILE="$BOT_DIR/scripts/aliases.sh"

cat > "$ALIAS_FILE" <<EOF
# Add these to your ~/.bashrc for quick access:

alias bot-status='sudo systemctl status cryptobot'
alias bot-start='sudo systemctl start cryptobot'
alias bot-stop='sudo systemctl stop cryptobot'
alias bot-restart='sudo systemctl restart cryptobot'
alias bot-logs='tail -f $BOT_DIR/logs/bot_*.log'
alias bot-monitor='$MONITOR_SCRIPT'
alias bot-watch='watch -n 60 $MONITOR_SCRIPT'
EOF

echo ""
echo "========================================================================"
echo "✅ Monitoring dashboard installed successfully!"
echo "========================================================================"
echo ""
echo "📊 TO USE:"
echo "   $MONITOR_SCRIPT              # Run once"
echo "   watch -n 60 $MONITOR_SCRIPT  # Auto-refresh every 60 seconds"
echo ""
echo "🎯 CONVENIENT ALIASES (optional):"
echo "   Add to your ~/.bashrc:"
echo "   source $ALIAS_FILE"
echo ""
echo "   Then you can use:"
echo "   bot-status    # Check status"
echo "   bot-start     # Start bot"
echo "   bot-stop      # Stop bot"
echo "   bot-logs      # View live logs"
echo "   bot-monitor   # Show dashboard"
echo ""
