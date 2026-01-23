#!/bin/bash
# VPS Deployment Script - Deploy Backend Fixes
# This script deploys the bot_reader.py LEFT JOIN fix to show all 5 bots

echo "========================================="
echo "🚀 Deploying Backend Fixes to VPS"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST="root@72.60.40.29"
PROJECT_DIR="~/cryptobot_v3"
BRANCH="claude/check-dashboard-status-VNa0U"

echo -e "${YELLOW}Step 1: Connecting to VPS...${NC}"
ssh $VPS_HOST << 'ENDSSH'

cd ~/cryptobot_v3

echo ""
echo "========================================="
echo "Step 2: Pulling Latest Code"
echo "========================================="
git fetch origin
git pull origin claude/check-dashboard-status-VNa0U

echo ""
echo "========================================="
echo "Step 3: Checking Changed Files"
echo "========================================="
git log --oneline -3
echo ""
git diff HEAD~1 enterprise/backend/utils/bot_reader.py | head -50

echo ""
echo "========================================="
echo "Step 4: Stopping Backend"
echo "========================================="
pkill -f uvicorn
sleep 2

# Verify it's stopped
if pgrep -f uvicorn > /dev/null; then
    echo "⚠️  Warning: Backend still running, force killing..."
    pkill -9 -f uvicorn
    sleep 2
else
    echo "✅ Backend stopped successfully"
fi

echo ""
echo "========================================="
echo "Step 5: Starting Backend with New Code"
echo "========================================="
cd enterprise/backend

# Create logs directory if not exists
mkdir -p logs

# Start backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
sleep 3

# Verify it started
if pgrep -f uvicorn > /dev/null; then
    echo "✅ Backend started successfully"
    echo "PID: $(pgrep -f uvicorn)"
else
    echo "❌ ERROR: Backend failed to start"
    echo "Check logs: tail -50 logs/backend.log"
    exit 1
fi

echo ""
echo "========================================="
echo "Step 6: Verifying Backend Health"
echo "========================================="
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "========================================="
echo "Step 7: Testing Bot Status Endpoint"
echo "========================================="

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cryptobot.com","password":"change_me_immediately"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "⚠️  Warning: Could not get auth token"
    echo "   Manual check required: Check admin credentials"
else
    echo "✅ Auth token obtained"
    
    # Test bot status
    echo ""
    echo "Bot Status:"
    curl -s http://localhost:8000/api/bots/status \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
    
    echo ""
    echo "Portfolio Summary:"
    curl -s http://localhost:8000/api/trades/portfolio \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Open browser: http://72.60.40.29:3000"
echo "2. Hard refresh: Ctrl+Shift+R"
echo "3. Login: admin@cryptobot.com"
echo "4. Verify all 5 bots are visible"
echo ""
echo "To check logs:"
echo "  tail -f ~/cryptobot_v3/enterprise/backend/logs/backend.log"
echo ""

ENDSSH

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 Deployment Script Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "If you see all 5 bots in the API response above, the deployment was successful!"
echo ""
