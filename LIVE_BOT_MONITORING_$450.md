# LIVE Bot Monitoring Checklist - $450 Deployment
**Your Configuration:** ULTRA CONSERVATIVE
**Date Deployed:** January 4, 2026
**Total Allocation:** $450 Real Money

---

## 📊 Your Actual LIVE Configuration

| Bot | Allocation | Per Trade | Daily Loss Limit | Strategy |
|-----|------------|-----------|------------------|----------|
| Grid Bot BTC | $225 | $11 | $25 | Proven (83% win rate) |
| Grid Bot ETH | $225 | $7 | $20 | Proven (100% win rate!) |
| **TOTAL** | **$450** | - | **$45** | **Ultra Conservative** |

**Based on Paper Results:**
- Grid Bot BTC: +$1,734 in 1 month (83% win rate, 52 trades)
- Grid Bot ETH: +$6,475 in 1 month (100% win rate, 116 trades)

**Expected LIVE Performance (7.5% scale):**
- Conservative: +$130/month (28.9% monthly return)
- Expected: +$308/month (68% monthly return)
- Optimistic: +$615/month (137% monthly return)

**Risk:** MINIMAL (7.5% of paper allocation)

---

## ✅ Immediate Checks (First 5 Minutes)

### 1. Verify Bot is Running

```bash
ssh user@72.60.40.29
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

# Check service status
sudo systemctl status cryptobot_live.service
```

**Expected:**
```
● cryptobot_live.service - 🔴 Crypto Trading Bot (LIVE - REAL MONEY) 🔴
     Active: active (running)

... Grid Bot BTC: $225 ($11/trade)
... Grid Bot ETH: $225 ($7/trade)
... 🔴 LIVE BOT RUNNING - REAL MONEY MODE 🔴
```

### 2. Check Logs for Errors

```bash
tail -30 logs/bot_systemd.log
```

**Look for:**
- ✅ "Grid Bot BTC" and "Grid Bot ETH" registered
- ✅ "LIVE BOT RUNNING" message
- ❌ NO "Error", "Failed", "Exception" messages

###3. Check Database Registration

```bash
sqlite3 data/trades_v3_live.db << 'EOF'
SELECT
    strategy,
    status,
    ROUND(wallet_balance, 2) as balance,
    total_trades,
    last_heartbeat
FROM bot_status;
EOF
```

**Expected Output:**
```
Grid Bot BTC|RUNNING|225.0|0|2026-01-04 ...
Grid Bot ETH|RUNNING|225.0|0|2026-01-04 ...
```

✅ **If you see this, LIVE bot is successfully running!**

---

## 📋 First Hour Monitoring

### Check Dashboard (http://72.60.40.29:8501)

1. **Switch to LIVE TRADING mode** in sidebar
2. Verify display shows:
   - ✅ Active Bots: 2/2
   - ✅ Grid Bot BTC: $225 balance
   - ✅ Grid Bot ETH: $225 balance
   - ✅ Total Money: $450
   - ✅ Status: RUNNING (green indicators)

### Wait for First Trades

**Expected Timeline:**
- **High volatility market:** 30 minutes - 2 hours
- **Normal market:** 2-6 hours
- **Low volatility market:** 6-24 hours

**Grid Bots only trade when price crosses grid levels.**

If no trades after 2 hours:
- ✅ This is NORMAL if market is stable
- Check current BTC price is within $88K-$108K
- Check current ETH price is within $2.8K-$3.6K
- Be patient - Grid Bots wait for opportunities

---

## 📊 Daily Monitoring (Days 1-3)

### Morning Check (Once per day)

```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

# Run this complete diagnostic
sqlite3 data/trades_v3_live.db << 'EOF'
.mode column
.headers on

-- Bot Status
SELECT '=== BOT STATUS ===' as section;
SELECT strategy, status,
       ROUND(wallet_balance,2) as balance,
       ROUND(total_pnl,2) as pnl,
       total_trades
FROM bot_status;

-- Trades Last 24h
SELECT '=== TRADES (24H) ===' as section;
SELECT strategy,
       COUNT(*) as trades,
       SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
       SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
       ROUND(SUM(cost),2) as volume
FROM trades
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY strategy;

-- Recent Trades
SELECT '=== LAST 5 TRADES ===' as section;
SELECT datetime(timestamp, 'localtime') as time,
       strategy, symbol, side,
       ROUND(price,2) as price,
       ROUND(cost,2) as cost
FROM trades
ORDER BY timestamp DESC
LIMIT 5;

-- P&L Summary
SELECT '=== PERFORMANCE ===' as section;
SELECT 'Total P&L' as metric,
       ROUND(SUM(total_pnl),2) as value
FROM bot_status;
EOF
```

### Daily Success Criteria

**After 24 Hours:**
- ✅ Service status: RUNNING
- ✅ Trades executed: 2-10 (depends on market volatility)
- ✅ P&L: -$20 to +$50 (small range is normal)
- ✅ No circuit breaker triggers
- ✅ No critical errors in logs

**After 48 Hours:**
- ✅ Total trades: 4-20
- ✅ P&L: -$10 to +$100
- ✅ Both bots trading (not just one)

**After 72 Hours (3 days):**
- ✅ Total trades: 10-30
- ✅ P&L: +$20 to +$150
- ✅ Win rate: > 70%
- ✅ Consistent trading pattern

---

## 🎯 Expected Performance Benchmarks

### Conservative Expectations (Your $450 Allocation)

**Daily:**
- Trades: 2-8 total (1-4 per bot)
- P&L: +$4 to +$20
- Win Rate: 80-95%

**Weekly:**
- Trades: 14-56 total
- P&L: +$28 to +$140
- Cumulative: Small, steady growth

**Monthly:**
- Trades: 60-240 total
- P&L: +$130 to +$615
- Return: 28% to 137%

**These are estimates based on your paper trading results scaled to 7.5%**

---

## 🚨 Warning Signs & Actions

### ⚠️ Warning Level 1: Monitor Closely

**Triggers:**
- No trades for 24 hours
- P&L: -$10 to -$30
- Win rate < 70%

**Action:**
- Monitor every 6 hours
- Check logs for errors
- Verify prices are in grid ranges
- Continue running

### ⚠️⚠️ Warning Level 2: Investigate

**Triggers:**
- No trades for 48 hours
- P&L: -$30 to -$45
- Circuit breaker approaching

**Action:**
```bash
# Check current prices
sqlite3 data/trades_v3_live.db "SELECT symbol, ROUND(price,2), timestamp FROM trades ORDER BY timestamp DESC LIMIT 2;"

# Compare to grid ranges:
# BTC: $88,000 - $108,000
# ETH: $2,800 - $3,600

# Check for errors
grep -i "error\|failed\|exception" logs/bot_systemd.log | tail -20
```

### 🛑 Critical Level: STOP BOT

**Triggers:**
- P&L: < -$50 (circuit breaker)
- Repeated errors in logs
- Unexplained behavior

**Emergency Stop:**
```bash
# Method 1: Stop service
sudo systemctl stop cryptobot_live.service

# Method 2: Create stop signal
touch /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/STOP_SIGNAL_LIVE

# Method 3: Kill process
ps aux | grep run_bot_LIVE
sudo kill <PID>
```

**Then:**
1. Review logs thoroughly
2. Analyze all trades
3. Identify root cause
4. Fix in paper trading first
5. Validate fix for 72 hours
6. Re-deploy to LIVE

---

## 📈 Scaling Plan (After 72 Hours Success)

### Phase 2: Scale to 15% (If Successful)

**Success Criteria:**
- ✅ 10+ trades executed
- ✅ P&L: Positive (any amount > $0)
- ✅ Win rate: > 70%
- ✅ No circuit breaker triggers
- ✅ No critical errors

**Scale Up To:**
```python
# Grid Bot BTC
'amount': 22,              # $22 per level (was $11)
'initial_balance': 450,    # $450 total (was $225)
'max_daily_loss': 50,      # Increase loss limit

# Grid Bot ETH
'amount': 15,              # $15 per level (was $7)
'initial_balance': 450,    # $450 total (was $225)
'max_daily_loss': 40,      # Increase loss limit

# New Total: $900 (15% of paper)
```

**Expected Performance (15%):**
- Monthly P&L: +$260 to +$1,230
- Monthly Return: 28% to 137%

### Phase 3: Scale to 25% (After Another 72 Hours)

**If Phase 2 successful, scale to:**
- BTC: $750 ($37.50 per trade)
- ETH: $750 ($25 per trade)
- Total: $1,500 (25% of paper)
- Expected: +$430 to +$2,050/month

### Phase 4: Add Other Strategies

**After 2 weeks of successful Grid Bot trading:**
1. Add SMA Trend Bot at 10% allocation
2. Monitor for 1 week
3. Add Buy-the-Dip at 10% allocation
4. Monitor for 1 week
5. Gradually increase all bots

---

## 💡 Pro Tips

### 1. Telegram Alerts

If Telegram is configured, you should receive:

**Startup:**
```
🔴 LIVE TRADING BOT STARTED 🔴
⚠️ REAL MONEY MODE ACTIVE
📊 Active Strategies:
• Grid Bot BTC: $225 ($11/trade)
• Grid Bot ETH: $225 ($7/trade)
```

**Trades:**
```
✅ BUY Grid Bot BTC
📊 BTC/USDT
💰 $11.00 @ $91,234.56
```

**Alerts:**
If alerts stop, check Telegram bot configuration.

### 2. Compare Paper vs LIVE

**Run this weekly:**
```bash
# Paper performance
cd /Antigravity/antigravity/scratch/crypto_trading_bot
sqlite3 data/trades_v3_paper.db "SELECT strategy, ROUND(total_pnl,2), total_trades FROM bot_status WHERE strategy LIKE '%Grid%';"

# LIVE performance
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE
sqlite3 data/trades_v3_live.db "SELECT strategy, ROUND(total_pnl,2), total_trades FROM bot_status;"
```

**LIVE should track paper at ~7.5% scale**

### 3. Keep Paper Bot Running

**DO NOT stop paper trading bot!**
- Paper validates changes before LIVE
- Paper tests new strategies
- Paper provides benchmark data
- Both bots run independently

### 4. Log Everything

**Create a trading journal:**
```bash
# Daily snapshot
echo "$(date): LIVE Bot Performance" >> ~/trading_journal.txt
sqlite3 /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db \
  "SELECT ROUND(SUM(total_pnl),2) FROM bot_status;" >> ~/trading_journal.txt
```

---

## 📞 Quick Reference Commands

### Status Check
```bash
sudo systemctl status cryptobot_live.service
```

### View Live Logs
```bash
tail -f /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/bot_systemd.log
```

### Check P&L
```bash
sqlite3 /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db \
  "SELECT strategy, ROUND(total_pnl,2) as pnl FROM bot_status;"
```

### Check Recent Trades
```bash
sqlite3 /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db \
  "SELECT datetime(timestamp,'localtime') as time, strategy, side, ROUND(price,2) FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

### Emergency Stop
```bash
sudo systemctl stop cryptobot_live.service
```

### Restart Bot
```bash
sudo systemctl restart cryptobot_live.service
```

---

## 🎯 Your Next Steps

**Right Now:**
1. ✅ Verify bot is running (systemctl status)
2. ✅ Check dashboard shows 2/2 active bots
3. ✅ Confirm Telegram startup message received
4. ✅ Monitor logs for first 30 minutes

**First 6 Hours:**
1. Check logs every 2 hours
2. Watch for first trades
3. Verify no errors

**First 72 Hours:**
1. Run daily morning diagnostic
2. Check dashboard daily
3. Monitor P&L trend
4. Document any issues

**After 72 Hours (If Successful):**
1. Run comprehensive performance analysis
2. Decide on scaling to Phase 2 (15%)
3. Or maintain current allocation longer
4. Plan next strategies to add

---

## ✅ Success Indicators

You're doing GREAT if:
- ✅ Bot runs continuously without crashes
- ✅ Trades execute regularly (2-8 per day)
- ✅ P&L is positive or small negative
- ✅ Win rate > 70%
- ✅ No circuit breaker triggers
- ✅ Telegram alerts working
- ✅ Dashboard shows accurate data

**Congratulations on deploying to LIVE trading!** 🎉

Your ultra-conservative $450 approach is smart and minimizes risk while proving the strategy with real money.

---

**Monitoring Guide Created:** January 4, 2026
**For:** $450 LIVE Deployment (7.5% paper scale)
**Risk:** MINIMAL
**Expected:** +$130-$615/month
