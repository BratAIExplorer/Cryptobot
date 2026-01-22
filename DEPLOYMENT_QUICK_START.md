# 🚀 Deployment Quick Start Guide

**Target**: VPS at `/root/cryptobot_v3`
**Time Required**: 35 minutes (5 min Part A + 30 min Part B)
**Branch**: `claude/check-dashboard-status-VNa0U`

---

## 📋 Prerequisites

- SSH access to your VPS
- VPS IP address
- Git repository access

---

## 🎯 What These Scripts Do

### Part A: Fix Buy-Dip Bots (5 minutes)
**File**: `fix_buy_dip_bots.sh`

**Fixes**:
- ✅ Switches to correct branch with A/B test bypass
- ✅ Fixes latency measurement (shows ~2ms not 2142ms)
- ✅ Enables Buy-Dip bots to execute trades
- ✅ Backs up data before changes

**What to Expect**:
```
✅ Bot is running (PID: XXXXX)
✅ Latency fix confirmed: 2-100ms
✅ A/B test bypass confirmed: Buy-Dip bots will execute trades
```

### Part B: Deploy Enterprise Dashboard (30 minutes)
**File**: `deploy_enterprise_dashboard.sh`

**Deploys**:
- ✅ Backend API (FastAPI) on port 8000
- ✅ Frontend Web UI (Next.js) on port 3000
- ✅ PostgreSQL database for users
- ✅ Auto-installs Node.js if missing

**Result**:
- Web dashboard at `http://YOUR_VPS_IP:3000`
- Control bot without SSH/terminal
- View trades, portfolio, performance

---

## 🚀 Step-by-Step Execution

### Step 1: SSH to Your VPS

```bash
ssh root@YOUR_VPS_IP
```

Replace `YOUR_VPS_IP` with your actual VPS IP address.

---

### Step 2: Navigate to Bot Directory

```bash
cd ~/cryptobot_v3
```

---

### Step 3: Pull Latest Code

```bash
git pull origin claude/check-dashboard-status-VNa0U
```

**Expected Output**:
```
Already on 'claude/check-dashboard-status-VNa0U'
From https://github.com/...
   b44a6a1..2039f13  claude/check-dashboard-status-VNa0U -> origin/claude/check-dashboard-status-VNa0U
Updating b44a6a1..2039f13
Fast-forward
 PAPER_TO_LIVE_CHECKLIST.md               | 477 ++++++++++++++++++++++++++++++++
 deploy_bug_fixes.sh                      | 185 +++++++++++++
 docs/critical/BOT_PROCESS_VERIFICATION.md | 201 +++++++++++++
 3 files changed, 860 insertions(+)
```

---

### Step 4: Execute Part A (Fix Buy-Dip Bots)

```bash
bash fix_buy_dip_bots.sh
```

**This script will**:
1. Stop current bot
2. Backup data
3. Switch to correct branch
4. Verify fixes are present
5. Restart bot
6. Show logs

**Wait for**:
```
✅ PART A COMPLETE
```

**Verification**:
```bash
# Watch logs for confirmation
tail -f logs/bot.log

# Look for:
# ✅ Binance latency: 2ms (Excellent)
# ✅ [A/B TEST] Bypassing confluence check for Buy-Dip-X.X%
```

Press `Ctrl+C` to exit log viewing.

---

### Step 5: Execute Part B (Deploy Dashboard)

```bash
bash deploy_enterprise_dashboard.sh
```

**This script will**:
1. Check/install Node.js (if missing)
2. Check/install PostgreSQL (if missing)
3. Setup backend API
4. Setup frontend UI
5. Configure firewall
6. Start both services

**Wait for**:
```
✅ DEPLOYMENT COMPLETE!
```

**This takes 20-30 minutes** (mostly npm install and build).

---

## 🌐 Access Your Dashboard

After Part B completes, you'll see:

```
🌐 Access Your Dashboard:

   Web Interface: http://YOUR_VPS_IP:3000
   API Documentation: http://YOUR_VPS_IP:8000/docs

🔐 First Login:

   Email:    admin@cryptobot.local
   Password: change_me_immediately
```

**Action Required**:
1. Open browser
2. Go to `http://YOUR_VPS_IP:3000`
3. Login with credentials above
4. **IMMEDIATELY change password**

---

## ✅ Verification Checklist

### Part A Success:
- [ ] Bot running (check with `ps aux | grep run_bot`)
- [ ] Logs show latency <100ms (not 2142ms)
- [ ] A/B test bypass messages in logs
- [ ] No "Confluence Reject" messages when dips detected

### Part B Success:
- [ ] Can access dashboard at `http://VPS_IP:3000`
- [ ] Can login successfully
- [ ] Dashboard shows bot status
- [ ] Can see trade history
- [ ] Bot control buttons work (start/stop/restart)
- [ ] Portfolio chart displays
- [ ] No error messages in UI

---

## 📝 Useful Commands After Deployment

### Monitor Bot
```bash
# Watch bot logs live
tail -f ~/cryptobot_v3/logs/bot.log

# Quick status check
cd ~/cryptobot_v3 && python3 status.py

# Full readiness check
cd ~/cryptobot_v3 && python3 check_live_readiness.py
```

### Monitor Dashboard Services
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl -I http://localhost:3000

# View backend logs
tail -f ~/cryptobot_v3/enterprise/backend/logs/backend.log

# View frontend logs
tail -f ~/cryptobot_v3/enterprise/frontend/logs/frontend.log
```

### Check Running Processes
```bash
# Check all services
ps aux | grep -E "run_bot|main.py|next"

# Bot PID
pgrep -f run_bot.py

# Backend PID
pgrep -f main.py

# Frontend PID
pgrep -f "next start"
```

### Stop Services (If Needed)
```bash
# Stop bot
pkill -f run_bot.py

# Stop backend
pkill -f main.py

# Stop frontend
pkill -f "next start"
```

### Restart Services
```bash
# Restart bot only
cd ~/cryptobot_v3
nohup python3 run_bot.py > logs/bot.log 2>&1 &

# Restart dashboard (both backend + frontend)
cd ~/cryptobot_v3
bash deploy_enterprise_dashboard.sh
```

---

## 🚨 Troubleshooting

### Issue: Part A script fails with "git: command not found"
**Solution**:
```bash
sudo apt update && sudo apt install -y git
```

### Issue: Part A shows "⚠️ A/B test bypass not found"
**Solution**:
```bash
# Verify branch
git branch --show-current

# Should show: claude/check-dashboard-status-VNa0U
# If not, manually switch:
git checkout claude/check-dashboard-status-VNa0U
git pull origin claude/check-dashboard-status-VNa0U
```

### Issue: Part B fails "Node.js not found"
**Solution** (manual install):
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version  # Verify
```

### Issue: Part B fails "PostgreSQL not found"
**Solution** (manual install):
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Issue: Dashboard shows blank page
**Solution**:
```bash
# Check if services running
ps aux | grep -E "main.py|next"

# Check frontend logs
tail -100 ~/cryptobot_v3/enterprise/frontend/logs/frontend.log

# Rebuild if needed
cd ~/cryptobot_v3/enterprise/frontend
npm run build
npm start
```

### Issue: Can't login to dashboard
**Solution**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Should return: {"status":"ok"}

# If not, check backend logs
tail -100 ~/cryptobot_v3/enterprise/backend/logs/backend.log

# Restart backend
cd ~/cryptobot_v3/enterprise/backend
nohup python3 main.py > logs/backend.log 2>&1 &
```

### Issue: Port 3000 or 8000 not accessible from browser
**Solution**:
```bash
# Check firewall
sudo ufw status

# Open ports if needed
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Check cloud provider security groups (AWS/GCP/Azure/Hostinger)
# Ensure ports 3000 and 8000 are open to your IP
```

---

## 📊 What's Next After Deployment

### Immediate (Today):
1. ✅ Execute Part A & B (you're doing this now)
2. ✅ Login to dashboard and change password
3. ✅ Verify bot is trading (watch for dip executions)
4. ✅ Familiarize yourself with dashboard UI

### This Week:
1. Monitor A/B test results (32 hours remaining of 72h test)
2. Work on safe MVPs from `PAPER_TO_LIVE_CHECKLIST.md`:
   - API key preparation
   - Capital allocation planning
   - Telegram alerts setup
   - Emergency procedures documentation

### After 72h Test (Day 3):
1. Analyze A/B test results
2. Choose winning dip threshold
3. Apply remaining bug fixes (ATR, regime_state, position limit)
4. Paper test with fixes for 24h

### Week 2+:
- Follow timeline in `PAPER_TO_LIVE_CHECKLIST.md`
- Production hardening
- Pre-live prep
- Gradual live trading rollout (10% → 100% over 7 days)

---

## 📚 Reference Documents

All in `/root/cryptobot_v3/`:

- **This Guide**: `DEPLOYMENT_QUICK_START.md` ⭐ (you are here)
- **Go-Live Checklist**: `PAPER_TO_LIVE_CHECKLIST.md` (477 lines)
- **AI Handover**: `docs/AI_HANDOVER.md` (1617 lines, comprehensive history)
- **Dashboard Analysis**: `ENTERPRISE_DASHBOARD_COMPLETE_ANALYSIS.md`
- **Monitoring Guide**: `MONITORING_GUIDE.md`
- **VPS Commands**: `QUICK_VPS_COMMANDS.md`

---

## 🎯 Success Metrics

By the end of today, you should have:

- ✅ Bot running on correct branch
- ✅ Latency showing ~2-100ms
- ✅ Buy-Dip bots executing trades (not skipped)
- ✅ Web dashboard accessible
- ✅ Can control bot from browser (no SSH needed)
- ✅ Can view trades, portfolio, performance in UI

**Congratulations! You'll have a professional web interface for your crypto trading bot.** 🎉

---

## 📞 Support

If you encounter issues:

1. Check logs (bot, backend, frontend)
2. Review troubleshooting section above
3. Check `docs/AI_HANDOVER.md` for detailed context
4. Verify all prerequisites are installed

---

**Last Updated**: 2026-01-22
**Git Commit**: 2039f13
**Branch**: claude/check-dashboard-status-VNa0U
**Status**: ✅ Ready to Execute
