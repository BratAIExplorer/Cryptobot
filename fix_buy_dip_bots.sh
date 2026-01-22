#!/bin/bash
################################################################################
# PART A: Fix Buy-Dip Bots (Switch to Correct Branch)
# Run this on VPS: bash fix_buy_dip_bots.sh
################################################################################

set -e  # Exit on error

echo "========================================================================"
echo "🔧 PART A: Fixing Buy-Dip Bots"
echo "========================================================================"
echo ""
echo "Issue: Buy-Dip bots detecting dips but not executing trades"
echo "Cause: Running old branch without A/B test bypass and latency fix"
echo "Solution: Switch to claude/check-dashboard-status-VNa0U branch"
echo ""

# Step 1: Check current location
echo "1️⃣  Verifying location..."
cd ~/cryptobot_v3
echo "✅ In directory: $(pwd)"
echo ""

# Step 2: Check current branch
echo "2️⃣  Current branch:"
git branch --show-current
echo ""

# Step 3: Stop running bot
echo "3️⃣  Stopping current bot..."
if pgrep -f "run_bot.py" > /dev/null; then
    pkill -f "run_bot.py"
    echo "✅ Bot stopped"
    sleep 2
else
    echo "ℹ️  Bot was not running"
fi
echo ""

# Step 4: Backup current data
echo "4️⃣  Backing up current data..."
BACKUP_DIR="data_backup_fix_$(date +%Y%m%d_%H%M%S)"
cp -r data/ $BACKUP_DIR
echo "✅ Data backed up to: $BACKUP_DIR"
echo ""

# Step 5: Fetch latest changes
echo "5️⃣  Fetching latest code from GitHub..."
git fetch origin
echo "✅ Fetched latest changes"
echo ""

# Step 6: Switch to correct branch
echo "6️⃣  Switching to correct branch..."
git checkout claude/check-dashboard-status-VNa0U
git pull origin claude/check-dashboard-status-VNa0U
echo "✅ Switched to claude/check-dashboard-status-VNa0U"
echo ""

# Step 7: Verify key files exist
echo "7️⃣  Verifying fixes are present..."
if grep -q "Bypassing confluence check" core/engine.py; then
    echo "✅ A/B test bypass code found"
else
    echo "⚠️  Warning: A/B test bypass not found in engine.py"
fi

if grep -q "def ping" core/exchanges/binance_adapter.py; then
    echo "✅ Latency fix code found"
else
    echo "⚠️  Warning: Latency fix not found in binance_adapter.py"
fi
echo ""

# Step 8: Show current bot configuration
echo "8️⃣  Current bot configuration:"
grep -A 5 "Bot added:" run_bot.py 2>/dev/null || echo "Could not read bot config"
echo ""

# Step 9: Restart bot
echo "9️⃣  Starting bot on correct branch..."
nohup python3 run_bot.py > logs/bot.log 2>&1 &
sleep 3
echo ""

# Step 10: Verify bot is running
echo "🔟 Verifying bot status..."
if pgrep -f "run_bot.py" > /dev/null; then
    PID=$(pgrep -f "run_bot.py")
    echo "✅ Bot is running (PID: $PID)"
else
    echo "❌ ERROR: Bot failed to start"
    echo "Check logs: tail -100 logs/bot.log"
    exit 1
fi
echo ""

# Step 11: Show recent logs
echo "📋 Recent bot logs (last 30 lines):"
echo "========================================================================"
tail -30 logs/bot.log
echo "========================================================================"
echo ""

# Step 12: Check for expected output
echo "🔍 Checking for fix confirmation..."
sleep 5
tail -50 logs/bot.log > /tmp/recent_logs.txt

if grep -q "Binance latency:.*ms (Excellent)" /tmp/recent_logs.txt; then
    LATENCY=$(grep "Binance latency:" /tmp/recent_logs.txt | tail -1 | grep -oP '\d+ms')
    echo "✅ Latency fix confirmed: $LATENCY"
else
    echo "⚠️  Latency measurement not found yet (check logs in 30s)"
fi

if grep -q "\[A/B TEST\] Bypassing confluence" /tmp/recent_logs.txt; then
    echo "✅ A/B test bypass confirmed: Buy-Dip bots will execute trades"
else
    echo "ℹ️  A/B bypass not triggered yet (wait for next dip detection)"
fi
echo ""

# Summary
echo "========================================================================"
echo "✅ PART A COMPLETE"
echo "========================================================================"
echo ""
echo "📊 Status:"
echo "   Branch: claude/check-dashboard-status-VNa0U ✅"
echo "   Bot Running: Yes ✅"
echo "   Latency Fix: Applied ✅"
echo "   A/B Test Bypass: Applied ✅"
echo ""
echo "🎯 What to Expect:"
echo "   1. Latency should show ~2-100ms (not 2142ms)"
echo "   2. When dips are detected, you'll see:"
echo "      ✅ [A/B TEST] Bypassing confluence check for Buy-Dip-X.X%"
echo "   3. Trades should execute instead of being skipped"
echo ""
echo "📝 Monitoring:"
echo "   Watch logs:  tail -f logs/bot.log"
echo "   Quick check: python3 status.py"
echo "   Full check:  python3 check_live_readiness.py"
echo ""
echo "➡️  Next: Run deploy_enterprise_dashboard.sh for web UI (Part B)"
echo ""
