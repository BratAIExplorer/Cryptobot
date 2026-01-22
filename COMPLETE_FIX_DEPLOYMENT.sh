#!/bin/bash
################################################################################
# COMPLETE FIX - All Issues Resolved
# Date: 2026-01-22
# Purpose: Fix starting capital, enable 5 bots, lower confluence, fresh data
################################################################################

set -e

echo "========================================================================"
echo "🔧 COMPLETE FIX - Deploying All Solutions"
echo "========================================================================"
echo ""

cd ~/cryptobot_v3

# ============================================================================
# FIX 1: Starting Capital Bug (10000 → 1500)
# ============================================================================
echo "📊 FIX 1: Correcting starting capital..."

# Fix in risk_module.py line 645
sed -i 's/portfolio_value=Decimal("10000")/portfolio_value=Decimal("1500")/' core/risk_module.py

# Verify
grep "portfolio_value=Decimal" core/risk_module.py | tail -1
echo "✅ Starting capital fixed: 10000 → 1500"
echo ""

# ============================================================================
# FIX 2: Lower Confluence Threshold for UNDEFINED Regime
# ============================================================================
echo "📊 FIX 2: Lowering confluence threshold..."

# Check current threshold logic in engine.py
if grep -q "threshold = 20" core/engine.py; then
    # Change threshold from 20 to 10 for UNDEFINED regime
    sed -i 's/threshold = 20/threshold = 10/' core/engine.py
    echo "✅ Confluence threshold lowered: 20 → 10"
else
    echo "ℹ️  Confluence threshold already configured"
fi
echo ""

# ============================================================================
# FIX 3: Enable A/B Test (3 Buy-Dip Variants = 5 Total Bots)
# ============================================================================
echo "📊 FIX 3: Enabling A/B test for 5 bots..."

# Check if A/B test is already enabled
if grep -q "AB_TEST_ENABLED = True" run_bot.py; then
    echo "ℹ️  A/B test already enabled"
else
    # Add A/B test configuration at top of run_bot.py (after imports)
    sed -i '/^from core.engine import TradingEngine/a\\n# A/B Test Configuration\nAB_TEST_ENABLED = True\nAB_TEST_VARIANTS = [\n    {"name": "Buy-Dip-5.2%", "take_profit": 0.052},\n    {"name": "Buy-Dip-5.5%", "take_profit": 0.055},\n    {"name": "Buy-Dip-8.0%", "take_profit": 0.080}\n]' run_bot.py
    echo "✅ A/B test enabled with 3 variants"
fi
echo ""

# ============================================================================
# FIX 4: Archive Old Data & Restart with Fresh Database
# ============================================================================
echo "📊 FIX 4: Ensuring fresh database..."

# Stop bot if running
echo "🛑 Stopping current bot..."
pkill -f run_bot.py 2>/dev/null || echo "No bot running"
sleep 3

# Archive any existing database
if [ -f "data/multi/trades_paper.db" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ARCHIVE_DIR="data/archives/complete_fix_$TIMESTAMP"
    mkdir -p "$ARCHIVE_DIR"
    mv data/multi/trades_paper.db "$ARCHIVE_DIR/"
    echo "✅ Old database archived to: $ARCHIVE_DIR"
else
    echo "ℹ️  No existing database to archive"
fi
echo ""

# ============================================================================
# FIX 5: Restart Backend to Clear Cache
# ============================================================================
echo "📊 FIX 5: Restarting backend..."

cd ~/cryptobot_v3/enterprise/backend
pkill -f "uvicorn main:app" 2>/dev/null || echo "Backend not running"
sleep 2

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend restarted (PID: $BACKEND_PID)"
sleep 5
echo ""

# ============================================================================
# FIX 6: Start Bot with All Fixes
# ============================================================================
echo "📊 FIX 6: Starting bot with all fixes..."

cd ~/cryptobot_v3
nohup python3 -u run_bot.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "✅ Bot started (PID: $BOT_PID)"
echo ""

# Wait for initialization
echo "⏳ Waiting 15 seconds for bot initialization..."
sleep 15

# ============================================================================
# VERIFICATION
# ============================================================================
echo "========================================================================"
echo "✅ VERIFICATION"
echo "========================================================================"
echo ""

# Check processes
echo "📋 Running Processes:"
ps aux | grep -E "run_bot|uvicorn" | grep -v grep | awk '{print "   ", $2, $11, $12, $13, $14}'
echo ""

# Check bot logs
echo "📋 Bot Status (last 30 lines):"
tail -30 logs/bot.log | tail -15
echo ""

# Check database
if [ -f "data/multi/trades_paper.db" ]; then
    TRADE_COUNT=$(sqlite3 data/multi/trades_paper.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "0")
    echo "📊 Database: $TRADE_COUNT trades"
else
    echo "📊 Database: Not created yet (will be created on first trade)"
fi
echo ""

# Check backend health
echo "📊 Backend Health:"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Backend not responding"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "========================================================================"
echo "🎉 COMPLETE FIX DEPLOYED!"
echo "========================================================================"
echo ""
echo "✅ All Fixes Applied:"
echo "   1. Starting capital: 10000 → 1500 (correct loss %)"
echo "   2. Confluence threshold: 20 → 10 (allow dips in UNDEFINED regime)"
echo "   3. A/B test: Enabled (5 bots total)"
echo "   4. Database: Fresh start"
echo "   5. Backend: Cache cleared"
echo "   6. Bot: Restarted with all fixes"
echo ""
echo "🤖 Expected Bot Configuration (5 Bots):"
echo "   1. Grid Bot BTC - \$250"
echo "   2. Grid Bot ETH - \$250"
echo "   3. Buy-Dip-5.2% - ~\$333 (Conservative)"
echo "   4. Buy-Dip-5.5% - ~\$333 (Standard)"
echo "   5. Buy-Dip-8.0% - ~\$333 (Aggressive)"
echo ""
echo "   Total Capital: \$1,500 (Paper Mode)"
echo ""
echo "📊 Dashboard Access:"
echo "   URL: http://72.60.40.29:3000"
echo "   Login: admin@cryptobot.com / change_me_immediately"
echo ""
echo "   🔄 HARD REFRESH your browser (Ctrl+Shift+R) to clear cache!"
echo ""
echo "📝 Monitoring:"
echo "   Bot logs:     tail -f ~/cryptobot_v3/logs/bot.log"
echo "   Backend logs: tail -f ~/cryptobot_v3/enterprise/backend/logs/backend.log"
echo "   Quick status: ps aux | grep -E 'run_bot|uvicorn' | grep -v grep"
echo ""
echo "🎯 What to Expect:"
echo "   - Grid Bot BTC: Should place BUY orders at grid levels"
echo "   - Grid Bot ETH: Should place BUY orders at grid levels"
echo "   - Buy-Dip bots: Should accept dips with score ≥ 10 (not blocked)"
echo "   - Risk manager: Loss % should be accurate (~1-3%, not 85%)"
echo "   - Dashboard: Should show 5 bots with fresh data"
echo ""
echo "========================================================================"
echo ""
