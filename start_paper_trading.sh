#!/bin/bash
# 🤖 Start Crypto Bot in Paper Trading Mode
# This script launches the bot with proper logging and monitoring

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🤖 Starting Crypto Trading Bot - PAPER MODE"
echo "========================================================================"
echo "Date: $(date)"
echo "Location: $SCRIPT_DIR"
echo ""

# Create necessary directories
mkdir -p data logs backups

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 not found"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import ccxt, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing dependencies..."
    pip3 install -q ccxt pandas numpy
fi

# Show current configuration
echo ""
echo "⚙️  CONFIGURATION:"
echo "   Mode: PAPER TRADING"
echo "   Exchange: MEXC"
echo "   Database: data/trades_v3_paper.db"
echo ""

# Check environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  Telegram alerts: NOT CONFIGURED"
    echo "   (Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable)"
else
    echo "✅ Telegram alerts: ENABLED"
fi

if [ -z "$CRYPTOPANIC_API_KEY" ]; then
    echo "⚠️  CryptoPanic news: NOT CONFIGURED"
    echo "   (Set CRYPTOPANIC_API_KEY to enable)"
else
    echo "✅ CryptoPanic news: ENABLED"
fi

echo ""
echo "📊 ACTIVE STRATEGIES:"
echo "   ✅ Grid Bot BTC (3,000 USD allocation)"
echo "   ✅ Grid Bot ETH (3,000 USD allocation)"
echo "   ✅ SMA Trend V2 (4,000 USD allocation)"
echo "   ✅ Buy-the-Dip Hybrid V2.0 (3,000 USD allocation)"
echo "   ⏸️  Momentum Swing (500 USD - PAUSED/TEST)"
echo "   ✅ Hidden Gem V2 (1,800 USD allocation)"
echo ""
echo "   Total Allocation: ~14,300 USD (paper)"
echo ""

# Create log file name with timestamp
LOG_FILE="logs/bot_$(date +%Y%m%d_%H%M%S).log"

echo "📝 Logging to: $LOG_FILE"
echo ""
echo "========================================================================"
echo "🚀 STARTING BOT..."
echo "========================================================================"
echo ""
echo "   • Press Ctrl+C to stop"
echo "   • View logs: tail -f $LOG_FILE"
echo "   • Monitor: watch -n 60 'sqlite3 data/trades_v3_paper.db \"SELECT COUNT(*) FROM trades;\"'"
echo ""

# Start the bot
python3 run_bot.py 2>&1 | tee "$LOG_FILE"

# Capture exit status
EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Bot stopped gracefully"
else
    echo "⚠️  Bot exited with code: $EXIT_CODE"
fi
echo "========================================================================"
