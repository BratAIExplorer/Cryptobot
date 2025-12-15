#!/bin/bash
# Luno Monitor VPS Deployment Script
# Deploys currency conversion fixes to VPS

set -e  # Exit on error

echo "========================================"
echo "🚀 Deploying Luno Monitor Fixes to VPS"
echo "========================================"

VPS_USER="root"
VPS_HOST="srv1010193"
VPS_PATH="/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor"
LOCAL_PATH="c:/CryptoBot_Project/luno-monitor"

# Check if we have SSH access
echo ""
echo "📡 Testing VPS connection..."
if ! ssh -o ConnectTimeout=5 ${VPS_USER}@${VPS_HOST} "echo 'Connected'" &>/dev/null; then
    echo "❌ Cannot connect to VPS. Please check your SSH connection."
    exit 1
fi
echo "✅ VPS connection successful"

# Create backup on VPS
echo ""
echo "💾 Creating backup on VPS..."
ssh ${VPS_USER}@${VPS_HOST} "
    cd /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor
    if [ -f config.py ]; then
        cp config.py config.py.backup_$(date +%Y%m%d_%H%M%S)
        cp src/currency_converter.py src/currency_converter.py.backup_$(date +%Y%m%d_%H%M%S)
        echo '✅ Backup created'
    fi
"

# Upload fixed files
echo ""
echo "📤 Uploading fixed files to VPS..."

# Upload currency_converter.py
scp "${LOCAL_PATH}/src/currency_converter.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/src/currency_converter.py
echo "✅ currency_converter.py uploaded"

# Upload config.py
scp "${LOCAL_PATH}/config.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/config.py
echo "✅ config.py uploaded"

# Upload main.py
scp "${LOCAL_PATH}/main.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/main.py
echo "✅ main.py uploaded"

# Upload dip_monitor.py
scp "${LOCAL_PATH}/dip_monitor.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/dip_monitor.py
echo "✅ dip_monitor.py uploaded"

# Upload dip_monitor_config.py
scp "${LOCAL_PATH}/dip_monitor_config.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/dip_monitor_config.py
echo "✅ dip_monitor_config.py uploaded"

# Upload alert_state_manager.py
scp "${LOCAL_PATH}/alert_state_manager.py" ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/alert_state_manager.py
echo "✅ alert_state_manager.py uploaded"

# Restart Luno Monitor on VPS
echo ""
echo "🔄 Restarting Luno Monitor on VPS..."
ssh ${VPS_USER}@${VPS_HOST} "
    cd ${VPS_PATH}
    
    # Kill existing Luno monitor processes
    pkill -f 'python.*main.py' || echo 'No running main.py process'
    pkill -f 'python.*dip_monitor.py' || echo 'No running dip_monitor.py process'
    
    # Give processes time to stop
    sleep 2
    
    # Start main monitor in background
    nohup python3 main.py > luno_monitor.log 2>&1 &
    echo 'Luno Portfolio Monitor started'
    
    # Start dip monitor in background
    nohup python3 dip_monitor.py > dip_monitor.log 2>&1 &
    echo 'Dip Monitor started'
    
    # Give processes time to start
    sleep 3
    
    # Check if processes are running
    if pgrep -f 'python.*main.py' > /dev/null; then
        echo '✅ Luno Portfolio Monitor is running'
    else
        echo '❌ Warning: Luno Portfolio Monitor may not have started'
    fi
    
    if pgrep -f 'python.*dip_monitor.py' > /dev/null; then
        echo '✅ Dip Monitor is running'
    else
        echo '❌ Warning: Dip Monitor may not have started'
    fi
"

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "Summary of Fixes Deployed:"
echo "  ✅ Currency conversion: ZAR → MYR (live rates)"
echo "  ✅ Alert cooldowns: 24h profit, 2h drops"
echo "  ✅ Buying thresholds: 15% / 50%"
echo ""
echo "Next steps:"
echo "  1. Monitor logs for any errors:"
echo "     ssh ${VPS_USER}@${VPS_HOST} 'tail -f ${VPS_PATH}/luno_monitor.log'"
echo ""
echo "  2. Verify prices are correct (should be ~4x lower than before)"
echo ""
echo "  3. Check for duplicate alerts (should have cooldown messages)"
echo ""
