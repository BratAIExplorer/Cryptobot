#!/bin/bash
# MEXC API Setup Helper

echo "=========================================="
echo "🔧 MEXC API KEYS SETUP"
echo "=========================================="
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
    echo ""
    echo "Current API configuration:"
    grep -E "MEXC_API_KEY|MEXC_SECRET|TELEGRAM" .env | sed 's/=.*$/=***hidden***/'
    echo ""
else
    echo "❌ .env file NOT found"
    echo ""
    echo "Creating .env from template..."
    cp .env.template .env
    echo "✅ Created .env file"
    echo ""
fi

echo "=========================================="
echo "📋 SETUP INSTRUCTIONS"
echo "=========================================="
echo ""
echo "1️⃣  Get your MEXC API Keys:"
echo "   Go to: https://www.mexc.com/user/openapi"
echo ""
echo "   ⚠️  IMPORTANT: When creating API key:"
echo "   ✅ Check: 'Read'"
echo "   ✅ Check: 'Spot Trading'  ← CRITICAL!"
echo "   ❌ Uncheck: 'Futures' (not needed)"
echo ""
echo "2️⃣  Edit .env file:"
echo "   nano .env"
echo ""
echo "3️⃣  Add your keys:"
echo "   MEXC_API_KEY=your_api_key_here"
echo "   MEXC_SECRET=your_secret_here"
echo "   TELEGRAM_BOT_TOKEN=your_telegram_bot_token"
echo "   TELEGRAM_CHAT_ID=your_telegram_chat_id"
echo ""
echo "4️⃣  Load environment variables:"
echo "   source .env"
echo "   export \$(cat .env | grep -v '^#' | xargs)"
echo ""
echo "5️⃣  Run diagnostic:"
echo "   python3 diagnose_mexc_api.py"
echo ""
echo "=========================================="
echo ""

# Check if variables are currently set
echo "Current environment status:"
if [ -z "$MEXC_API_KEY" ]; then
    echo "❌ MEXC_API_KEY not set in environment"
else
    echo "✅ MEXC_API_KEY is set"
fi

if [ -z "$MEXC_SECRET" ]; then
    echo "❌ MEXC_SECRET not set in environment"
else
    echo "✅ MEXC_SECRET is set"
fi

echo ""
echo "Ready to configure? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Opening .env file in editor..."
    echo "Update your API keys, then save and exit"
    sleep 2
    nano .env 2>/dev/null || vi .env 2>/dev/null || echo "Please edit .env manually"

    echo ""
    echo "Loading environment variables..."
    set -a
    source .env 2>/dev/null
    set +a

    echo "✅ Environment loaded"
    echo ""
    echo "Run diagnostic now:"
    echo "   python3 diagnose_mexc_api.py"
fi
