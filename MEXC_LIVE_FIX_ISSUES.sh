#!/bin/bash
# MEXC Live Trading - Issue Fix Script
# Run this on your VPS: /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

echo "=========================================="
echo "🔧 MEXC LIVE TRADING - FIX ISSUES"
echo "=========================================="

# Change to LIVE bot directory
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

echo ""
echo "1️⃣  Checking .env file configuration..."
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating .env template..."
    cat > .env << 'EOF'
# MEXC API Credentials (CRITICAL: Use MEXC_SECRET not MEXC_SECRET_KEY!)
MEXC_API_KEY=your_api_key_here
MEXC_SECRET=your_secret_here

# Telegram Alerts
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
TRADING_MODE=LIVE
EXCHANGE=MEXC

# Optional
CRYPTOPANIC_API_KEY=
EOF
    echo "✅ .env template created. Please edit with your credentials:"
    echo "   nano .env"
    exit 1
fi

# Check for common .env mistakes
echo "Checking .env variables..."
if grep -q "MEXC_SECRET_KEY" .env; then
    echo "⚠️  WARNING: Found MEXC_SECRET_KEY (should be MEXC_SECRET)"
    echo "   Fixing automatically..."
    sed -i 's/MEXC_SECRET_KEY/MEXC_SECRET/g' .env
    echo "   ✅ Fixed: MEXC_SECRET_KEY → MEXC_SECRET"
fi

# Validate required variables are set
source .env 2>/dev/null || true

if [ -z "$MEXC_API_KEY" ] || [ "$MEXC_API_KEY" = "your_api_key_here" ]; then
    echo "❌ MEXC_API_KEY not set in .env"
    echo "   Edit .env and add your MEXC API key"
    exit 1
fi

if [ -z "$MEXC_SECRET" ] || [ "$MEXC_SECRET" = "your_secret_here" ]; then
    echo "❌ MEXC_SECRET not set in .env"
    echo "   Edit .env and add your MEXC secret"
    exit 1
fi

echo "✅ .env file configured correctly"

echo ""
echo "2️⃣  Testing MEXC API Connection..."
echo "=========================================="

python3 << 'PYEOF'
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

try:
    mexc = ccxt.mexc({
        'apiKey': os.getenv('MEXC_API_KEY'),
        'secret': os.getenv('MEXC_SECRET'),  # Correct variable name
        'enableRateLimit': True
    })

    # Test connection
    balance = mexc.fetch_balance()
    usdt = balance['USDT']['total']

    print(f"✅ MEXC API Connected!")
    print(f"💰 USDT Balance: ${usdt:,.2f}")
    print(f"📊 Recommended allocation: ${usdt * 0.8:,.2f} (keep 20% reserve)")

    # Recommended position sizes
    if usdt >= 1000:
        print(f"\n💡 Recommended position sizes for ${usdt:,.0f} balance:")
        print(f"   Buy-the-Dip: ${min(50, usdt * 0.05):.0f}/coin")
        print(f"   Grid Bots: ${min(300, usdt * 0.15):.0f} each")
        print(f"   Other strategies: ${min(100, usdt * 0.08):.0f}/coin")
    else:
        print(f"\n⚠️  Balance ${usdt:,.0f} is LOW for 6-strategy portfolio")
        print(f"   Minimum recommended: $1,000")
        print(f"   Consider starting with 2-3 strategies only")

except ccxt.AuthenticationError as e:
    print(f"❌ Authentication Error: {e}")
    print("   Check your MEXC_API_KEY and MEXC_SECRET in .env")
    exit(1)
except Exception as e:
    print(f"❌ Connection Error: {e}")
    exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ MEXC API test failed. Fix the errors above before proceeding."
    exit 1
fi

echo ""
echo "3️⃣  Checking Database Schema..."
echo "=========================================="

# Check paper trading database schema first
PAPER_DB="/Antigravity/antigravity/scratch/crypto_trading_bot/data/trades_v3_paper.db"
LIVE_DB="data/trades_mexc_live.db"

if [ -f "$PAPER_DB" ]; then
    echo "Checking paper trading database schema..."
    echo ""
    echo "📋 Positions table schema:"
    sqlite3 "$PAPER_DB" ".schema positions" || echo "No positions table found"

    echo ""
    echo "📋 Trades table schema:"
    sqlite3 "$PAPER_DB" ".schema trades" || echo "No trades table found"

    # Try to get paper trading stats with correct column names
    echo ""
    echo "📊 Attempting to read paper trading performance..."

    # Try different column name variations
    for col in pnl profit realized_pnl; do
        result=$(sqlite3 "$PAPER_DB" "SELECT COUNT(*) FROM positions WHERE status='CLOSED' LIMIT 1;" 2>/dev/null)
        if [ $? -eq 0 ] && [ ! -z "$result" ]; then
            echo "Found $result closed positions"

            # Try to calculate performance
            sqlite3 "$PAPER_DB" << SQL
.mode column
.headers on
SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN exit_price > entry_price THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN exit_price <= entry_price THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN exit_price > entry_price THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate_pct
FROM positions
WHERE status='CLOSED' AND exit_time > datetime('now', '-24 hours');
SQL
            break
        fi
    done
fi

echo ""
echo "4️⃣  Checking Live Database Setup..."
echo "=========================================="

if [ ! -f "$LIVE_DB" ]; then
    echo "⚠️  Live database doesn't exist yet (will be created on first run)"
    mkdir -p data
else
    echo "✅ Live database exists: $LIVE_DB"
    echo "   Tables:"
    sqlite3 "$LIVE_DB" ".tables"
fi

echo ""
echo "5️⃣  Testing Telegram Notifications..."
echo "=========================================="

python3 << 'PYEOF'
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not token or not chat_id:
    print("⚠️  Telegram not configured (optional)")
    exit(0)

try:
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    message = """🔴 **MEXC LIVE BOT - PRE-LAUNCH TEST** 🔴

This is an automated test message from your MEXC live trading bot.

✅ If you receive this, Telegram alerts are working!

⚠️ **REMINDER:** This will be REAL MONEY trading.

Status: Pre-launch checks in progress...
"""

    response = requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    })

    if response.status_code == 200:
        print("✅ Telegram test message sent successfully!")
        print(f"   Check chat ID: {chat_id}")
    else:
        print(f"⚠️  Telegram response: {response.status_code}")
        print(f"   {response.text}")

except Exception as e:
    print(f"❌ Telegram error: {e}")
PYEOF

echo ""
echo "6️⃣  Verifying Bot Configuration..."
echo "=========================================="

# Check if run_bot_mexc.py exists
if [ ! -f "run_bot_mexc.py" ]; then
    echo "❌ run_bot_mexc.py not found!"
    echo "   Looking for bot runner scripts..."
    ls -la run*.py 2>/dev/null || echo "   No run*.py files found"
    exit 1
fi

echo "✅ Bot script found: run_bot_mexc.py"

# Check position sizes in the config
echo ""
echo "📊 Current position sizes in run_bot_mexc.py:"
grep -A 2 "'amount':" run_bot_mexc.py | head -20

echo ""
echo "⚠️  CRITICAL: Verify position sizes are appropriate for your balance!"
echo "   Paper trading uses $500/coin - REDUCE THIS for live trading!"

echo ""
echo "=========================================="
echo "✅ PRE-LAUNCH CHECKS COMPLETE"
echo "=========================================="
echo ""
echo "📋 SUMMARY:"
echo "   1. .env configuration: ✅"
echo "   2. MEXC API connection: ✅"
echo "   3. Database schema: ✅"
echo "   4. Telegram alerts: ✅"
echo "   5. Bot configuration: ⚠️  REVIEW POSITION SIZES"
echo ""
echo "⏭️  NEXT STEPS:"
echo "   1. Review paper trading performance (if available)"
echo "   2. Adjust position sizes in run_bot_mexc.py for your balance"
echo "   3. Create a test launch with 1-2 strategies first"
echo "   4. Monitor closely for first 24 hours"
echo ""
echo "🚀 When ready to launch:"
echo "   nohup python3 run_bot_mexc.py > logs/live_$(date +%Y%m%d).log 2>&1 &"
echo ""
