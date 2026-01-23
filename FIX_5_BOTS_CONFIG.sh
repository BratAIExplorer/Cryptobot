#!/bin/bash
################################################################################
# FIX 5 BOTS - Replace single Buy-the-Dip with 3 A/B Test Variants
# Date: 2026-01-23
# Purpose: Create 3 separate Buy-Dip bots instead of 1
################################################################################

set -e

echo "========================================================================"
echo "🔧 FIXING BOT CONFIGURATION - Creating 5 Separate Bots"
echo "========================================================================"
echo ""

cd ~/cryptobot_v3

# Backup current config
echo "📦 Creating backup..."
cp run_bot.py run_bot.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Create Python script to modify run_bot.py
echo "🔧 Creating bot configuration fix..."

cat > /tmp/fix_bots.py << 'ENDPYTHON'
#!/usr/bin/env python3
"""
Fix run_bot.py to create 3 separate Buy-the-Dip bots instead of 1
"""
import re

# Read the file
with open('run_bot.py', 'r') as f:
    content = f.read()

# Find and replace the single Buy-the-Dip bot with 3 variants
old_pattern = r'''    engine\.add_bot\(\{
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': top_10,

        # Budget: \$1000 Total \(\$100 per coin\)
        'amount': 15,                 # \$15 per buy
        'initial_balance': 1000,
        'max_exposure_per_coin': 100, # Cap at \$100 per coin

        # Entry Conditions \(V3\)
        'dip_threshold': 0\.03,       # 3% dip
        'rsi_limit': 35,             # V3 param
        'cooldown_minutes': 60,

        # Legacy/Hybrid Fallbacks
        'dip_percentage': 0\.03,
        'min_confluence': 65,

        # PROFIT RULES \(User Request: 5-10% Profit, NO Losses\)
        'take_profit_pct': 0\.08,      # Target 8% Profit
        'stop_loss_pct': None,        # DISABLING STOP LOSS \(Hold until profit\)
        'stop_loss_enabled': False,

        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    \}\)'''

new_code = '''    # ==========================================
    # 🧪 A/B TEST: 3 Buy-Dip Variants ($333 each)
    # ==========================================
    # Testing different profit targets:
    # - Conservative: 5.2% (quick wins)
    # - Standard: 5.5% (balanced)
    # - Aggressive: 8.0% (patient hold)

    # Variant 1: Conservative (5.2% profit)
    engine.add_bot({
        'name': 'Buy-Dip-5.2%',
        'type': 'Buy-the-Dip',
        'symbols': top_10,
        'amount': 15,
        'initial_balance': 333,
        'max_exposure_per_coin': 33,
        'dip_threshold': 0.03,
        'rsi_limit': 35,
        'cooldown_minutes': 60,
        'dip_percentage': 0.03,
        'min_confluence': 65,
        'take_profit_pct': 0.052,      # 5.2% profit target
        'stop_loss_pct': None,
        'stop_loss_enabled': False,
        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })

    # Variant 2: Standard (5.5% profit)
    engine.add_bot({
        'name': 'Buy-Dip-5.5%',
        'type': 'Buy-the-Dip',
        'symbols': top_10,
        'amount': 15,
        'initial_balance': 333,
        'max_exposure_per_coin': 33,
        'dip_threshold': 0.03,
        'rsi_limit': 35,
        'cooldown_minutes': 60,
        'dip_percentage': 0.03,
        'min_confluence': 65,
        'take_profit_pct': 0.055,      # 5.5% profit target
        'stop_loss_pct': None,
        'stop_loss_enabled': False,
        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })

    # Variant 3: Aggressive (8.0% profit)
    engine.add_bot({
        'name': 'Buy-Dip-8.0%',
        'type': 'Buy-the-Dip',
        'symbols': top_10,
        'amount': 15,
        'initial_balance': 334,
        'max_exposure_per_coin': 33,
        'dip_threshold': 0.03,
        'rsi_limit': 35,
        'cooldown_minutes': 60,
        'dip_percentage': 0.03,
        'min_confluence': 65,
        'take_profit_pct': 0.080,      # 8.0% profit target
        'stop_loss_pct': None,
        'stop_loss_enabled': False,
        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })'''

# Check if pattern exists
if re.search(old_pattern, content, re.MULTILINE):
    content = re.sub(old_pattern, new_code, content, count=1, flags=re.MULTILINE)
    print("✅ Found and replaced single Buy-the-Dip bot with 3 variants")
else:
    print("⚠️  Pattern not found - trying alternate approach")
    # Try simpler pattern matching
    if "'name': 'Buy-the-Dip Strategy'" in content:
        # Find the start and end of the bot config
        start_idx = content.find("engine.add_bot({\n        'name': 'Buy-the-Dip Strategy'")
        if start_idx != -1:
            # Find the closing })\n after this bot
            temp_content = content[start_idx:]
            # Count braces to find matching close
            brace_count = 0
            end_offset = 0
            for i, char in enumerate(temp_content):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_offset = i + 2  # Include the )
                        break

            if end_offset > 0:
                end_idx = start_idx + end_offset
                content = content[:start_idx] + new_code + content[end_idx:]
                print("✅ Used alternate method to replace bot configuration")
            else:
                print("❌ Could not find end of bot configuration")
                exit(1)
    else:
        print("❌ Could not find Buy-the-Dip Strategy bot")
        exit(1)

# Write the modified content
with open('run_bot.py', 'w') as f:
    f.write(content)

print("✅ Bot configuration updated successfully")
ENDPYTHON

python3 /tmp/fix_bots.py

echo "✅ Configuration fix applied"
echo ""

# Stop current bot
echo "🛑 Stopping current bot..."
pkill -f run_bot.py 2>/dev/null || echo "No bot running"
sleep 3

# Archive old database
if [ -f "data/multi/trades_paper.db" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ARCHIVE_DIR="data/archives/5bots_fix_$TIMESTAMP"
    mkdir -p "$ARCHIVE_DIR"
    mv data/multi/trades_paper.db "$ARCHIVE_DIR/"
    echo "✅ Old database archived to: $ARCHIVE_DIR"
fi
echo ""

# Restart backend
echo "🔄 Restarting backend..."
cd ~/cryptobot_v3/enterprise/backend
pkill -f "uvicorn main:app" 2>/dev/null || echo "Backend not running"
sleep 2
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend restarted (PID: $BACKEND_PID)"
sleep 3

# Start bot with new config
echo "🚀 Starting bot with 5 bots configuration..."
cd ~/cryptobot_v3
nohup python3 -u run_bot.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "✅ Bot started (PID: $BOT_PID)"
echo ""

# Wait for initialization
echo "⏳ Waiting 15 seconds for bot initialization..."
sleep 15

# Verification
echo "========================================================================"
echo "✅ VERIFICATION"
echo "========================================================================"
echo ""

echo "📋 Running Processes:"
ps aux | grep -E "run_bot|uvicorn" | grep -v grep | awk '{print "   ", $2, $11, $12, $13, $14}'
echo ""

echo "📋 Bot Startup (checking for 5 bots):"
grep "Bot added" logs/bot.log | tail -10
echo ""

echo "📋 Expected Output:"
echo "   ✅ Bot added: Grid Bot BTC"
echo "   ✅ Bot added: Grid Bot ETH"
echo "   ✅ Bot added: Buy-Dip-5.2%"
echo "   ✅ Bot added: Buy-Dip-5.5%"
echo "   ✅ Bot added: Buy-Dip-8.0%"
echo ""

echo "📊 Total Capital Check:"
grep "Total Capital" logs/bot.log | tail -1
echo ""

echo "========================================================================"
echo "🎉 FIX COMPLETE!"
echo "========================================================================"
echo ""
echo "🔄 HARD REFRESH your browser (Ctrl+Shift+R)"
echo "📊 Dashboard should now show:"
echo "   - 5 bots (2 Grid + 3 Buy-Dip)"
echo "   - Portfolio: \$1,500"
echo "   - Fresh data (0 trades initially)"
echo ""
echo "========================================================================"
echo ""
