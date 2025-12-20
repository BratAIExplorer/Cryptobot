#!/bin/bash
# Deploy Luno Monitor Fixes to VPS
# Run this from your LOCAL machine (Windows Git Bash or WSL)

VPS_HOST="root@srv1010193"
VPS_PATH="/root/luno-monitor"

echo "🚀 Deploying Luno Monitor fixes to VPS..."
echo ""

# Copy changed files
echo "📤 Copying config.py..."
scp config.py ${VPS_HOST}:${VPS_PATH}/

echo "📤 Copying currency_converter.py..."
scp src/currency_converter.py ${VPS_HOST}:${VPS_PATH}/src/

echo "📤 Copying price_monitor.py..."
scp src/price_monitor.py ${VPS_HOST}:${VPS_PATH}/src/

echo "📤 Copying portfolio_analyzer.py..."
scp src/portfolio_analyzer.py ${VPS_HOST}:${VPS_PATH}/src/

echo "📤 Copying alert_state_manager.py..."
scp alert_state_manager.py ${VPS_HOST}:${VPS_PATH}/

echo "📤 Copying main.py..."
scp main.py ${VPS_HOST}:${VPS_PATH}/

echo ""
echo "✅ Files deployed!"
echo ""
echo "Next steps on VPS:"
echo "1. Stop the bot: pkill -f 'luno-monitor/main.py'"
echo "2. Delete old alert state: rm /root/luno-monitor/alert_state.json"
echo "3. Restart the bot: cd /root/luno-monitor && python3 main.py"
