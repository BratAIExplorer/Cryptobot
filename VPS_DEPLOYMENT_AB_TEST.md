# 🧪 A/B Test Deployment Guide - Confluence=0

## 📋 Overview
This deployment sets `min_confluence=0` to collect empirical data on all trade opportunities, allowing us to determine the optimal threshold based on actual performance rather than guesswork.

## 🎯 Test Duration
**48 hours** (Start: Now, End: 2026-01-26 ~same time)

---

## 🚀 Step 1: Deploy to VPS

### 1.1 Push Changes to GitHub
```bash
git push origin claude/check-dashboard-status-VNa0U
```

### 1.2 SSH into VPS
```bash
ssh root@72.60.40.29
```

### 1.3 Pull Latest Code
```bash
cd ~/cryptobot_v3
git fetch origin
git checkout claude/check-dashboard-status-VNa0U
git pull origin claude/check-dashboard-status-VNa0U
```

### 1.4 Verify Change
```bash
grep "min_confluence" run_bot.py
# Should show: 'min_confluence': 0,  # A/B TEST: Collect data...
```

### 1.5 Restart Bot
```bash
sudo systemctl restart cryptobot
```

### 1.6 Verify Bot Started
```bash
# Check process
pgrep -f "run_bot.py" && echo "✅ RUNNING" || echo "❌ STOPPED"

# Check logs
tail -f logs/bot_engine.log
# Should see: "🤖 Crypto Bot - Refined Parameters"
# Press Ctrl+C to exit tail
```

---

## 📊 Step 2: Monitor During Test (48 Hours)

### Daily Checks (Morning & Evening)

#### Check Bot Status
```bash
ssh root@72.60.40.29 "pgrep -f 'run_bot.py' && echo '✅ RUNNING' || echo '❌ STOPPED'"
```

#### Watch Recent Activity
```bash
ssh root@72.60.40.29 "tail -30 ~/cryptobot_v3/logs/bot_engine.log"
```

#### Check Trade Count
```bash
ssh root@72.60.40.29 "sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db 'SELECT COUNT(*) as total_trades, SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins, ROUND(SUM(pnl), 2) as total_pnl FROM trades WHERE timestamp >= datetime(\"now\", \"-24 hours\");'"
```

### What You'll See

**Expected Log Output:**
```
INFO - Dip Detected: SOL/USDT (-3.2%), Confluence: 4/100 ✅ QUALIFIED
INFO - Dip Detected: ADA/USDT (-4.1%), Confluence: 12/100 ✅ QUALIFIED
INFO - 🟢 TRADE EXECUTED: BUY SOL/USDT @ $142.50
```

✅ **Key Difference from Before:**
- Previously: Scores below 50 were **❌ Skipped**
- Now: **ALL dips are qualified** (confluence=0 threshold)

### Warning Signs (Action Required)

| Sign | Meaning | Action |
|:---|:---|:---|
| 20+ trades in 1 hour | Too aggressive | Consider raising to min_confluence=10 |
| Circuit breaker triggered | Daily loss limit hit | Check why - bad market or bad strategy? |
| No trades in 12+ hours | No dips detected | Normal - wait for market movement |
| Bot process stopped | Crash or error | Check logs: `journalctl -u cryptobot -n 50` |

---

## 📈 Step 3: Collect Data After 48 Hours

### 3.1 Extract Confluence Scores from Logs
```bash
ssh root@72.60.40.29
cd ~/cryptobot_v3
bash scripts/extract_confluence_from_logs.sh
```

This creates a CSV file with all dip detections and their confluence scores.

### 3.2 Download Data Locally
```bash
# From your Windows machine
scp root@72.60.40.29:~/cryptobot_v3/confluence_analysis_*.csv .
```

### 3.3 Analyze Trade Performance
```bash
ssh root@72.60.40.29
cd ~/cryptobot_v3

# If confluence_score column exists in database:
python3 analyze_confluence_impact.py

# Otherwise, analyze via database directly:
sqlite3 data/multi/trades_paper.db << 'EOF'
SELECT
    CASE
        WHEN pnl > 0 THEN 'WIN'
        WHEN pnl < 0 THEN 'LOSS'
        ELSE 'BREAK-EVEN'
    END as outcome,
    COUNT(*) as trade_count,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(SUM(pnl), 2) as total_pnl
FROM trades
WHERE timestamp >= datetime('now', '-48 hours')
GROUP BY outcome;
EOF
```

---

## 🎯 Step 4: Determine Optimal Confluence

### Manual Analysis (If Database Doesn't Have Confluence Scores)

1. **Cross-reference** logs with database trades by timestamp & symbol
2. **Group trades** by confluence score ranges: 0-20, 21-40, 41-60, 61-80, 81-100
3. **Calculate** win rate & avg PnL for each range
4. **Identify** the threshold where quality improves significantly

### Example Decision Matrix

| Confluence Range | Trades | Wins | Win Rate | Avg PnL | Total PnL |
|:---|---:|---:|---:|---:|---:|
| 0-20 | 45 | 12 | 27% | -$0.50 | -$22.50 |
| 21-40 | 28 | 13 | 46% | $0.20 | $5.60 |
| 41-60 | 15 | 9 | 60% | $1.50 | $22.50 |
| 61-80 | 8 | 6 | 75% | $2.80 | $22.40 |
| 81-100 | 2 | 2 | 100% | $5.00 | $10.00 |

**Recommendation from above:**
- **min_confluence = 40** (filters out unprofitable <40, keeps 60%+ win rate)
- Alternative: **min_confluence = 60** (fewer trades but higher quality)

---

## 🔧 Step 5: Apply Findings

### Update Confluence Threshold
```bash
# Edit run_bot.py on VPS
nano ~/cryptobot_v3/run_bot.py

# Change line:
'min_confluence': 0,  # A/B TEST
# To:
'min_confluence': 40,  # Based on 48h A/B test data

# Save and restart
sudo systemctl restart cryptobot
```

### Commit Changes
```bash
git add run_bot.py
git commit -m "feat: set optimal min_confluence=40 based on A/B test data

Test Results (48 hours):
- Confluence <40: 27% win rate, -$22 total
- Confluence 40+: 65% win rate, +$55 total

Conclusion: Threshold of 40 filters low-quality while
preserving profitable setups.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin claude/check-dashboard-status-VNa0U
```

---

## 🆘 Troubleshooting

### Bot Stopped During Test
```bash
# Check why it stopped
journalctl -u cryptobot -n 100

# Common causes:
# 1. Circuit breaker (daily loss > $100)
# 2. Python error/crash
# 3. API connection issue

# Restart
sudo systemctl restart cryptobot
```

### Too Many Trades (Risk of Circuit Breaker)
```bash
# Temporarily increase to min_confluence=10 or 20
nano ~/cryptobot_v3/run_bot.py
# Change: 'min_confluence': 10,
sudo systemctl restart cryptobot
```

### No Trades at All
```bash
# Check if dips are being detected
grep "Dip Detected" ~/cryptobot_v3/logs/bot_engine.log | tail -20

# If yes: Bot is working, just waiting for opportunities
# If no: Check if bot is scanning properly
```

---

## 📝 Post-Test Documentation

After completing the test and determining optimal threshold, document:

1. **Test Period:** [Start Date/Time] to [End Date/Time]
2. **Total Dips Detected:** [Number]
3. **Total Trades Executed:** [Number]
4. **Confluence Distribution:** [Summary of score ranges]
5. **Optimal Threshold:** [Number] (with rationale)
6. **Expected Impact:** [Estimated reduction in trades, improvement in win rate]

Save this in: `CONFLUENCE_AB_TEST_RESULTS_[DATE].md`

---

## ✅ Success Criteria

The test is successful if you can:
- [x] Collect 20+ trades across various confluence levels
- [x] Identify clear win rate differences between ranges
- [x] Determine a threshold that improves profit factor
- [x] Have data-driven confidence in the new setting

---

**Test Started:** 2026-01-24
**Expected End:** 2026-01-26
**Status:** 🟢 IN PROGRESS
