#!/bin/bash
# Quick Deployment Script
# Run this on VPS after pushing changes to GitHub

echo "================================"
echo "🚀 Deploying Crypto Bot Updates"
echo "================================"

# Navigate to project directory
cd /Antigravity/antigravity/scratch/crypto_trading_bot || exit 1

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart crypto_bot_runner.service
sudo systemctl restart crypto_bot.service
sudo systemctl restart portfolio_monitor.service

# Check status
echo ""
echo "✅ Deployment complete. Checking status..."
sleep 2
python3 scripts/check_status.py
