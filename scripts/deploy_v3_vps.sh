#!/bin/bash
# ==========================================
# 🚀 CryptoBot V3 VPS Deployment Script
# ==========================================
# 1. Backs up legacy bot
# 2. Creates new V3 directory
# 3. Copies files
# 4. Sets up Environment
# ==========================================

APP_DIR="cryptobot_v3"
LEGACY_DIR="crypto_bot"
BACKUP_DIR="crypto_bot_backup_legacy_$(date +%Y%m%d)"

echo "🚀 Starting Deployment..."

# 1. Backup Legacy
if [ -d "$LEGACY_DIR" ]; then
    echo "📦 Backing up legacy bot to $BACKUP_DIR..."
    cp -r "$LEGACY_DIR" "$BACKUP_DIR"
    echo "✅ Backup Complete."
else
    echo "ℹ️  No legacy bot found at $LEGACY_DIR. Skipping backup."
fi

# 2. Create V3 Directory
echo "📂 Creating $APP_DIR..."
mkdir -p "$APP_DIR"

# 3. Copy Files (Assuming script runs from parent or we copy manually)
# Ideally, you rsync from local. This script assumes it's running ON VPS and files are in 'current' or 'temp' dir.
# For this script, we assume user uploaded files to 'upload_temp' or we are untaring.
# ...
# BUT simpler: User should run this command:
# rsync -avz --exclude 'venv' --exclude 'data' --exclude '.git' ./ user@vps:~/cryptobot_v3/

echo "✅ Directory Ready: ~/$APP_DIR"
echo "👉 Action Required: Upload your local code to ~/$APP_DIR"
echo "   Example: rsync -avz --exclude 'venv' --exclude 'data' ./ user@vps:~/$APP_DIR/"

# 4. Setup
echo "🛠️  Setting up Environment..."
cd "$APP_DIR" || exit

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtualenv created"
fi

source venv/bin/activate
pip install -r requirements.txt
echo "✅ Dependencies Installed"

# 5. Deployment Info
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT PREPPED"
echo "=========================================="
echo "1. Code:     ~/$APP_DIR"
echo "2. Config:   BINANCE Only"
echo "3. Bots:"
echo "   - Grid Bot BTC ($250)"
echo "   - Grid Bot ETH ($250)"
echo "   - Dip Bot Top10 ($1000)"
echo ""
echo "👉 To Start:"
echo "   cd ~/$APP_DIR"
echo "   source venv/bin/activate"
echo "   python run_bot.py --mode live" # User to change to live manually
echo "=========================================="
