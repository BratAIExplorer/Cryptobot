# VPS Deployment Guide for Luno Monitor Fixes

## Files Changed
All files are in `c:\CryptoBot_Project\luno-monitor\`:
- `src/currency_converter.py` - Fixed ZAR → MYR conversion
- `config.py` - Updated trading pairs to ZAR
- `main.py` - Added alert cooldown system
- `dip_monitor.py` - Updated alert messaging
- `dip_monitor_config.py` - Changed thresholds to 15%/50%
- `alert_state_manager.py` - Already exists (alert cooldown tracking)

## Quick VPS Deployment (Recommended)

### Option 1: Use Deployment Script (Easiest)
```bash
# From Git Bash or WSL
cd /c/CryptoBot_Project/luno-monitor
bash deploy_to_vps.sh
```

This script will:
1. Create backups on VPS
2. Upload all fixed files
3. Restart both monitors
4. Verify they're running

---

## Option 2: Manual Deployment

### Step 1: SSH to VPS
```bash
ssh root@srv1010193
```

### Step 2: Navigate to Luno Monitor
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor
```

### Step 3: Backup Current Files
```bash
cp config.py config.py.backup
cp src/currency_converter.py src/currency_converter.py.backup
cp main.py main.py.backup
```

### Step 4: Upload Files from Local Machine

**Open a NEW terminal on your local Windows machine:**

```bash
# From Git Bash or PowerShell
cd c:\CryptoBot_Project\luno-monitor

# Upload currency converter
scp src/currency_converter.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/src/

# Upload config
scp config.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/

# Upload main monitor
scp main.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/

# Upload alert state manager
scp alert_state_manager.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/

# Upload dip monitor files
scp dip_monitor.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/
scp dip_monitor_config.py root@srv1010193:/Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/
```

### Step 5: Restart Monitors (Back on VPS)

**In your VPS SSH session:**

```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor

# Stop existing processes
pkill -f 'python.*main.py'
pkill -f 'python.*dip_monitor.py'

# Wait for clean shutdown
sleep 2

# Start Portfolio Monitor
nohup python3 main.py > luno_monitor.log 2>&1 &

# Start Dip Monitor  
nohup python3 dip_monitor.py > dip_monitor.log 2>&1 &

# Verify processes are running
ps aux | grep 'python.*main.py'
ps aux | grep 'python.*dip_monitor.py'
```

### Step 6: Monitor Logs
```bash
# Watch Portfolio Monitor
tail -f luno_monitor.log

# Watch Dip Monitor
tail -f dip_monitor.log
```

**Look for:**
- ✅ "Updated exchange rate: 1 ZAR = 0.24XX MYR"
- ✅ "Alert cooldown manager initialized"
- ✅ Prices in RM format (should be ~4x lower than before)
- ✅ "⏳ Skipping alert (cooldown)" messages

---

## Verification Checklist

After deployment, verify:

### 1. Currency Conversion Working
```bash
# On VPS, check the log
tail -20 luno_monitor.log
```
**Look for:** Exchange rate message showing ~0.24 MYR per ZAR

### 2. Prices Are Correct
**Check next email alert:**
- XRP should show **~RM 8-9** (not RM 33)
- BTC should show **~RM 370,000** (not RM 1.5M)

### 3. No Duplicate Alerts
**Monitor your email:**
- Should only get ONE email per alert within cooldown period
- Subsequent triggers show in log as "Skipping (cooldown)"

### 4. New Buying Thresholds Active
**Dip Monitor alerts trigger at:**
- Tier 1: 15% drop (was 10%)
- Tier 2: 50% drop (was 20%)

---

## Troubleshooting

### If monitors didn't start:
```bash
# Check for errors
cat luno_monitor.log
cat dip_monitor.log

# Try running in foreground to see errors
python3 main.py
```

### If prices still wrong:
```bash
# Check exchange rate in log
grep "exchange rate" luno_monitor.log

# Manually verify config
cat config.py | grep ZAR
```

### If still getting duplicates:
```bash
# Check alert state file exists
ls -la alert_state.json

# View cooldown state
cat alert_state.json
```

---

## Expected Behavior After Fix

### Email Notifications Will Show:
```
🎯 XRP Profit Target Reached!
Cryptocurrency: XRP
Target Price: RM 13.23
Current Price: RM 8.35  ← Correct MYR price!
```

### Console Output Will Show:
```
✓ Updated exchange rate: 1 ZAR = 0.2430 MYR
Portfolio Value: RM 2,450.00 (+12.5%)
⏳ Skipping XRP 25% alert (cooldown)  ← No duplicates!
```

---

## Quick Commands Reference

```bash
# SSH to VPS
ssh root@srv1010193

# Check if monitors running
ps aux | grep python

# View live logs
tail -f /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/luno_monitor.log

# Restart monitors
cd /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor
pkill -f 'python.*main.py' && nohup python3 main.py > luno_monitor.log 2>&1 &
pkill -f 'python.*dip_monitor.py' && nohup python3 dip_monitor.py > dip_monitor.log 2>&1 &

# Check status
ps aux | grep 'main.py\|dip_monitor'
```
