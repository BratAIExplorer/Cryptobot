# 📊 72-HOUR POST-DEPLOYMENT MONITORING CHECKLIST

**Deployment Date:** _[To be filled]_
**Monitoring Period:** First 72 hours after bot restart
**Version:** 2025.12.30 (Intelligence Enhanced + Strategy V2)

---

## ⏰ MONITORING SCHEDULE

### **Hour 1: Immediate Checks (Critical)**
- [ ] **T+10min:** Bot started successfully, no crashes
- [ ] **T+30min:** First confluence calculations working
- [ ] **T+1hr:** Check regime detection is functioning
- [ ] **T+1hr:** Verify crash detection is active
- [ ] **T+1hr:** Confirm Telegram alerts received (if configured)

**Commands:**
```bash
# Check bot is running
ps aux | grep run_bot.py

# Check recent logs
tail -100 logs/bot_$(date +%Y%m%d).log

# Test Telegram
python3 scripts/test_telegram.py

# Check database
sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) FROM trades;"
```

---

### **Hour 6: Early Performance Check**
- [ ] **Strategy Activity:** At least 1-2 bots should be evaluating coins
- [ ] **No Crashes:** No error alerts or service restarts
- [ ] **SMA Trend V2:** Verify ADX filter is working (check logs for "ADX")
- [ ] **Hidden Gem V2:** Confirm using new symbol list (no SAND/MANA/AXS)
- [ ] **CryptoPanic:** News fetching (if API configured)

**Commands:**
```bash
# Check active evaluations in logs
grep -i "evaluating\|signal" logs/bot_$(date +%Y%m%d).log | tail -50

# Check for ADX calculations (SMA V2 feature)
grep -i "adx" logs/bot_$(date +%Y%m%d).log | tail -20

# Check crash detection
grep -i "crash\|flash" logs/bot_$(date +%Y%m%d).log | tail -20

# Check CryptoPanic integration
grep -i "cryptopanic\|news" logs/bot_$(date +%Y%m%d).log | tail -20
```

**Database Check:**
```sql
-- Check trades by strategy
SELECT
    bot_name,
    COUNT(*) as trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells
FROM trades
WHERE entry_time > datetime('now', '-6 hours')
GROUP BY bot_name;
```

---

### **Hour 24: Day 1 Review**
- [ ] **All Strategies Evaluated:** Each bot should have evaluated multiple coins
- [ ] **First Trades Executed:** At least 1-2 positions opened (if market conditions allow)
- [ ] **No False Starts:** Verify confluence scores preventing bad entries
- [ ] **Risk Limits Working:** Max exposure per coin respected
- [ ] **Alerts Functioning:** Received buy/sell notifications (if Telegram configured)

**Performance Metrics:**
```bash
# Run analysis script
python3 analyze_all_strategies.py

# Check strategy-specific performance
python3 scripts/telegram_report.py  # Generates performance summary
```

**Key Metrics to Check:**
- [ ] **Grid Bots:** Should have 5-10+ fills per day
- [ ] **SMA Trend V2:** Win rate improving vs historical (target 45%+)
- [ ] **Buy-the-Dip:** Only entering on genuine dips (5%+)
- [ ] **Hidden Gem V2:** Using new symbol list, 10% SL working
- [ ] **Momentum Swing:** Still paused at $500 (verify low activity)

**Database Validation:**
```sql
-- Verify V2 improvements are active
SELECT
    bot_name,
    symbol,
    entry_price,
    current_price,
    stop_loss_price,
    take_profit_price,
    (take_profit_price - entry_price) / entry_price * 100 as tp_pct,
    (entry_price - stop_loss_price) / entry_price * 100 as sl_pct
FROM trades
WHERE exit_time IS NULL
ORDER BY entry_time DESC;
```

**Expected SL/TP for V2:**
- Hidden Gem: TP=15%, SL=10% (was 10%/20%)
- SMA Trend: TP=10%, SL=5% (was same/3%)

---

### **Hour 48: Day 2 Review**
- [ ] **Position Management:** Trailing stops activating correctly
- [ ] **Exit Logic:** Hybrid V2.0 dynamic TP working for Buy-the-Dip
- [ ] **Crash Detection:** Verify coins are blocked during flash crashes
- [ ] **News Veto:** Check if CryptoPanic vetoed any bad trades (if configured)
- [ ] **No Strategy Failures:** Momentum Swing still safe at $500

**Advanced Checks:**
```bash
# Check trailing stop activations
grep -i "trailing" logs/bot_*.log | tail -50

# Check crash detection events
grep -i "crash detected\|blocking.*crash" logs/bot_*.log

# Check news-based vetoes
grep -i "veto\|cryptopanic.*bearish" logs/bot_*.log

# Performance by coin
sqlite3 data/trades_v3_paper.db << EOF
SELECT
    symbol,
    COUNT(*) as trades,
    ROUND(AVG(CASE
        WHEN exit_time IS NOT NULL
        THEN (exit_price - entry_price) / entry_price * 100
        ELSE 0
    END), 2) as avg_return_pct,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses
FROM trades
WHERE entry_time > datetime('now', '-48 hours')
GROUP BY symbol
ORDER BY avg_return_pct DESC;
EOF
```

**Red Flags to Watch:**
- ❌ Same coin being bought repeatedly at loss (cooldown failure)
- ❌ Stop losses not triggering (check SL implementation)
- ❌ Hidden Gem buying dead coins (SAND, MANA, AXS = bug!)
- ❌ SMA Trend win rate < 30% (whipsaw issue not fixed)
- ❌ Any strategy exceeding circuit breaker limits

---

### **Hour 72: Final Validation**
- [ ] **3-Day Performance:** Calculate actual returns vs expectations
- [ ] **Strategy V2 Validation:** Compare new vs old performance
- [ ] **System Stability:** No crashes, memory leaks, or stalls
- [ ] **Ready for Scale:** If paper trading successful, plan live transition

**Final Performance Report:**
```bash
# Generate comprehensive report
python3 comprehensive_analysis.py

# Database summary
sqlite3 data/trades_v3_paper.db << EOF
.mode column
.headers on

-- Overall Performance
SELECT
    'OVERALL' as strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_pct,
    ROUND(SUM(profit), 2) as total_profit,
    ROUND(AVG(profit), 2) as avg_per_trade
FROM trades
WHERE exit_time IS NOT NULL;

-- By Strategy
SELECT
    bot_name,
    COUNT(*) as trades,
    ROUND(SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate,
    ROUND(SUM(profit), 2) as profit
FROM trades
WHERE exit_time IS NOT NULL
GROUP BY bot_name
ORDER BY profit DESC;
EOF
```

**GO/NO-GO Decision:**

✅ **GREEN (Scale Up):**
- Win rate ≥ 40% overall
- All V2 improvements functioning
- No critical bugs
- System stable for 72 hours

⚠️ **YELLOW (Continue Monitoring):**
- Win rate 30-40%
- Minor issues but no showstoppers
- Need 1 more week data

🔴 **RED (Rollback/Fix):**
- Win rate < 30%
- Critical bugs (wrong SL/TP, crashes)
- V2 improvements not working

---

## 🎯 SUCCESS CRITERIA (72-Hour Targets)

### **Strategy-Specific Targets:**

**Grid Bots (BTC/ETH):**
- ✅ 30-50 fills over 72 hours
- ✅ $100-200 paper profit (proof of concept)
- ✅ No missed grid opportunities

**SMA Trend Bot V2:**
- ✅ ADX filter active (log evidence)
- ✅ Win rate ≥ 45% (improvement from 30%)
- ✅ No whipsaws in sideways market
- ✅ 3-5 trades executed

**Buy-the-Dip (Hybrid V2.0):**
- ✅ Only buying genuine dips (5%+)
- ✅ Dynamic TP working (varies by hold time)
- ✅ No forced exits (only TP or floor hits)
- ✅ 5-10 positions opened

**Hidden Gem Monitor V2:**
- ✅ Using new symbol list (verify no SAND/MANA/AXS)
- ✅ 10% SL, 15% TP (not 20%/10%)
- ✅ No 72-hour forced exits
- ✅ 2-4 gem positions

**Momentum Swing (Paused):**
- ✅ ONLY $500 allocation (not $1000)
- ✅ ≤ 2 positions max
- ✅ Verify it needs backtest before scale

---

## 📞 ESCALATION & ISSUES

**If Critical Issues Found:**

1. **Bot Crash Loop:**
   ```bash
   # Create stop signal
   touch STOP_SIGNAL

   # Check error logs
   tail -200 logs/bot_$(date +%Y%m%d).log

   # Review stack trace
   grep -A 20 "Traceback" logs/bot_*.log
   ```

2. **Wrong SL/TP Executing:**
   ```bash
   # Emergency: Stop bot immediately
   pkill -f run_bot.py

   # Verify configuration
   grep -A 5 "Hidden Gem\|SMA Trend" run_bot.py

   # Check recent trades
   sqlite3 data/trades_v3_paper.db \
     "SELECT * FROM trades ORDER BY entry_time DESC LIMIT 10;"
   ```

3. **Performance Degradation:**
   ```bash
   # Check system resources
   top -b -n 1 | head -20

   # Check database size
   du -h data/*.db

   # Analyze slow queries (if any)
   grep "slow\|timeout" logs/bot_*.log
   ```

**Rollback Procedure:**
```bash
# Stop bot
touch STOP_SIGNAL  # or pkill -f run_bot.py

# Revert to previous version
git log --oneline -5  # Find stable commit
git checkout <commit_hash>

# Restart with old config
python3 run_bot.py
```

---

## 📝 MONITORING LOG TEMPLATE

| Time | Check | Status | Notes |
|------|-------|--------|-------|
| T+10min | Bot Started | ⬜ | |
| T+1hr | Confluence Working | ⬜ | |
| T+1hr | Crash Detection Active | ⬜ | |
| T+6hr | First Activity | ⬜ | |
| T+24hr | Day 1 Review | ⬜ | |
| T+24hr | Performance Analysis | ⬜ | |
| T+48hr | Trailing Stops Check | ⬜ | |
| T+48hr | News Veto Check | ⬜ | |
| T+72hr | Final Validation | ⬜ | |
| T+72hr | GO/NO-GO Decision | ⬜ | |

---

## 🔗 USEFUL COMMANDS REFERENCE

```bash
# Start monitoring (run these in separate terminals)
tail -f logs/bot_$(date +%Y%m%d).log                    # Live logs
watch -n 60 'python3 scripts/telegram_report.py'        # Performance every 60s
watch -n 300 'sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) FROM trades;"'  # Trade count

# Quick stats
python3 comprehensive_analysis.py | tail -50            # Performance summary
python3 analyze_all_strategies.py                       # Strategy breakdown

# Database queries
sqlite3 data/trades_v3_paper.db                         # Interactive mode
sqlite3 data/trades_v3_paper.db ".schema trades"        # See table structure
sqlite3 data/trades_v3_paper.db ".tables"               # List all tables
```

---

**GOOD LUCK! 🚀**

Monitor carefully, trust the data, and don't hesitate to rollback if something looks wrong.
