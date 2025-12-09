#!/bin/bash

# Clear screen
clear

echo "==================================================="
echo "🚀 Starting Lumina Crypto Bot (v3.0 Refactor)"
echo "==================================================="

# 1. Check Python Version
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "❌ Error: Python 3 not found! Please install python3."
    exit 1
fi

echo "✅ Using Python: $($PY_CMD --version)"

# 2. Install Requirements (Quietly)
echo "📦 Checking dependencies..."
$PY_CMD -m pip install -q -r requirements.txt

# 3. Check for Database Migration
if [ ! -f "data/trades_v3.db" ]; then
    echo "⚠️  V3 Database not found. Running migration..."
    $PY_CMD scripts/migrate_v3.py
else
    echo "✅ V3 Database found."
fi

# 4. Run the Bot
echo "🤖 Launching Engine..."
echo "---------------------------------------------------"
$PY_CMD run_bot.py
