# ⚡ Quick VPS Commands

## 🚀 ONE-COMMAND DEPLOYMENT

```bash
cd ~/cryptobot_v3 && bash deploy_update.sh
```

This will:
1. Stop the bot
2. Backup data
3. Pull latest code
4. Test monitoring tools
5. Restart bot
6. Verify it's running

---

## 🧪 ONE-COMMAND TESTING (Without Restart)

```bash
cd ~/cryptobot_v3 && bash test_deployment.sh
```

This will test everything without stopping/restarting the bot.

---

## 📋 MANUAL STEP-BY-STEP

### 1. Deploy Update
```bash
# Go to directory
cd ~/cryptobot_v3

# Stop bot
pkill -f run_bot.py

# Backup data
cp -r data/ data_backup_$(date +%Y%m%d)/

# Pull latest code
git fetch origin
git checkout claude/check-dashboard-status-VNa0U
git pull

# Restart bot
nohup python3 run_bot.py > logs/bot.log 2>&1 &

# Check it's running
ps aux | grep run_bot.py
```

### 2. Quick Status Check
```bash
cd ~/cryptobot_v3
python3 status.py
```

### 3. Latency Test
```bash
cd ~/cryptobot_v3
python3 monitor_binance_latency.py -s 10
```

### 4. Full Readiness Check
```bash
cd ~/cryptobot_v3
python3 check_live_readiness.py
```

### 5. Watch Logs
```bash
cd ~/cryptobot_v3
tail -f logs/bot.log
```

### 6. Check Bot Process
```bash
ps aux | grep run_bot.py
```

### 7. Kill Bot (Emergency)
```bash
pkill -f run_bot.py
```

---

## 🔍 VERIFICATION CHECKLIST

After deployment, verify:

```bash
# 1. Check bot is running
ps aux | grep run_bot.py

# 2. Check recent logs
tail -50 ~/cryptobot_v3/logs/bot.log

# 3. Look for the latency fix (should show low ms, not 2142ms)
grep "Binance latency:" ~/cryptobot_v3/logs/bot.log | tail -1

# 4. Check open positions
sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db "SELECT symbol, ROUND(unrealized_pnl_pct,2) as pnl_pct FROM positions WHERE status='OPEN';"

# 5. Run status check
cd ~/cryptobot_v3 && python3 status.py
```

**Expected Results:**
- ✅ Bot process running
- ✅ Logs show: "✅ Binance latency: 2ms (Excellent)"
- ✅ No errors in recent logs
- ✅ Positions still tracked correctly
- ✅ Monitoring tools work

---

## ⚠️ TROUBLESHOOTING

### Bot won't start
```bash
cd ~/cryptobot_v3
tail -100 logs/bot.log
# Look for Python errors
```

### Monitoring tools fail
```bash
cd ~/cryptobot_v3
python3 -c "from core.engine import TradingEngine; print('✅ Imports OK')"
```

### Latency still showing high
```bash
# Test actual network latency
ping -c 10 api.binance.com

# Run monitoring tool
cd ~/cryptobot_v3
python3 monitor_binance_latency.py -s 10
```

### Need to rollback
```bash
cd ~/cryptobot_v3
pkill -f run_bot.py
git checkout d45ed79  # Previous commit
nohup python3 run_bot.py > logs/bot.log 2>&1 &
```

---

## 📊 MONITORING SCHEDULE

### Daily (30 seconds)
```bash
cd ~/cryptobot_v3 && python3 status.py
```

### Weekly (2 minutes)
```bash
cd ~/cryptobot_v3
python3 monitor_binance_latency.py -s 20
python3 check_live_readiness.py
```

### On-Demand (When needed)
```bash
# Watch logs live
tail -f ~/cryptobot_v3/logs/bot.log

# Check specific bot performance
sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db "SELECT strategy, COUNT(*) as trades, ROUND(SUM(pnl),2) as total_pnl FROM trades GROUP BY strategy;"
```

---

## 💾 BACKUP COMMANDS

### Manual backup before changes
```bash
cd ~/cryptobot_v3
cp -r data/ ~/backups/data_$(date +%Y%m%d_%H%M%S)/
```

### Restore from backup
```bash
cd ~/cryptobot_v3
pkill -f run_bot.py
cp -r ~/backups/data_YYYYMMDD_HHMMSS/* data/
nohup python3 run_bot.py > logs/bot.log 2>&1 &
```

---

## 🎯 WHAT TO LOOK FOR

### ✅ Good Signs
- Logs show: "✅ Binance latency: 2ms (Excellent)"
- Bot reports open positions correctly
- No Python errors in logs
- Monitoring tools work
- PnL tracking accurate

### ⚠️ Warning Signs
- Latency > 500ms (but should be ~2ms)
- Errors in logs
- Bot not running
- Monitoring tools fail

### ❌ Bad Signs
- Latency > 2000ms (indicates fix didn't apply)
- Python import errors
- Database errors
- Bot crashes on startup

---

## 📞 QUICK REFERENCE

```bash
# Deploy update
cd ~/cryptobot_v3 && bash deploy_update.sh

# Just test (no restart)
cd ~/cryptobot_v3 && bash test_deployment.sh

# Quick status
cd ~/cryptobot_v3 && python3 status.py

# Watch logs
tail -f ~/cryptobot_v3/logs/bot.log

# Stop bot
pkill -f run_bot.py

# Start bot
cd ~/cryptobot_v3 && nohup python3 run_bot.py > logs/bot.log 2>&1 &

# Check if running
ps aux | grep run_bot.py
```

---

**Most Important:** Look for "✅ Binance latency: 2ms (Excellent)" in startup logs to confirm fix worked!
