#!/bin/bash
# Watch for first trade with Confluence=50 settings
# This script monitors logs for high-confluence signals

VPS_USER="root"
VPS_IP="72.60.40.29"
LOG_PATH="~/cryptobot_v3/logs/bot_engine.log"

echo "🔍 Watching for first trade with Confluence >= 50..."
echo "Press Ctrl+C to stop"
echo ""

# Watch log file and filter for important events
ssh ${VPS_USER}@${VPS_IP} "tail -f ${LOG_PATH} | grep --line-buffered -E 'Confluence|TRADE|Dip Detected|Entry Signal'"
