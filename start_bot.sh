#!/bin/bash

# ==========================================
# 🚀 CryptoBot V2.1 Deployment Script
# ==========================================

echo "=========================================="
echo "    🚀 STARTING DEPLOYMENT (V2.1)"
echo "=========================================="

# 1. Pull Latest Code
echo "📥 1. Pulling latest code from git..."
git pull origin main

# 2. Update Dependencies
echo "📦 2. Checking dependencies..."
pip install -r requirements.txt

# 3. Secure Permissions
echo "🔒 3. Securing secrets..."
chmod 600 .env
chmod 700 start_bot.sh

# 4. Database Backup & Migration
echo "💾 4. Running Pre-Start Backup & Migration..."
python3 migrate_confluence_v2.py
python3 scripts/auto_backup.py &
BACKUP_PID=$!
echo "   -> Backup Service Started (PID: $BACKUP_PID)"

# 5. Start Dashboard (Background)
echo "📊 5. Starting Dashboard..."
pm2 delete dashboard 2>/dev/null
pm2 start "streamlit run dashboard/app.py --server.port 8501" --name dashboard
echo "   -> Dashboard running on :8501"

# 6. Start Trading Bot (Background)
echo "🤖 6. Starting Trading Bot..."
pm2 delete crypto_bot 2>/dev/null
pm2 start run_bot.py --name crypto_bot --interpreter python3
echo "   -> Bot Service running"

# 7. Verification
echo "✅ 7. Assessing Status..."
pm2 save
pm2 list

echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETE! "
echo "   -> Dashboard: http://$(curl -s ifconfig.me):8501"
echo "   -> Password:  admin123"
echo "=========================================="
