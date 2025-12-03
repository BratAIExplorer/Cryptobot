#!/bin/bash
# One-Time VPS Setup Script
# This clones the repo from GitHub and sets up the environment

echo "==========================================="
echo "🔧 Initial VPS Setup from GitHub"
echo "==========================================="

# Backup existing installation
if [ -d "/Antigravity/antigravity/scratch/crypto_trading_bot" ]; then
    echo "📦 Backing up existing installation..."
    BACKUP_NAME="crypto_trading_bot_backup_$(date +%Y%m%d_%H%M%S)"
    sudo mv /Antigravity/antigravity/scratch/crypto_trading_bot /Antigravity/antigravity/scratch/$BACKUP_NAME
    echo "✅ Backup created: $BACKUP_NAME"
fi

# Clone from GitHub
echo ""
echo "📥 Cloning from GitHub..."
cd /Antigravity/antigravity/scratch/ || exit 1
git clone https://github.com/BratAIExplorer/Cryptobot.git crypto_trading_bot

# Find the most recent backup
LATEST_BACKUP=$(ls -dt /Antigravity/antigravity/scratch/crypto_trading_bot_backup_* 2>/dev/null | head -n 1)

if [ -n "$LATEST_BACKUP" ]; then
    echo ""
    echo "🔄 Restoring critical files from backup..."
    
    # Restore database
    if [ -f "$LATEST_BACKUP/data/trades.db" ]; then
        sudo cp "$LATEST_BACKUP/data/trades.db" crypto_trading_bot/data/
        echo "✅ Database restored"
    fi
    
    # Restore .env file
    if [ -f "$LATEST_BACKUP/.env" ]; then
        sudo cp "$LATEST_BACKUP/.env" crypto_trading_bot/
        echo "✅ Environment variables restored"
    fi
else
    echo "⚠️ No backup found. You will need to set up .env manually."
fi

# Set permissions
echo ""
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):$(whoami) crypto_trading_bot/
sudo chmod +x crypto_trading_bot/scripts/*.sh

# Restart services
echo ""
echo "🔄 Restarting services..."
sudo systemctl restart crypto_bot_runner.service
sudo systemctl restart crypto_bot.service
sudo systemctl restart portfolio_monitor.service

# Check status
echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
sleep 2
python3 crypto_trading_bot/scripts/check_status.py

echo ""
echo "📌 Next Steps:"
echo "   1. If .env was not restored, copy it manually"
echo "   2. Check that all bots are running above"
echo "   3. Use scripts/deploy.sh for future updates"
