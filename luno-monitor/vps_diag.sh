#!/bin/bash
# Luno Monitor Diagnostic Script
# Run this on your VPS to find why ZAR prices are still appearing

echo "===================================================="
echo "🔍 Searching for Luno Monitor processes..."
echo "===================================================="
ps aux | grep -E "main.py|src/dashboard.py" | grep -v grep

echo ""
echo "===================================================="
echo "📁 Searching for all luno-monitor directories..."
echo "===================================================="
find / -name "luno-monitor" -type d 2>/dev/null

echo ""
echo "===================================================="
echo "📄 Checking config.py in /root/luno-monitor..."
echo "===================================================="
if [ -f "/root/luno-monitor/config.py" ]; then
    grep -A 15 "CRYPTO_PAIRS =" /root/luno-monitor/config.py
    grep "PROFIT_TARGETS =" /root/luno-monitor/config.py
else
    echo "❌ /root/luno-monitor/config.py NOT FOUND"
fi

echo ""
echo "===================================================="
echo "📄 Checking .env in /root/luno-monitor..."
echo "===================================================="
if [ -f "/root/luno-monitor/.env" ]; then
    grep -E "PROFIT_TARGETS|CRYPTO_PAIRS|BASE_CURRENCY" /root/luno-monitor/.env
else
    echo "ℹ️ No .env found in /root/luno-monitor"
fi

echo ""
echo "===================================================="
echo "📊 Current Screen Sessions..."
echo "===================================================="
screen -ls

echo ""
echo "===================================================="
echo "🧪 Quick Ticker Test (Checking what Luno returns)..."
echo "===================================================="
cd /root/luno-monitor
./venv/bin/python3 -c "import config; from src.luno_client import LunoClient; c=LunoClient(); t=c.get_ticker('XRPMYR'); print(f'XRPMYR: {t[\"last_trade\"]}'); t2=c.get_ticker('XRPZAR'); print(f'XRPZAR: {t2[\"last_trade\"]}')" 2>/dev/null || echo "❌ Test failed (check path or venv)"

echo "===================================================="
echo "✅ Diagnostic Complete"
echo "===================================================="
