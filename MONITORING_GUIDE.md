# 🔍 Monitoring & Readiness Guide

This guide explains how to use the monitoring tools to ensure your system is ready for live trading.

---

## 🎯 **CURRENT DEPLOYMENT STATUS (2026-01-24)**

### ✅ Latest Changes Deployed
- **VPS Commit:** 3a30829
- **Confluence:** Reduced to 50 (from 70) for more trade opportunities
- **Capital:** $1,500 paper trading budget
- **Status:** ✅ Bot running and actively scanning

### 📊 Live Monitoring Commands (VPS)

#### **1. Watch Live Logs** (See dip detections & confluence scores in real-time)
```bash
ssh root@72.60.40.29 "tail -f ~/cryptobot_v3/logs/bot_engine.log"
```

#### **2. Check Bot Status**
```bash
ssh root@72.60.40.29 "pgrep -f 'run_bot.py' && echo '✅ RUNNING' || echo '❌ STOPPED'"
```

#### **3. Quick Performance Summary**
```bash
ssh root@72.60.40.29 "bash ~/cryptobot_v3/scripts/get_vps_perf.sh"
```

#### **4. Watch for First Trade** (Filter important events only)
```bash
./scripts/watch_for_first_trade.sh
```

#### **5. Full Monitor with Auto-Refresh** (Updates every 60 seconds)
```bash
watch -n 60 ./scripts/monitor_live.sh
```

### 🔍 What You're Seeing Now

**Expected Log Pattern:**
```
INFO - Dip Detected: SOL/USDT (-3.2%), Confluence: 4/50 ❌ Skipped
INFO - Dip Detected: ADA/USDT (-4.1%), Confluence: 12/50 ❌ Skipped
```

✅ **This is CORRECT behavior!**
- Bot is detecting dips
- Confluence scores are low (4-12)
- Correctly filtering out low-quality noise
- Waiting for confluence >= 50 for trade execution

**First Trade Will Look Like:**
```
INFO - Dip Detected: BTC/USDT (-5.2%), Confluence: 67/50 ✅ QUALIFIED
INFO - 🟢 TRADE EXECUTED: BUY BTC/USDT @ $42,150
```

### 📈 Confluence Score Guide

| Score Range | Action | Meaning |
|:---|:---|:---|
| 0-30 | ❌ Skip | Pure noise, no momentum |
| 31-49 | ❌ Skip | Below threshold |
| **50-70** | ✅ **TRADE** | Good quality signal |
| 71-100 | ✅ **TRADE** | Excellent confluence |

### 🎯 Next Steps
1. **Monitor for 24-48 hours** - Let bot find natural high-quality setups
2. **Review first 3 trades** - Verify they meet expectations
3. **Fine-tune if needed** - Adjust confluence threshold based on trade frequency

---

## 🚀 Quick Start

### 1. Quick Status Check (30 seconds)
```bash
python3 status.py
```
Shows instant snapshot of:
- Binance latency
- Paper trading performance
- Quick readiness assessment

**Run this daily** to catch issues early.

---

### 2. Detailed Latency Test (1 minute)
```bash
python3 monitor_binance_latency.py
```

Tests Binance connection with 10 samples and shows:
- Average, min, max latency
- Standard deviation (stability)
- Trading strategy readiness
- Actionable recommendations

**Options:**
```bash
# More samples for better accuracy
python3 monitor_binance_latency.py -s 20 -i 1

# Continuous monitoring (runs every 5 minutes)
python3 monitor_binance_latency.py --continuous

# Don't save to log file
python3 monitor_binance_latency.py --no-log
```

---

### 3. Full Readiness Check (2 minutes)
```bash
python3 check_live_readiness.py
```

Comprehensive validation covering:
- ✅ Binance latency
- ✅ Paper trading history (days, trades)
- ✅ Profitability
- ✅ Win rate
- ✅ Drawdown/risk control
- ✅ Market regime detection
- ✅ API credentials
- ✅ Risk management

**Only go live if this passes with no FAIL statuses.**

---

## 📊 Understanding Results

### Latency Benchmarks

| Status | Latency | Grid Bots | Buy-Dip | Scalping |
|--------|---------|-----------|---------|----------|
| 🟢 Excellent | <200ms | ✅ Perfect | ✅ Perfect | ✅ Ready |
| ✅ Good | 200-500ms | ✅ Great | ✅ Great | ⚠️ Marginal |
| 🟡 Acceptable | 500-1000ms | ⚠️ Monitor | ✅ Good | ❌ Too Slow |
| 🔴 Slow | 1000-2000ms | ❌ Not Ready | 🟡 OK | ❌ Too Slow |
| 🛑 Critical | >2000ms | ❌ Fix Now | ❌ Fix Now | ❌ Fix Now |

### Trading History Requirements

| Requirement | Minimum | Recommended | Excellent |
|-------------|---------|-------------|-----------|
| Days Trading | 14+ | 30+ | 60+ |
| Total Trades | 20+ | 50+ | 100+ |
| Win Rate | 35%+ | 50%+ | 60%+ |
| Profitability | $0+ | $50+ | $200+ |

---

## 🔧 Fixing Common Issues

### Issue 1: High Latency (>1000ms)

**Diagnosis:**
```bash
# Test network to Binance
ping -c 20 api.binance.com

# Check VPS location
curl ipinfo.io

# Time HTTP request
time curl -s https://api.binance.com/api/v3/ping
```

**Solutions:**

1. **VPS Location** (Most Common)
   - Binance servers: Singapore, Tokyo, Frankfurt
   - Your VPS should be in same region
   - Check current location: `curl ipinfo.io`
   - Consider migrating to:
     - AWS ap-southeast-1 (Singapore)
     - AWS ap-northeast-1 (Tokyo)
     - AWS eu-central-1 (Frankfurt)

2. **DNS Issues**
   ```bash
   # Test DNS speed
   time nslookup api.binance.com

   # Change to faster DNS (Google)
   sudo nano /etc/resolv.conf
   # Add: nameserver 8.8.8.8
   ```

3. **Network Congestion**
   - Test at different times (peak vs off-peak)
   - Upgrade VPS bandwidth
   - Contact VPS provider

4. **Rate Limiting**
   ```bash
   # Check rate limit headers
   curl -I https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
   ```

---

### Issue 2: Insufficient Trading History

**Problem:** Less than 20 trades or 14 days

**Solution:**
```bash
# Continue running paper trading
python3 run_bot.py

# Let it run for 2-4 weeks minimum
# Check progress daily:
python3 status.py
```

**Accelerate Testing:**
- Reduce signal thresholds temporarily (paper only!)
- Add more symbols to trade
- Use shorter timeframes (but beware: results won't be representative!)

---

### Issue 3: Unprofitable Strategy

**Problem:** Negative PnL in paper trading

**Solution:**
1. Analyze losing trades:
   ```python
   from core.logger import TradeLogger
   logger = TradeLogger(mode='paper')
   trades = logger.get_trades()
   losses = trades[trades['pnl'] < 0].sort_values('pnl')
   print(losses[['symbol', 'strategy', 'entry_price', 'exit_price', 'pnl']])
   ```

2. Common issues:
   - Stop losses too tight
   - Take profits too aggressive
   - Wrong market conditions
   - Poor symbol selection

3. Review strategy parameters:
   - Grid spacing
   - Dip detection thresholds
   - Risk per trade
   - Max concurrent positions

---

## 📈 Monitoring Schedule

### Daily (Morning)
```bash
python3 status.py
```
- Check if bot is running
- Review overnight performance
- Monitor latency

### Weekly
```bash
python3 monitor_binance_latency.py -s 20
python3 check_live_readiness.py
```
- Deep latency analysis
- Full readiness assessment
- Review weekly P&L

### Before Going Live
```bash
# 1. Run monitoring at different times
python3 monitor_binance_latency.py -s 30

# 2. Wait 2 hours, test again (peak vs off-peak)
python3 monitor_binance_latency.py -s 30

# 3. Full readiness check
python3 check_live_readiness.py

# 4. If all pass, review checklist:
cat PAPER_TO_LIVE_CHECKLIST.md
```

---

## 🤖 Automated Monitoring with Cron

Add to crontab (`crontab -e`):

```bash
# Quick status every hour (save to file)
0 * * * * cd /root/cryptobot_v3 && python3 status.py >> logs/status_history.log 2>&1

# Detailed latency check every 4 hours
0 */4 * * * cd /root/cryptobot_v3 && python3 monitor_binance_latency.py -s 10 >> logs/latency_checks.log 2>&1

# Full readiness check daily at 8 AM
0 8 * * * cd /root/cryptobot_v3 && python3 check_live_readiness.py >> logs/readiness_checks.log 2>&1
```

---

## 🚨 Alert Thresholds

### Critical Alerts (Stop Trading)
- ❌ Latency > 2000ms for 3+ consecutive checks
- ❌ Connection failures > 5 in 1 hour
- ❌ Daily loss > 10%
- ❌ Single loss > $100

### Warning Alerts (Monitor Closely)
- ⚠️ Latency > 1000ms
- ⚠️ Win rate drops below 40%
- ⚠️ 3+ consecutive losses
- ⚠️ No trades in 12 hours (if market active)

### Info (Good to Know)
- ℹ️ New milestone reached ($100, $250, $500, $1000)
- ℹ️ Profitable day
- ℹ️ Latency improved

---

## 📝 Logs and History

### Log Files

```bash
# Latency history (JSONL format)
logs/latency_history.jsonl

# Status checks
logs/status_history.log

# Full readiness checks
logs/readiness_checks.log

# Bot trading logs
logs/trading.log
```

### Analyze History

```python
import json

# Load latency history
with open('logs/latency_history.jsonl') as f:
    history = [json.loads(line) for line in f]

# Calculate average over last week
recent = [h for h in history[-50:]]  # Last 50 checks
avg_latency = sum(h['avg'] for h in recent) / len(recent)
print(f"Average latency (last 50 checks): {avg_latency:.1f}ms")

# Find peak latency times
for h in sorted(history, key=lambda x: x['avg'], reverse=True)[:5]:
    print(f"{h['timestamp']}: {h['avg']}ms")
```

---

## 🎯 Decision Matrix

| Scenario | Action |
|----------|--------|
| ✅ All checks pass | Start with 10% capital, single best bot |
| ⚠️ Some warnings | Fix warnings first, then start small |
| ❌ Any failures | Continue paper trading, fix issues |
| 🔴 Critical latency | **DO NOT GO LIVE** - Fix VPS/network first |
| 📉 Losses in paper | **DO NOT GO LIVE** - Fix strategy first |

---

## 💡 Pro Tips

1. **Test at Different Times**
   - Morning, afternoon, evening, night
   - Weekday vs weekend
   - During high volatility events

2. **Compare with Baseline**
   - Document initial latency
   - Monitor trends over time
   - Alert if degrades significantly

3. **VPS Optimization**
   - Minimal services running
   - Dedicated to trading only
   - Regular updates and restarts

4. **Backup Plans**
   - Know how to stop bot quickly
   - Have manual override ready
   - Telegram alerts configured

5. **Start Small**
   - 10% of planned capital
   - Single best-performing bot
   - Scale up gradually after 1-2 weeks

---

## 📚 Reference

### Latency Measurement
The system measures latency using lightweight `fetch_time()` calls to Binance API. This gives true network round-trip time, not data transfer time.

**What was fixed:** Previous version measured time to fetch 250 days of OHLCV data, which incorrectly showed 2000ms+ latency when actual network latency might be <500ms.

### Trading Strategies by Latency

- **Grid Bots**: Need <1000ms for optimal grid management
- **Buy-the-Dip**: Can work with <2000ms (less time-sensitive)
- **Scalping**: Require <200ms (not recommended for retail)
- **Swing Trading**: Can tolerate <5000ms

---

## 🆘 Getting Help

If issues persist:
1. Run full diagnostic: `bash BINANCE_LATENCY_INVESTIGATION.md` (follow steps)
2. Check VPS provider documentation
3. Contact VPS support with latency logs
4. Consider professional VPS migration service

---

**Last Updated:** 2026-01-22
**Version:** 1.0
