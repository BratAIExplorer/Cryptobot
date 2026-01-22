#!/bin/bash
################################################################################
# VPS Deployment Script
# Safely updates code and restarts bot
################################################################################

set -e  # Exit on error

echo "========================================================================"
echo "🚀 DEPLOYING CRYPTOBOT UPDATE"
echo "========================================================================"
echo ""

# Change to bot directory
cd ~/cryptobot_v3

# Step 1: Stop bot
echo "1️⃣  Stopping bot..."
if pgrep -f "run_bot.py" > /dev/null; then
    pkill -f "run_bot.py"
    echo "✅ Bot stopped"
    sleep 2
else
    echo "ℹ️  Bot was not running"
fi
echo ""

# Step 2: Backup data
echo "2️⃣  Backing up data..."
BACKUP_DIR="data_backup_$(date +%Y%m%d_%H%M%S)"
cp -r data/ $BACKUP_DIR
echo "✅ Data backed up to: $BACKUP_DIR"
echo ""

# Step 3: Pull latest code
echo "3️⃣  Pulling latest code..."
git fetch origin
git checkout claude/check-dashboard-status-VNa0U
git pull
echo "✅ Code updated"
echo ""

# Step 4: Test monitoring tools
echo "4️⃣  Testing new monitoring tools..."
echo ""
echo "📊 Quick Status Check:"
python3 status.py
echo ""

echo "📡 Latency Check (5 samples):"
python3 monitor_binance_latency.py -s 5
echo ""

# Step 5: Restart bot
echo "5️⃣  Restarting bot..."
nohup python3 run_bot.py > logs/bot.log 2>&1 &
sleep 3
echo "✅ Bot started"
echo ""

# Step 6: Verify bot is running
echo "6️⃣  Verifying bot status..."
if pgrep -f "run_bot.py" > /dev/null; then
    PID=$(pgrep -f "run_bot.py")
    echo "✅ Bot is running (PID: $PID)"
else
    echo "❌ ERROR: Bot failed to start"
    echo "Check logs: tail -100 logs/bot.log"
    exit 1
fi
echo ""

# Step 7: Show recent logs
echo "7️⃣  Recent bot logs (last 20 lines):"
echo "========================================================================"
tail -20 logs/bot.log
echo "========================================================================"
echo ""

# Success message
echo "========================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "========================================================================"
echo ""
echo "📌 Next Steps:"
echo "   1. Monitor logs: tail -f logs/bot.log"
echo "   2. Check status: python3 status.py"
echo "   3. Watch for 'Binance latency: ~2ms (Excellent)' in logs"
echo ""
echo "🔍 Monitoring Commands:"
echo "   Daily check:    python3 status.py"
echo "   Latency test:   python3 monitor_binance_latency.py"
echo "   Full check:     python3 check_live_readiness.py"
echo ""
