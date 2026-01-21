# 🚀 DEPLOYMENT LOG - Critical Bot Fixes
## B's CRYPTO Wealth Generating BOTS

**Deployment Date**: 2026-01-21 10:42 UTC+8
**Deployment Engineer**: Senior Full Stack Developer
**Status**: 🟢 IN PROGRESS
**Approval**: User approved all critical fixes

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Approvals Received
- [x] Kill old bot at `/Antigravity/antigravity/scratch/crypto_trading_bot/` (EXTRA CAREFUL)
- [x] Deploy position limit fix (5→30) to SAME branch (DON'T create new)
- [x] Lower Confluence threshold if needed (for testing)
- [x] Proceed step-by-step with full documentation

### ✅ Safety Constraints
- [x] Must not break expected behavior
- [x] Allow bots to continue testing
- [x] Deploy to SAME branch (no new branches)
- [x] Document everything clearly

---

## 🎯 DEPLOYMENT STEPS

### **STEP 1: Verify Old Bot Process** ⏳ IN PROGRESS

**Objective**: Identify which bot is OLD and which is NEW, verify safe to kill

**Commands to Run on VPS**:
```bash
# 1. Check both bot processes
ps aux | grep run_bot

# 2. Check logs of BOTH bots to verify which is active
tail -50 /root/cryptobot_v3/bot.log | head -20
tail -50 /Antigravity/antigravity/scratch/crypto_trading_bot/bot.log | head -20

# 3. Check which bot is writing to database
lsof | grep -E "trades.*db" | grep python

# 4. Verify NEW bot path and branch
cd /root/cryptobot_v3
pwd
git branch
git log -1 --oneline
```

**Expected Results**:
- NEW bot: `/root/cryptobot_v3/` on branch with A/B test code
- OLD bot: `/Antigravity/antigravity/scratch/crypto_trading_bot/` on old branch
- Database access: Should show which process is writing

**Safety Verification**:
- ✅ Verify OLD bot has older log entries
- ✅ Verify NEW bot has A/B test messages in logs
- ✅ Confirm PID to kill

**Status**: 🟡 AWAITING VPS EXECUTION

---

### **STEP 2: Kill Old Bot (CAREFULLY)** ⏸️ PENDING

**Objective**: Terminate OLD bot process without affecting NEW bot

**Pre-Kill Verification**:
```bash
# Verify PID before killing
ps aux | grep [OLD_BOT_PID]

# Double-check it's the OLD path
ps aux | grep [OLD_BOT_PID] | grep "/Antigravity/antigravity/scratch"
```

**Kill Command** (ONLY after verification):
```bash
# Graceful shutdown first
kill -SIGTERM [OLD_BOT_PID]

# Wait 10 seconds
sleep 10

# Verify it stopped
ps aux | grep [OLD_BOT_PID]

# Force kill if still running
kill -9 [OLD_BOT_PID]
```

**Post-Kill Verification**:
```bash
# Verify only ONE bot running
ps aux | grep run_bot | grep -v grep
# Should show only /root/cryptobot_v3/

# Check NEW bot still running
tail -f /root/cryptobot_v3/bot.log
```

**Status**: ⏸️ PENDING (waiting for Step 1)

---

### **STEP 3: Deploy Position Limit Fix** ⏸️ PENDING

**Objective**: Update position limit from 5 to 30 in SAME branch

**Current Branch**: Verify first
```bash
cd /root/cryptobot_v3
git branch
# Expected: claude/test-dip-bot-profit-lhCxz OR claude/review-handover-bot-performance-Rwv92
```

**Option A: If on test-dip-bot branch, cherry-pick the fix**:
```bash
cd /root/cryptobot_v3
git fetch --all

# Cherry-pick the position limit fix commit
git cherry-pick a7d40d7  # "fix: bypass position size check when portfolio value corrupted"

# Verify the change
git log -1
git diff HEAD~1
```

**Option B: If on review-handover branch, already has fix**:
```bash
# Just pull latest
git pull origin claude/review-handover-bot-performance-Rwv92

# Verify fix is present
grep -A 5 "max_concurrent_positions" core/risk_module.py
```

**Verification**:
```bash
# Check the actual value in code
grep "max_concurrent_positions.*=" core/risk_module.py | grep -v "#"
# Should show: max_concurrent_positions: int = 30
```

**Status**: ⏸️ PENDING (waiting for Step 2)

---

### **STEP 4: Lower Confluence Threshold** ⏸️ PENDING

**Objective**: Reduce Confluence V2 threshold from 75 to 20-30 for testing

**File to Edit**: `core/engine.py` or `run_bot.py` (check which has confluence threshold)

**Find Current Setting**:
```bash
cd /root/cryptobot_v3
grep -n "confluence.*threshold\|Threshold.*75" core/engine.py run_bot.py
```

**Edit to Lower Threshold**:
```bash
# Backup first
cp core/engine.py core/engine.py.backup_$(date +%Y%m%d_%H%M%S)

# Edit the file (find the line with threshold 75)
# Change to: threshold = 20  # Lowered for testing phase
```

**Status**: ⏸️ PENDING (waiting for Step 3)

---

### **STEP 5: Restart Bot** ⏸️ PENDING

**Objective**: Restart bot with all fixes applied

**Restart Commands**:
```bash
cd /root/cryptobot_v3

# Stop current bot
pkill -f "python3 run_bot.py"

# Wait 5 seconds
sleep 5

# Verify stopped
ps aux | grep run_bot

# Start bot in background
nohup python3 run_bot.py > bot.log 2>&1 &

# Get new PID
echo $!

# Verify started
ps aux | grep run_bot
```

**Post-Restart Verification**:
```bash
# Check logs for startup
tail -50 bot.log

# Verify no position limit errors after 5 minutes
sleep 300
grep "Maximum concurrent positions" bot.log | tail -5
# Should show NO new errors or limit=30

# Verify trading activity
grep -E "BUY|SELL" bot.log | tail -10
```

**Status**: ⏸️ PENDING (waiting for Step 4)

---

### **STEP 6: Monitor and Verify** ⏸️ PENDING

**Objective**: Verify all fixes working and trading resumed

**Monitoring Commands** (1 hour after restart):
```bash
# Check for position limit errors
grep "Maximum concurrent positions" bot.log | tail -20
# Should show: (5) before restart, none after

# Check for confluence blocks
grep "Confluence V2 Reject" bot.log | tail -20
# Should show: fewer rejections with lower threshold

# Check for new trades
python3 check_all_bots.py
# Compare trade counts before/after

# Check specific bot performance
sqlite3 data/multi/trades_paper.db "SELECT bot_name, COUNT(*) as trades, datetime('now') as checked FROM trades GROUP BY bot_name;"
```

**Success Criteria**:
- ✅ Position limit errors gone (or showing limit=30)
- ✅ New trades executing (BUY/SELL in logs)
- ✅ Confluence acceptance rate improved
- ✅ Total trade count increasing

**Status**: ⏸️ PENDING (waiting for Step 5)

---

## 📊 DEPLOYMENT RESULTS

### Before Deployment:
- Position limit: 5 (blocking all trades)
- Confluence: 100% rejection (threshold 75)
- Old bot: Running (potential conflicts)
- Trading activity: STALLED ❌

### After Deployment:
- Position limit: TBD ⏸️
- Confluence: TBD ⏸️
- Old bot: TBD ⏸️
- Trading activity: TBD ⏸️

---

## 🚨 ROLLBACK PLAN (If Needed)

If anything goes wrong:

```bash
# Stop current bot
pkill -f "python3 run_bot.py"

# Restore backup
cd /root/cryptobot_v3
git reset --hard HEAD~1  # If changes committed
cp core/engine.py.backup_* core/engine.py  # If file edited

# Restart with old config
nohup python3 run_bot.py > bot.log 2>&1 &
```

---

## 📝 DEPLOYMENT NOTES

**Timestamp**: 2026-01-21 10:42 UTC+8
**Status**: Step 1 in progress - verifying old bot process
**Next Action**: Execute VPS commands to verify bot processes

---

**Deployment Log Status**: 🟢 ACTIVE
**Last Updated**: 2026-01-21 10:42 UTC+8
