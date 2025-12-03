#!/bin/bash
# Step 7: Fix Dashboard Permissions & Re-create Strategy Script

echo "=========================================="
echo "🔧 STEP 7: Fix Dashboard Permissions"
echo "=========================================="
echo ""

echo "--- 1. Fixing Service Status Check Permissions ---"
# The dashboard runs as a user that might not have permission to check systemctl status
# We'll add a sudoers rule to allow 'systemctl is-active' without password

# Create sudoers file
cat > /etc/sudoers.d/dashboard_monitor << 'EOF'
root ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active *
EOF

chmod 0440 /etc/sudoers.d/dashboard_monitor
echo "✅ Added sudo permissions for systemctl is-active"

echo ""
echo "--- 2. Updating Dashboard Code to use Sudo ---"
python3 << 'PYTHON_PATCH_DASHBOARD'
with open('/root/luno-monitor/src/dashboard.py', 'r') as f:
    content = f.read()

# Update the command to use sudo
if 'cmd = f"systemctl is-active {service}"' in content:
    content = content.replace(
        'cmd = f"systemctl is-active {service}"', 
        'cmd = f"sudo systemctl is-active {service}"'
    )
    print("✅ Updated dashboard.py to use sudo for status checks")
else:
    print("⚠️ Could not find exact line to update in dashboard.py")

with open('/root/luno-monitor/src/dashboard.py', 'w') as f:
    f.write(content)
PYTHON_PATCH_DASHBOARD

echo ""
echo "--- 3. Re-creating Strategy Tweak Script ---"
# Re-creating step4_tweak_strategy.sh since it was missing
cat > /root/step4_tweak_strategy.sh << 'SCRIPT_EOF'
#!/bin/bash
# Step 4: Optimize Buy-the-Dip Strategy (Top 20 Coins Edition)

echo "=========================================="
echo "🚀 STEP 4: Strategy Optimization (Top 20 Coins)"
echo "=========================================="
echo ""

ENGINE_FILE="/Antigravity/antigravity/scratch/crypto_trading_bot/core/engine.py"
RUN_BOT_FILE="/Antigravity/antigravity/scratch/crypto_trading_bot/run_bot.py"

echo "--- 1. Widening Buy Logic (engine.py) ---"
# Change strict 8-10% drop to 4-15% drop to catch more dips
python3 << 'PYTHON_PATCH_ENGINE'
with open('/Antigravity/antigravity/scratch/crypto_trading_bot/core/engine.py', 'r') as f:
    content = f.read()

# Old logic: if -0.10 <= drop_pct <= -0.08:
# New logic: if -0.15 <= drop_pct <= -0.04:
old_logic = "if -0.10 <= drop_pct <= -0.08:"
new_logic = "if -0.15 <= drop_pct <= -0.04:  # Widened to 4-15% drop"

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print("✅ Logic updated: 8-10% -> 4-15% drop")
else:
    print("⚠️ Could not find exact logic line, checking if already updated...")
    if new_logic in content:
        print("✅ Logic already updated")
    else:
        print("❌ Failed to find logic line to update")

with open('/Antigravity/antigravity/scratch/crypto_trading_bot/core/engine.py', 'w') as f:
    f.write(content)
PYTHON_PATCH_ENGINE

echo ""
echo "--- 2. Expanding to Top 20 Coins (run_bot.py) ---"
# Add Top 20 coins to Buy-the-Dip strategy
python3 << 'PYTHON_PATCH_CONFIG'
with open('/Antigravity/antigravity/scratch/crypto_trading_bot/run_bot.py', 'r') as f:
    content = f.read()

# Target list: Top 20 by volume/market cap
top_20_coins = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
    'DOGE/USDT', 'ADA/USDT', 'TRX/USDT', 'AVAX/USDT', 'SHIB/USDT', 
    'DOT/USDT', 'LINK/USDT', 'BCH/USDT', 'NEAR/USDT', 'LTC/USDT', 
    'UNI/USDT', 'PEPE/USDT', 'APT/USDT', 'ICP/USDT', 'ETC/USDT'
]

# Format as string for replacement
new_list_str = str(top_20_coins)

import re
pattern = r"('type': 'Buy-the-Dip',\s*\n\s*'symbols': )\[.*?\]"
replacement = f"\\1{new_list_str}"

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("✅ Expanded Buy-the-Dip watchlist to Top 20 Coins")
else:
    print("❌ Failed to find Buy-the-Dip symbols list")

with open('/Antigravity/antigravity/scratch/crypto_trading_bot/run_bot.py', 'w') as f:
    f.write(content)
PYTHON_PATCH_CONFIG

echo ""
echo "=========================================="
echo "✅ OPTIMIZATION COMPLETE"
echo "=========================================="
SCRIPT_EOF

chmod +x /root/step4_tweak_strategy.sh
echo "✅ Re-created /root/step4_tweak_strategy.sh"

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE"
echo "=========================================="
echo ""
echo "📋 Restart services to apply:"
echo "  systemctl restart portfolio_monitor.service"
echo ""
echo "📋 Run the strategy tweak script:"
echo "  /root/step4_tweak_strategy.sh"
echo "  systemctl restart crypto_bot_runner.service"
