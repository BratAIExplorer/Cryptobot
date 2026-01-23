# 🚀 VPS Deployment Guide - Dashboard Fix

## Quick Deployment (Copy-Paste Method)

### Option A: Automated Script

Run this **single command** from your local machine:

```bash
bash C:\Antigravity\Au-tomata\Cryptobot\DEPLOY_DASHBOARD_FIX.sh
```

### Option B: Manual Steps (If script doesn't work)

**Step 1: SSH to VPS**
```bash
ssh root@72.60.40.29
```

**Step 2: Pull Latest Code**
```bash
cd ~/cryptobot_v3
git pull origin claude/check-dashboard-status-VNa0U
```

**Step 3: Restart Backend**
```bash
cd enterprise/backend
pkill -f uvicorn
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
```

**Step 4: Verify Deployment**
```bash
# Check backend is running
ps aux | grep uvicorn | grep -v grep

# Test API
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cryptobot.com","password":"change_me_immediately"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -s http://localhost:8000/api/trades/portfolio \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Expected Results

### You should see ALL 5 bots in the response:

```json
{
  "strategies": [
    {"name": "Grid Bot BTC", "balance": 250, "trades": 0, "pnl": 0.0},
    {"name": "Grid Bot ETH", "balance": 200, "trades": 0, "pnl": 0.0},
    {"name": "Buy-Dip-5.2%", "balance": 333, "trades": 0, "pnl": 0.0},
    {"name": "Buy-Dip-5.5%", "balance": 333, "trades": 0, "pnl": 0.0},
    {"name": "Buy-Dip-8.0%", "balance": 334, "trades": 0, "pnl": 0.0}
  ],
  "total_value_usd": 1500.0
}
```

## Verification

1. **Open Dashboard**: http://72.60.40.29:3000
2. **Hard Refresh**: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. **Login**: admin@cryptobot.com / change_me_immediately
4. **Check**: You should see all 5 bots on the dashboard

## Troubleshooting

### If still showing only 1-3 bots:

**Check 1: Backend Version**
```bash
ssh root@72.60.40.29
cd ~/cryptobot_v3
git log --oneline -1
```
Should show: `3e36f7f fix: complete Bug #2 - show all bots via LEFT JOIN`

**Check 2: Backend Logs**
```bash
tail -50 ~/cryptobot_v3/enterprise/backend/logs/backend.log
```
Look for errors

**Check 3: Database**
```bash
sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db \
  "SELECT strategy, status, wallet_balance FROM bot_status;"
```
Should show 5 rows

### If buttons still don't work:
This is expected - Phase 2 (button functionality) is next. Backend deployment only fixes the bot visibility issue.

## Time Estimate
- Automated script: 2-3 minutes
- Manual steps: 5-7 minutes

## Success Criteria
✅ All 5 bots visible on dashboard  
✅ Portfolio total shows $1,500  
✅ No API errors in console  
⏳ Buttons still won't work (Phase 2)

---

**Status**: Ready to deploy
**Risk**: Low (only restarting backend with new code)
**Rollback**: `git checkout HEAD~1 enterprise/backend/utils/bot_reader.py` then restart
