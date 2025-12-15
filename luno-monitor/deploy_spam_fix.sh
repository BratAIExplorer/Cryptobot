#!/bin/bash
# Quick VPS update script for spam fix and target updates

echo "🔧 Deploying spam fix and target updates..."

VPS_USER="root"
VPS_HOST="srv1010193"
VPS_PATH="/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor"

# Upload fixed files
echo "📤 Uploading fixed files..."
scp c:/CryptoBot_Project/luno-monitor/config.py ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/config.py
scp c:/CryptoBot_Project/luno-monitor/main.py ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/main.py

# Restart services
echo "🔄 Restarting monitors..."
ssh ${VPS_USER}@${VPS_HOST} "
    systemctl restart portfolio_monitor.service
    sleep 3
    systemctl status portfolio_monitor.service --no-pager
"

echo "✅ Done! Check for 'Initialized X already-reached targets' in logs"
