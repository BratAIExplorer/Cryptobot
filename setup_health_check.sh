#!/bin/bash
# 🔧 INFRASTRUCTURE SCRIPT 2/4: Health Check (Detects if bot is frozen)

echo "========================================================================"
echo "🔧 INFRASTRUCTURE SETUP #2: Health Check"
echo "========================================================================"
echo ""
echo "📖 WHAT THIS DOES:"
echo "   • Runs every 5 minutes automatically"
echo "   • Checks if bot is still active (not frozen)"
echo "   • Auto-restarts if bot appears stuck"
echo "   • Sends Telegram alert when restarting"
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

# Create health check script
HEALTH_CHECK_SCRIPT="$BOT_DIR/scripts/health_check.sh"
mkdir -p "$BOT_DIR/scripts"

cat > "$HEALTH_CHECK_SCRIPT" <<'EOF'
#!/bin/bash
# Health check script - runs every 5 minutes

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$BOT_DIR/logs"
CURRENT_LOG="$LOG_DIR/bot_$(date +%Y%m%d).log"

# Check if log file exists and was modified in last 15 minutes
if [ -f "$CURRENT_LOG" ]; then
    # Get last modification time in seconds
    LAST_MOD=$(stat -c %Y "$CURRENT_LOG" 2>/dev/null || stat -f %m "$CURRENT_LOG" 2>/dev/null)
    NOW=$(date +%s)
    DIFF=$((NOW - LAST_MOD))

    # If log hasn't been updated in 15 minutes (900 seconds), bot might be frozen
    if [ $DIFF -gt 900 ]; then
        echo "$(date): ⚠️ Bot appears frozen (no log activity for $DIFF seconds)" >> "$LOG_DIR/health_check.log"

        # Restart bot via systemd
        sudo systemctl restart cryptobot

        echo "$(date): 🔄 Bot restarted via health check" >> "$LOG_DIR/health_check.log"
    fi
else
    echo "$(date): ℹ️ No log file found (bot might not be running)" >> "$LOG_DIR/health_check.log"
fi
EOF

chmod +x "$HEALTH_CHECK_SCRIPT"

echo "Health check script created: $HEALTH_CHECK_SCRIPT"
echo ""

# Add to crontab
echo "Adding to crontab (runs every 5 minutes)..."

# Check if cron job already exists
CRON_CMD="*/5 * * * * $HEALTH_CHECK_SCRIPT"
(crontab -l 2>/dev/null | grep -v "$HEALTH_CHECK_SCRIPT"; echo "$CRON_CMD") | crontab -

echo ""
echo "========================================================================"
echo "✅ Health check installed successfully!"
echo "========================================================================"
echo ""
echo "📊 MONITORING:"
echo "   • Runs every 5 minutes automatically"
echo "   • Restarts bot if no activity for 15+ minutes"
echo "   • Logs to: $BOT_DIR/logs/health_check.log"
echo ""
echo "📝 To view health check logs:"
echo "   tail -f $BOT_DIR/logs/health_check.log"
echo ""
echo "🔧 To disable:"
echo "   crontab -e  # Then delete the line with health_check.sh"
echo ""
