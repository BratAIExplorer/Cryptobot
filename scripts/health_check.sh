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
