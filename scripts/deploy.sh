#!/bin/bash
# Quick Deployment Script
# Usage: ./scripts/deploy.sh

echo "================================"
echo "🚀 Deploying Crypto Bot Updates"
echo "================================"

# 1. Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull

# 2. Run Database Migrations (Safety Check)
# This ensures we never miss a DB column update again!
if [ -f "migrate_add_rsi_columns.py" ]; then
    echo "🛠️ Checking for DB updates..."
    python3 migrate_add_rsi_columns.py
fi

# 3. Restart services
echo "🔄 Restarting services..."
sudo systemctl restart crypto_bot_runner.service
sudo systemctl restart crypto_bot.service
# sudo systemctl restart portfolio_monitor.service

# 4. Check status
echo ""
echo "✅ Deployment complete. Checking status..."
sleep 2
python3 scripts/check_status.py
