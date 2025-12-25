# 🚀 DEPLOYMENT CHECKLIST - Refined Parameters

**Status: READY TO DEPLOY** ✅

---

## 📦 Files Ready for Deployment

### Modified Files:
- ✅ `core/logger.py` - P&L calculation fix
- ✅ `run_bot.py` - Refined parameters (PENDING - see below)

### New Files Created:
- ✅ `reset_losing_bots_only.py` - Selective reset script
- ✅ `daily_bot_check.py` - Daily performance tracker
- ✅ `backtest_hold_days.py` - Backtest optimal hold times
- ✅ `verify_pnl_fix.py` - P&L verification
- ✅ `STOP_LOSING_BOTS.md` - Bot shutdown guide

---

## 🎯 Refined Parameters Summary

### Grid Bots (SCALE UP - Priority #1)
```
Allocation: $6,000 (was $2,000)
Grid Bot BTC: $3,000
Grid Bot ETH: $3,000
Parameters: Keep EXACTLY as-is (already working!)
Expected Monthly: +$7,200
```

### SMA Trend Bot (Optimize - Priority #2)
```
Allocation: $4,000
SMA Fast: 20
SMA Slow: 50
Take Profit: 10%
Stop Loss: -3%
Trailing Stop: 4% (activates at +6%)
Max Hold: 21 days
Expected Monthly: +$320
```

### Buy-the-Dip (Test - Priority #3)
```
Allocation: $3,000
Position: Start $25, scale to $200
Take Profit: 6%
Stop Loss: -4%
Trend Filters: 7-day & 21-day SMA
Cooldown: 6h after win, 48h after loss
Max Hold: 60 days (backtest to optimize)
Max Daily Trades: 3
Circuit Breaker: -$100 daily / -$300 weekly
Expected Monthly: +$150 (if profitable)
```

### Momentum Swing (**HOLD** - Paper trade first)
```
Allocation: $1,000 (smallest - unproven)
Position: $150 fixed
Take Profit: 10%
Stop Loss: -4%
Max Hold: 12 days
Coins: BTC, ETH only
Expected Monthly: +$60 (if it works)
```

---

## 🚦 DEPLOYMENT SEQUENCE

### Phase 1: Local Testing (15 min)
```bash
cd c:\CryptoBot_Project

# Run backtest
python backtest_hold_days.py

# Test daily tracker (should work even with no recent trades)
python daily_bot_check.py
```

### Phase 2: Git Workflow (10 min)
```bash
# Stage files
git add core/logger.py
git add reset_losing_bots_only.py
git add daily_bot_check.py
git add backtest_hold_days.py
git add verify_pnl_fix.py
git add STOP_LOSING_BOTS.md

# Note: run_bot.py will be updated with refined parameters AFTER backtest results

# Commit  
git commit -m "feat: P&L fix + monitoring tools + backtest framework"

# Push
git push origin main
```

### Phase 3: VPS Deployment (20 min)
```bash
# SSH to VPS
ssh [user]@[vps-ip]
cd /Antigravity/antigravity/scratch/crypto_trading_bot

# Pull code
git pull origin main

# Run backtest to determine optimal hold days
python3 backtest_hold_days.py

# Run selective reset (CREATES BACKUP FIRST!)
python3 reset_losing_bots_only.py

# Restart bots with new code
pm2 restart crypto-bot
pm2 restart dashboard

# Verify
pm2 logs crypto-bot --lines 50
```

### Phase 4: Daily Monitoring
```bash
# Every morning:
python3 daily_bot_check.py
```

---

## ⚠️ HOLD - run_bot.py Not Yet Updated

**WHY:** We need backtest results first to set optimal max_hold_days.

**NEXT:** After backtest shows optimal hold period (likely 14-30 days):
1. Update run_bot.py with refined parameters
2. Commit updated run_bot.py
3. Pull on VPS
4. Restart bots

**This ensures DATA-DRIVEN parameter selection, not guesswork.**

---

## ✅ What You Can Do RIGHT NOW

1. **Test scripts locally:**
   ```bash
   python daily_bot_check.py
   python backtest_hold_days.py
   ```

2. **Review parameters** - Make sure you agree with allocations

3. **When ready to deploy:**
   - Run backtest first
   - Use results to finalize run_bot.py
   - Then full deployment

---

## 🎯 Expected Timeline

- **Today:** Backtest + review results
- **Tomorrow:** Update run_bot.py with optimal params
- **Day 3:** Deploy to VPS
- **Week 1:** Monitor daily with daily_bot_check.py
- **Week 2:**  Scale up if profitable

---

## 📞 Emergency Contact

If something breaks:
1. Check `pm2 logs crypto-bot`
2. Restore backup: `backups/trades_v3_paper_BEFORE_RESET_[timestamp].db`
3. Rollback Git: `git reset --hard HEAD~1`

---

**Status: Scripts ready. Waiting for backtest results to finalize run_bot.py** ✅
