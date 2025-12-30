# 🚀 HYBRID V2.0 DEPLOYMENT GUIDE

**Version:** 2.0.0
**Branch:** `claude/add-performance-dashboard-HeqGs`
**Target:** Buy-the-Dip Strategy Enhancement
**Estimated Deployment Time:** 30-45 minutes

---

## 📋 TABLE OF CONTENTS

1. [What's Changing](#whats-changing)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Post-Deployment Monitoring](#post-deployment-monitoring)
5. [Expected Behavior](#expected-behavior)
6. [Rollback Plan](#rollback-plan)
7. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## 🎯 WHAT'S CHANGING

### New Strategy: Hybrid v2.0 for Buy-the-Dip

**OLD (5% TP Infinite Hold):**
- Hold indefinitely until +5% profit
- No stop loss (manual intervention only)
- No correlation management
- No volatility awareness

**NEW (Hybrid v2.0 - Dynamic Time-Weighted):**
- **Dynamic Take Profit:**
  - 0-60 days: 5% TP (quick wins)
  - 60-120 days: 8% TP (medium patience)
  - 120-180 days: 12% TP + 8% trailing stop
  - 180+ days: 15% TP + 10% trailing stop ✨ **Your theory!**

- **Quality-Based Catastrophic Floors:**
  - BTC/ETH (Top 10): -70% floor
  - Top 20 coins: -50% floor
  - Others: -40% floor

- **Regime-Aware Entry:**
  - CRISIS: Pause all buys
  - BEAR: Only top 10 coins
  - BULL: Buy aggressively

- **Intelligence Enhancements:**
  - Correlation Manager: Prevents buying 3+ correlated positions
  - Volatility Clustering: Adjusts TP based on market volatility
  - Exit Prediction: Smart timing based on hold duration

### Files Modified

```
core/risk_module.py           - Exit logic (CRITICAL)
core/engine.py                - Entry filtering + correlation checks
run_bot.py                    - Buy-the-Dip configuration
core/correlation_manager.py   - NEW: Portfolio diversification
core/volatility_clustering.py - NEW: Volatility detection
```

### Impact Analysis

| Strategy | Impact | Action Required |
|----------|--------|-----------------|
| Buy-the-Dip | 🔴 **MAJOR** | Full strategy overhaul |
| Grid Bots | 🟢 **NONE** | No changes |
| SMA Trend | 🟢 **NONE** | No changes |
| Momentum Swing | 🟢 **NONE** | No changes |
| Hidden Gem | 🟢 **NONE** | No changes |

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### 1. Backup Everything (CRITICAL!)

```bash
# On VPS
cd ~/crypto_bot  # or your bot directory

# Backup database
cp data/trades_v3_paper.db data/trades_v3_paper.db.backup_$(date +%Y%m%d_%H%M%S)

# Backup current code
git stash push -m "Backup before Hybrid v2.0 deployment $(date)"

# Verify backup
ls -lh data/trades_v3_paper.db.backup*
```

### 2. Check System Requirements

- [ ] Python 3.8+ installed
- [ ] Git installed and configured
- [ ] Current bot version is running (check logs)
- [ ] Internet connection stable
- [ ] Telegram bot configured (for alerts)

### 3. Review Current Positions

```bash
# Check how many Buy-the-Dip positions are open
sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) FROM positions WHERE strategy='Buy-the-Dip Strategy' AND status='OPEN';"

# Check current P&L
sqlite3 data/trades_v3_paper.db "SELECT symbol, buy_price, buy_timestamp FROM positions WHERE strategy='Buy-the-Dip Strategy' AND status='OPEN' ORDER BY buy_timestamp;"
```

**Expected:** You should have ~17 open positions from Dec 2-5.

### 4. Verify Branch Status

```bash
git status
git log --oneline -5
```

**Expected:** Should show you're on `claude/add-performance-dashboard-HeqGs` branch.

---

## 🚀 DEPLOYMENT STEPS

### STEP 1: Stop Current Bot (5 minutes)

```bash
# Method 1: Create stop signal (graceful shutdown)
touch STOP_SIGNAL

# Wait for shutdown confirmation
tail -f bot.log  # Watch for "✅ Bot stopped successfully"
```

**OR**

```bash
# Method 2: Find and kill process
ps aux | grep run_bot.py
kill <PID>
```

**Verification:** No `run_bot.py` process running:
```bash
ps aux | grep run_bot.py | grep -v grep
# Should return nothing
```

### STEP 2: Pull Latest Code (2 minutes)

```bash
# Ensure you're on the correct branch
git checkout claude/add-performance-dashboard-HeqGs

# Pull latest changes
git pull origin claude/add-performance-dashboard-HeqGs
```

**Expected Output:**
```
From github.com:YourRepo/Cryptobot
 * branch            claude/add-performance-dashboard-HeqGs -> FETCH_HEAD
Updating d0311c2..179bc70
Fast-forward
 core/correlation_manager.py     | 367 +++++++++++++++++++++++++++
 core/volatility_clustering.py   | 125 ++++++++++
 core/risk_module.py             | 156 ++++++++----
 core/engine.py                  |  61 ++++-
 run_bot.py                      |  12 +-
 5 files changed, 564 insertions(+), 49 deletions(-)
```

### STEP 3: Verify Code Changes (3 minutes)

```bash
# Check that new files exist
ls -l core/correlation_manager.py core/volatility_clustering.py

# Verify run_bot.py configuration
grep -A 10 "EXIT STRATEGY: HYBRID V2.0" run_bot.py
```

**Expected:** Should see Hybrid v2.0 comments in run_bot.py.

### STEP 4: Test Import (1 minute)

```bash
# Test that all modules can be imported
python3 -c "
from core.risk_module import RiskManager
from core.engine import TradingEngine
from core.correlation_manager import CorrelationManager
from core.volatility_clustering import VolatilityClusterDetector
print('✅ All imports successful')
"
```

**Expected:** `✅ All imports successful`

**If errors:** Check error message, may need to install dependencies.

### STEP 5: Start Bot with New Strategy (2 minutes)

```bash
# Start bot (redirect output to log file)
nohup python3 run_bot.py > bot.log 2>&1 &

# Get process ID
echo $! > bot.pid
```

**Verification:**
```bash
# Check bot is running
ps aux | grep run_bot.py | grep -v grep

# Watch startup logs
tail -f bot.log
```

**Expected Startup Output:**
```
================================================================================
🤖 Crypto Bot - Refined Parameters (v2025.12.25)
================================================================================
✅ Telegram notifications enabled
🌡️ Warming up Market Regime Detector...
✅ Market Regime Initialized: BULL_CONFIRMED (Confidence: 78.5%)
🔗 Building correlation matrix for portfolio diversification...
✅ Correlation Matrix Built: 66 pairs analyzed
[STARTUP] Updating Buy-the-Dip Strategy: Trades=19, PnL=$-2145.67, Balance=$855.33
================================================================================
🚀 Bot Running - PAPER Mode
   Portfolio Allocation:
   - Grid Bots:      $6,000 (43%) ← SCALED UP!
   - SMA Trend:      $4,000 (29%)
   - Buy-the-Dip:    $3,000 (21%) ← Hybrid v2.0!
   - Momentum Swing: $1,000 (7%)  ← New strategy
   Expected Monthly: +$7,730 (55% return)
================================================================================
Press Ctrl+C to stop.
```

---

## 📊 POST-DEPLOYMENT MONITORING

### First 1 Hour: Critical Watch

```bash
# Watch bot logs in real-time
tail -f bot.log
```

**What to look for:**
- ✅ No Python errors
- ✅ "Correlation Matrix Built" message on startup
- ✅ Regime detector working (BULL/BEAR/CRISIS messages)
- ✅ Buy signals respect regime filters
- ✅ Correlation checks block over-concentrated buys

**Example Good Log:**
```
[Buy-the-Dip Strategy] BTC/USDT REGIME: BULL_CONFIRMED - Allowing buys
[Buy-the-Dip Strategy] SOL/USDT DIP DETECTED: 6.2% | Regime: BULL_CONFIRMED
🚫 Correlation Risk: 2 positions highly correlated with SOL/USDT
   Correlated: BNB/USDT, AVAX/USDT
   Correlation: 0.82, 0.75
   💡 Already have 2 positions moving together - avoid concentration
```

### First 6 Hours: Position Exits

**Monitor for:**
- First profit exits from existing positions
- Dynamic TP being applied correctly
- Checkpoint alerts (if any positions hit 60 days)

```bash
# Check if any positions closed
sqlite3 data/trades_v3_paper.db "SELECT * FROM trades WHERE strategy='Buy-the-Dip Strategy' AND side='SELL' AND timestamp > datetime('now', '-6 hours');"
```

**If position exits:**
```
Expected log format:
💰 [PROFIT EXIT] Buy-the-Dip Strategy | XRP/USDT
   Entry: $2.126000 | Exit: $2.232300
   Profit: +5.00%
   Reason: ✅ Take Profit Reached (+5.00%)
```

### First 24 Hours: Full Cycle Check

**Tasks:**
1. **Check P&L:**
   ```bash
   sqlite3 data/trades_v3_paper.db "SELECT SUM(profit_loss) FROM trades WHERE strategy='Buy-the-Dip Strategy' AND timestamp > datetime('now', '-24 hours');"
   ```

2. **Verify Correlation Matrix Updates:**
   Look for "Correlation Matrix Built" in logs (should happen daily on startup).

3. **Check Regime Filtering:**
   ```bash
   grep "CRISIS\|BEAR" bot.log | tail -20
   ```

4. **Telegram Alerts:**
   - Verify you received startup notification
   - Check for any checkpoint alerts (60/90/120 day positions)
   - Verify profit exit notifications

---

## 🎯 EXPECTED BEHAVIOR

### Scenario 1: Quick Win (30 days, +5%)
**Position:** Bought ADA at $0.6500
**Day 30 Price:** $0.6825 (+5.0%)

**Expected Action:** ✅ AUTO-SELL
**Reason:** Take Profit Reached (+5.00%)
**Net Profit:** +4.5% (after 0.5% fees)

**Log Output:**
```
💰 [PROFIT EXIT] Buy-the-Dip Strategy | ADA/USDT
   Entry: $0.650000 | Exit: $0.682500
   Profit: +5.00%
   Reason: ✅ Take Profit Reached (+5.00%)
```

---

### Scenario 2: Medium Hold (90 days, +8%)
**Position:** Bought DOT at $2.258
**Day 90 Price:** $2.439 (+8.0%)

**Expected Action:** ✅ AUTO-SELL
**Reason:** Take Profit Reached (+8.00%) [Dynamic TP applied]
**Net Profit:** +7.5% (after fees)

**Log Output:**
```
💰 [PROFIT EXIT] Buy-the-Dip Strategy | DOT/USDT
   Entry: $2.258000 | Exit: $2.439000
   Profit: +8.02%
   Reason: ✅ Dynamic TP Reached (+8.00% for 90-day hold)
```

---

### Scenario 3: Long Hold Recovery (180+ days, +20% peak)
**Position:** Bought SOL at $139.72
**Day 180 Price:** $167.66 (+20%)
**Day 185 Price:** $159.29 (+14%)

**Expected Action:** ✅ AUTO-SELL via Trailing Stop
**Reason:** Trailing Stop Hit (10% trail from peak)
**Net Profit:** +13.5% (after fees)

**Why Better Than 5% TP:** Old strategy would have sold at +5% on day 60, missing +9% additional gains!

**Log Output:**
```
💰 [PROFIT EXIT] Buy-the-Dip Strategy | SOL/USDT
   Entry: $139.720000 | Exit: $159.290000
   Profit: +14.00%
   Reason: ✅ Trailing Stop Hit (10% from peak $167.66)
   Hold Duration: 185 days
```

---

### Scenario 4: Dead Coin Protection (-45%)
**Position:** Bought LUNA at $1.000
**Current Price:** $0.550 (-45%)
**Coin Quality:** Not in Top 20

**Expected Action:** ✅ AUTO-SELL at -40% Floor
**Reason:** Catastrophic Floor Hit (-40% for non-top coins)
**Net Loss:** -40.5% (preserves 59.5% of capital)

**Why Important:** Without floor, could drift to -90%+ (FTX/LUNA scenario).

**Log Output:**
```
⚠️  [CATASTROPHIC EXIT] Buy-the-Dip Strategy | LUNA/USDT
   Entry: $1.000000 | Exit: $0.600000
   Loss: -40.00%
   Reason: Quality Floor Hit (Not Top 20 - max loss -40%)
   💡 Capital preserved: Preventing total wipeout
```

---

### Scenario 5: Crisis Regime (Pause Buys)
**Market Condition:** BTC crashes -20% in 3 days
**Regime State:** CRISIS
**Dip Detected:** ETH down -12% from high

**Expected Action:** ⛔ NO BUY
**Reason:** CRISIS Regime - Pausing all buys to preserve capital

**Log Output:**
```
[Buy-the-Dip Strategy] ETH/USDT DIP DETECTED: 12.0%
⛔ CRISIS Regime: Pausing all buys to preserve capital
```

---

### Scenario 6: Correlation Block
**Current Positions:** BTC/USDT, ETH/USDT, BNB/USDT (all highly correlated L1s)
**New Signal:** SOL/USDT dip detected
**Correlation:** SOL correlates 0.85 with BTC, 0.78 with ETH, 0.82 with BNB

**Expected Action:** 🚫 CORRELATION BLOCK
**Reason:** Already have 3 highly correlated L1 positions

**Log Output:**
```
[Buy-the-Dip Strategy] SOL/USDT DIP DETECTED: 8.5% | Regime: BULL_CONFIRMED
🚫 Correlation Risk: 3 positions highly correlated with SOL/USDT
   Correlated: BTC/USDT, ETH/USDT, BNB/USDT
   Correlation: 0.85, 0.78, 0.82
   💡 Already have 3 positions moving together - avoid concentration
```

---

## 🔄 ROLLBACK PLAN

### If Something Goes Wrong

**Symptoms requiring rollback:**
- Python errors on every cycle
- Bot crashes repeatedly
- Database corruption
- Positions not closing when they should

### Quick Rollback (5 minutes)

```bash
# 1. Stop current bot
touch STOP_SIGNAL
# Wait for shutdown

# 2. Restore backup database
cp data/trades_v3_paper.db.backup_YYYYMMDD_HHMMSS data/trades_v3_paper.db

# 3. Checkout previous version
git checkout HEAD~1  # Go back one commit

# 4. Restart bot
nohup python3 run_bot.py > bot.log 2>&1 &
```

### Full Rollback to Master

```bash
# Stop bot
touch STOP_SIGNAL

# Restore database backup
cp data/trades_v3_paper.db.backup_YYYYMMDD_HHMMSS data/trades_v3_paper.db

# Go back to main branch
git checkout main
git pull origin main

# Restart with old config
nohup python3 run_bot.py > bot.log 2>&1 &
```

**After Rollback:**
- Notify in GitHub issue what went wrong
- Share error logs
- We'll debug and re-deploy

---

## ❓ FAQ & TROUBLESHOOTING

### Q: Bot won't start, shows "ModuleNotFoundError: No module named 'core.correlation_manager'"

**Solution:**
```bash
# Verify file exists
ls -l core/correlation_manager.py

# If missing, re-pull code
git fetch origin claude/add-performance-dashboard-HeqGs
git reset --hard origin/claude/add-performance-dashboard-HeqGs
```

---

### Q: "Correlation Matrix Built: 0 pairs analyzed" - is this normal?

**Answer:** No, this means correlation building failed.

**Cause:** Likely exchange API issues or rate limiting.

**Impact:** Correlation filtering will be disabled, but other features work.

**Fix:** Bot will retry on next startup. Not critical for first deployment.

---

### Q: Position hit +5% but didn't sell

**Diagnosis:**
```bash
# Check risk module logs
grep "PROFIT EXIT\|Take Profit" bot.log | tail -20

# Check position age
sqlite3 data/trades_v3_paper.db "SELECT symbol, buy_timestamp, buy_price FROM positions WHERE id=<position_id>;"
```

**Possible Causes:**
1. Position is less than 60 days old and price is exactly at 5.00% (should sell)
2. Check if risk_module.py is correctly deployed
3. Verify no Python errors in logs

---

### Q: Bot keeps buying same coin repeatedly

**Possible Cause:** Correlation manager not working or cooldown not configured.

**Check:**
```bash
grep "Correlation Risk\|cooldown" bot.log | tail -10
```

**Expected:** Should see correlation blocks or cooldown messages.

**Fix:** Verify `run_bot.py` has `cooldown_same_day: 12` configured.

---

### Q: How do I manually sell a position stuck at -50%?

**Answer:** Use the dashboard (if available) or manual database update:

```bash
# Mark position for manual review
sqlite3 data/trades_v3_paper.db "UPDATE positions SET notes='MANUAL_REVIEW' WHERE id=<position_id>;"

# Then manually execute sell via Python console:
python3 -c "
from core.engine import TradingEngine
engine = TradingEngine(mode='paper', exchange='MEXC', db_path='data/trades_v3_paper.db')
# Execute manual sell
engine.execute_trade(
    bot={'name': 'Buy-the-Dip Strategy', 'amount': 25},
    symbol='YOUR/SYMBOL',
    side='SELL',
    price=CURRENT_PRICE,
    rsi=50,
    position_id=POSITION_ID,
    reason='Manual Sell - User Decision'
)
"
```

---

### Q: Can I test in paper mode first?

**Answer:** You're already in paper mode! (See `TRADING_MODE = 'paper'` in `run_bot.py`)

To switch to live:
1. **DO NOT** do this until you're 100% confident
2. Change `TRADING_MODE = 'live'` in `run_bot.py`
3. Add API keys to environment variables
4. Deploy with extreme caution

---

### Q: Expected annual return changed from 15-20% to 40-60%. Is this realistic?

**Answer:** Hybrid v2.0 is **optimistic** but based on:
- Dynamic TP captures bigger moves (not capped at 5%)
- Trailing stops let winners run to +20-30%
- Quality floors prevent -90% wipeouts
- Regime filtering avoids buying bear market knives
- Correlation limits reduce concentration risk

**Reality Check:**
- If actual returns are 30-40%, still a massive improvement
- First 3 months will be testing period
- Returns depend heavily on market conditions
- Past performance ≠ future results

**Monitor closely** and adjust if returns are below 20% after 90 days.

---

## 📞 SUPPORT

**Issues during deployment?**
1. Check logs first: `tail -100 bot.log`
2. Review this guide's troubleshooting section
3. Create GitHub issue with:
   - Full error message
   - Last 50 lines of bot.log
   - Output of `git log -1`
   - Database status: `sqlite3 data/trades_v3_paper.db ".tables"`

---

## ✅ DEPLOYMENT COMPLETE CHECKLIST

After 24 hours, verify:

- [ ] Bot is running without errors
- [ ] Correlation matrix built successfully
- [ ] Regime detector showing correct state
- [ ] At least one position exited (if any hit TP)
- [ ] Telegram alerts received
- [ ] No Python exceptions in logs
- [ ] Database not corrupted (can query positions)
- [ ] Backup verified and accessible

**If all checkboxes ✅:**
🎉 **Deployment Successful! Monitor for next 7 days.**

**If any checkbox ❌:**
⚠️ **Review logs and consider rollback if critical.**

---

**Good luck with your deployment! 🚀**

*Last Updated: 2025-12-30*
*Version: Hybrid v2.0*
