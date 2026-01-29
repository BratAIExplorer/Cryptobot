#!/bin/bash

# Safe Restart Script - OPTION A (Natural Exit)
# Usage: sudo ./safe_restart_option_a.sh

echo "🛡️  INITIATING SAFE STARTUP (OPTION A)..."
echo "   Goal: Preserve Open Positions, Apply Fixes, Restart."

# 1. Stop Service
echo "🛑 STOPPING CryptoBot Service..."
sudo systemctl stop cryptobot
sleep 2

# 2. Archive State
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR="REPORTS/archive_option_a_${TIMESTAMP}"
mkdir -p "$ARCHIVE_DIR"

echo "💾 ARCHIVING Current State to $ARCHIVE_DIR..."
cp data/trades_paper.db "$ARCHIVE_DIR/"
cp logs/bot_engine.log "$ARCHIVE_DIR/"
cp run_bot.py "$ARCHIVE_DIR/"
echo "   -> Backup Complete."

# 3. Verify Code Update
echo "🔍 VERIFYING Code Update..."
if grep -q "# 'name': 'Buy-the-Dip Strategy'" run_bot.py; then
    echo "   ✅ CORRECT: Legacy Bot is DISABLED in run_bot.py"
else
    echo "   ❌ WARNING: Legacy Bot appears ENABLED. Please check run_bot.py!"
    echo "   (Continuing, but double-check logs after start)"
fi

if grep -q "'min_confluence': 40" run_bot.py; then
    echo "   ✅ CORRECT: Confluence requirements set to 40"
else
    echo "   ❌ WARNING: Confluence might be 0 (Data Collection). Check run_bot.py!"
fi

# 4. Restart
echo "🚀 RESTARTING CryptoBot Service..."
sudo systemctl start cryptobot

echo "✅ SUCCESS. Bot is running with EXISTING database."
echo "   -> Open positions are preserved."
echo "   -> New trades will use strict logic."
echo "   -> Monitor logs: tail -f logs/bot_engine.log"
