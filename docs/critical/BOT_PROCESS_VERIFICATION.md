# 🔍 Bot Process Verification Guide
## B's CRYPTO Wealth Generating BOTS

**Created**: 2026-01-21 10:57 UTC+8
**Purpose**: Safely identify which bot to keep and which to kill

---

## 📊 CURRENT PROCESSES (VPS Output)

```
root      683195  0.2  3.7 637456 307204 ?       Sl   Jan20   1:44 python3 run_bot.py
root      683206  0.0  3.7 636112 306008 ?       Ssl  Jan20   0:30 /usr/bin/python3 -u /Antigravity/antigravity/scratch/crypto_trading_bot/run_bot.py
```

### Analysis:

| PID | Command | Path | Started | CPU % | Memory | Status |
|-----|---------|------|---------|-------|--------|--------|
| **683195** | `python3 run_bot.py` | Likely `/root/cryptobot_v3` | Jan 20 | 0.2% | 307 MB | 🟢 RUNNING |
| **683206** | `/usr/bin/python3 -u ...run_bot.py` | `/Antigravity/antigravity/scratch/crypto_trading_bot/` | Jan 20 | 0.0% | 306 MB | 🟡 OLD PATH |

---

## 🎯 VERIFICATION COMMANDS (Run on VPS)

### **Step 1: Verify PID 683195 (Likely NEW bot)**

```bash
# Get working directory of PID 683195
sudo pwdx 683195

# Expected: /root/cryptobot_v3
```

### **Step 2: Check which branch PID 683195 is using**

```bash
# Navigate to its directory
cd /root/cryptobot_v3

# Check current branch
git branch

# Expected: * claude/test-dip-bot-profit-lhCxz (with A/B test code)

# Check recent log
tail -30 bot.log | grep -E "Buy-Dip-5.2%|Buy-Dip-5.5%|Buy-Dip-8.0%"

# Expected: Should see A/B test bot names
```

### **Step 3: Verify PID 683206 (OLD bot)**

```bash
# Get working directory of PID 683206
sudo pwdx 683206

# Expected: /Antigravity/antigravity/scratch/crypto_trading_bot
```

### **Step 4: Check which database each bot is using**

```bash
# Check database access for PID 683195
sudo lsof -p 683195 | grep "\.db"

# Expected: /root/cryptobot_v3/data/multi/trades_paper.db

# Check database access for PID 683206
sudo lsof -p 683206 | grep "\.db"

# Expected: /Antigravity/antigravity/scratch/.../data/multi/trades_paper.db
```

### **Step 5: Compare recent log activity**

```bash
# Check NEW bot logs (PID 683195)
tail -20 /root/cryptobot_v3/bot.log

# Should see: Recent activity with A/B test bots

# Check OLD bot logs (PID 683206)  
tail -20 /Antigravity/antigravity/scratch/crypto_trading_bot/bot.log

# Might see: Older entries or errors
```

---

## ✅ IDENTIFICATION RESULTS

Based on the above commands, fill in:

**PID 683195**:
- Working directory: `_________________`
- Git branch: `_________________`
- Last log entry time: `_________________`
- Has A/B test bots?: YES / NO

**PID 683206**:
- Working directory: `_________________`
- Git branch: `_________________`
- Last log entry time: `_________________`
- Is OLD path?: YES / NO

---

## 🎯 DECISION MATRIX

### **If PID 683195 shows**:
- ✅ Working dir: `/root/cryptobot_v3`
- ✅ Branch: `claude/test-dip-bot-profit-lhCxz`
- ✅ Logs show: Buy-Dip-5.2%, Buy-Dip-5.5%, Buy-Dip-8.0%
- ✅ Recent log entries (within last hour)

**→ KEEP PID 683195 (This is the NEW bot)**

### **If PID 683206 shows**:
- ✅ Working dir: `/Antigravity/antigravity/scratch/crypto_trading_bot/`
- ✅ Old path confirmed
- ✅ Different database

**→ KILL PID 683206 (This is the OLD bot)**

---

## 🔪 SAFE KILL COMMANDS (Only After Verification)

### **BEFORE KILLING - Final Check**:
```bash
# Verify PID 683206 is NOT the active trader
# Check if it's made any trades in last hour
sudo lsof -p 683206 | grep "\.db"
# Note the database path

# Check that database for recent activity
sqlite3 [DATABASE_PATH] "SELECT MAX(timestamp) FROM trades;"
# If old timestamp (not in last hour) → Safe to kill
```

### **Kill OLD Bot (PID 683206)**:
```bash
# Graceful shutdown
kill -SIGTERM 683206

# Wait 10 seconds
sleep 10

# Verify stopped
ps -p 683206
# Should show: no process found

# If still running, force kill
kill -9 683206
```

### **Verify Only NEW Bot Remains**:
```bash
# Check bot processes
ps aux | grep run_bot | grep -v grep

# Should show ONLY PID 683195
```

---

## 🚨 SAFETY CHECKS

### **RED FLAGS - DO NOT KILL if you see**:
- ❌ PID 683195 is NOT in `/root/cryptobot_v3`
- ❌ PID 683195 does NOT have A/B test bot names in logs
- ❌ PID 683206 has very recent trades (last 10 minutes)
- ❌ Only ONE process running total

### **GREEN LIGHTS - SAFE TO KILL if you verify**:
- ✅ PID 683195 confirmed as NEW bot in `/root/cryptobot_v3`
- ✅ PID 683195 has A/B test bot names in recent logs
- ✅ PID 683206 confirmed as OLD path bot
- ✅ PID 683206 not writing to database recently

---

## 📋 EXECUTION CHECKLIST

- [ ] Run Step 1: Get working directory of PID 683195
- [ ] Run Step 2: Check branch and logs for PID 683195
- [ ] Run Step 3: Get working directory of PID 683206
- [ ] Run Step 4: Check database access for both PIDs
- [ ] Run Step 5: Compare log activity
- [ ] ✅ Confirm PID 683195 = NEW bot
- [ ] ✅ Confirm PID 683206 = OLD bot
- [ ] Kill PID 683206 (OLD bot)
- [ ] Verify only PID 683195 remains

---

**Status**: ⏸️ AWAITING VERIFICATION
**Next**: Run verification commands and share results before killing anything
