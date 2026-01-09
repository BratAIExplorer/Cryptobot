# 🤖 BOT STATUS, STABILITY & PERFORMANCE REVIEW

**Date:** 2026-01-06
**Branch:** `feature/adapter-refactor` (with Priority 1 enhancements merged)
**Review Type:** Comprehensive System Health Check

---

## 📊 QUICK STATUS CHECK COMMANDS

Run these on your VPS to assess current bot status:

```bash
# ============================================
# 1. CHECK RUNNING PROCESSES
# ============================================
ps aux | grep -E "python.*run_bot|python.*bot" | grep -v grep

# Expected: Should show python process if bot is running
# If empty: Bot is not currently running

# ============================================
# 2. CHECK BOT PID FILE
# ============================================
cat bot.pid 2>/dev/null
ps -p $(cat bot.pid 2>/dev/null) 2>/dev/null

# Shows: Process ID if bot is running
# Error: No such process (bot stopped)

# ============================================
# 3. CHECK RECENT LOGS
# ============================================
tail -100 logs/*.log | grep -E "ERROR|WARNING|CRITICAL|✅|❌" | tail -30

# Shows: Recent errors and status messages
# Look for: Patterns of failures, successful trades

# ============================================
# 4. CHECK DATABASE STATUS
# ============================================
sqlite3 data/trades_v3_paper.db "
SELECT
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN status='CLOSED' THEN 1 ELSE 0 END) as closed,
    SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END) as open_positions
FROM positions
GROUP BY strategy;
"

# Shows: Trade count per strategy
# Look for: Active strategies, open positions

# ============================================
# 5. CHECK RECENT PERFORMANCE (24h)
# ============================================
sqlite3 data/trades_v3_paper.db "
SELECT
    strategy,
    COUNT(*) as trades_24h,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate_pct
FROM positions
WHERE status='CLOSED'
  AND exit_time > datetime('now', '-24 hours')
GROUP BY strategy
ORDER BY total_pnl DESC;
"

# Shows: 24-hour performance by strategy
# Look for: Profitability, win rates

# ============================================
# 6. CHECK CIRCUIT BREAKER STATUS
# ============================================
sqlite3 data/trades_v3_paper.db "
SELECT * FROM circuit_breaker WHERE id=1;
"

# Shows: Circuit breaker state
# is_paused=1 means trading is PAUSED
# consecutive_errors shows error count

# ============================================
# 7. CHECK DISK SPACE
# ============================================
df -h /Antigravity/antigravity/scratch/crypto_trading_bot

# Shows: Disk usage
# Warning: If >90% full, cleanup needed

# ============================================
# 8. CHECK SYSTEMD SERVICE (if configured)
# ============================================
systemctl status cryptobot 2>/dev/null || echo "No systemd service configured"

# Shows: Service status
# Active (running): Bot is running as service
# Inactive (dead): Service stopped
```

---

## 🔍 DETAILED PERFORMANCE ANALYSIS

### **Grid Bot Performance Check**

```bash
# Check Grid Bot trades and profitability
sqlite3 data/trades_v3_paper.db << 'EOF'
.mode column
.headers on

SELECT
    'Grid Bot BTC' as bot,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl_per_trade,
    ROUND(MIN(pnl), 2) as worst_trade,
    ROUND(MAX(pnl), 2) as best_trade
FROM positions
WHERE strategy LIKE '%Grid%BTC%'
  AND status='CLOSED';

SELECT
    'Grid Bot ETH' as bot,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl_per_trade
FROM positions
WHERE strategy LIKE '%Grid%ETH%'
  AND status='CLOSED';
EOF
```

**Expected Results (from previous backtests):**
- BTC Grid: 70-100% win rate, $1.50 avg profit/trade
- ETH Grid: 70-100% win rate, $0.92 avg profit/trade

**Red Flags:**
- ❌ Win rate < 60%
- ❌ Average profit < $0.50
- ❌ Total PnL negative

---

### **Buy-the-Dip Performance Check**

```bash
# Check Dip strategy performance
sqlite3 data/trades_v3_paper.db << 'EOF'
.mode column
.headers on

SELECT
    COUNT(*) as total_positions,
    SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END) as currently_open,
    SUM(CASE WHEN status='CLOSED' AND pnl > 0 THEN 1 ELSE 0 END) as profitable_exits,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) /
          SUM(CASE WHEN status='CLOSED' THEN 1 ELSE 0 END), 1) as win_rate,
    ROUND(SUM(CASE WHEN status='CLOSED' THEN pnl ELSE 0 END), 2) as realized_pnl,
    ROUND(AVG(CASE WHEN status='CLOSED' THEN
          (julianday(exit_time) - julianday(entry_time)) ELSE NULL END), 1) as avg_hold_days
FROM positions
WHERE strategy LIKE '%Dip%';

-- Check current open positions
SELECT
    symbol,
    buy_price,
    ROUND((julianday('now') - julianday(entry_time)), 1) as days_held,
    confluence_score
FROM positions
WHERE strategy LIKE '%Dip%' AND status='OPEN'
ORDER BY entry_time DESC
LIMIT 10;
EOF
```

**Expected Results:**
- Win rate: 65%+
- Average hold time: 30-60 days
- Confluence scores: 65+ for entries

**Red Flags:**
- ❌ Win rate < 50%
- ❌ Positions held > 180 days
- ❌ Multiple positions with confluence < 60

---

## 🚨 STABILITY CHECKS

### **Check for Common Issues**

```bash
# ============================================
# 1. DATABASE LOCK ISSUES
# ============================================
lsof data/trades_v3_paper.db 2>/dev/null | wc -l
# Should be: 0-2 (if bot running)
# Warning: >5 means multiple processes accessing DB

# ============================================
# 2. MEMORY USAGE
# ============================================
ps aux | grep python | grep run_bot | awk '{print $4}'
# Should be: <5% memory
# Warning: >20% indicates memory leak

# ============================================
# 3. LOG FILE SIZE
# ============================================
du -sh logs/*.log
# Should be: <100MB each
# Action: Rotate logs if >500MB

# ============================================
# 4. API KEY VALIDITY
# ============================================
python3 -c "
import os
print('MEXC API Key set:', 'Yes' if os.getenv('MEXC_API_KEY') else 'No')
print('Binance API Key set:', 'Yes' if os.getenv('BINANCE_API_KEY') else 'No')
"

# ============================================
# 5. NETWORK CONNECTIVITY
# ============================================
ping -c 3 www.mexc.com > /dev/null 2>&1 && echo "✅ MEXC reachable" || echo "❌ MEXC unreachable"
ping -c 3 api.binance.com > /dev/null 2>&1 && echo "✅ Binance reachable" || echo "❌ Binance unreachable"
```

---

## 📈 PERFORMANCE BENCHMARKS

### **Grid Bot Benchmarks (from GRID_AND_DIP_STRATEGIES_REFERENCE.md)**

| Metric | BTC Grid | ETH Grid | Your Actual |
|--------|----------|----------|-------------|
| **Grid Levels** | 20 | 30 | ❓ Check config |
| **Range** | $85K-$110K | $2.8K-$3.6K | ❓ Check logs |
| **Grid Step** | $1,315 | $27.59 | ❓ Calculated |
| **Net Profit/Trade** | $1.50 | $0.92 | ❓ Run query |
| **Win Rate** | 70-100% | 70-100% | ❓ Run query |
| **Trades/Week** | 10-20 | 10-20 | ❓ Check DB |

**To check your actual values:**
```bash
# Get Grid Bot configuration from logs
grep "Grid Bot" logs/*.log | grep -E "lower_limit|upper_limit|grid_levels" | tail -10
```

---

### **Buy-the-Dip Benchmarks**

| Metric | Expected | Your Actual |
|--------|----------|-------------|
| **Win Rate** | 65%+ | ❓ Run query |
| **Avg Hold Time** | 30-60 days | ❓ Run query |
| **Confluence Threshold** | 65+ | ❓ Check config |
| **Take Profit** | 5-15% (dynamic) | ❓ Check exits |
| **Max Loss Floor** | -40% to -70% | ❓ Check config |

---

## 🔧 RECOMMENDED ACTIONS

### **If Bot is NOT Running:**

```bash
# Check why it stopped
tail -200 logs/*.log | grep -E "ERROR|Exception|Traceback" | tail -30

# Common issues:
# 1. API key expired → Update .env
# 2. Database locked → Kill zombie processes
# 3. Circuit breaker triggered → Reset in DB
# 4. Out of memory → Restart server

# Restart bot (paper trading)
python3 run_bot.py --mode paper
```

---

### **If Performance is Below Benchmarks:**

**Grid Bot Underperforming:**
```bash
# Check if using static grids (required for profitability)
grep "FORCE STATIC GRIDS" strategies/grid_strategy_v2.py

# Should show: Line 89 with force static comment
# If missing: Grid may be using dynamic (unprofitable) ranges

# Check grid range is correct
grep "lower_limit\|upper_limit" run_bot.py | grep -A2 "Grid Bot BTC"
```

**Buy-the-Dip Underperforming:**
```bash
# Check confluence scoring is active
grep "min_confluence" run_bot.py

# Should show: 65 or higher
# If lower: Reduce threshold to 60 and monitor

# Check Hybrid v2.0 is active
grep "Hybrid v2.0" core/risk_module.py

# Should exist: Dynamic TP logic
```

---

### **If Circuit Breaker is Active:**

```bash
# Check reason
sqlite3 data/trades_v3_paper.db "
SELECT reason, triggered_at, consecutive_errors
FROM circuit_breaker
WHERE id=1;
"

# Reset if false alarm
sqlite3 data/trades_v3_paper.db "
UPDATE circuit_breaker
SET is_paused=0, consecutive_errors=0, reason='Manual reset'
WHERE id=1;
"

# Then restart bot
```

---

## 📋 WEEKLY PERFORMANCE REPORT

Run this every Sunday to track progress:

```bash
sqlite3 data/trades_v3_paper.db << 'EOF'
.mode column
.headers on

-- Weekly Summary
SELECT
    'WEEKLY SUMMARY' as report,
    COUNT(*) as total_trades,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
FROM positions
WHERE status='CLOSED'
  AND exit_time > datetime('now', '-7 days');

-- Performance by Strategy
SELECT
    strategy,
    COUNT(*) as trades,
    ROUND(SUM(pnl), 2) as pnl,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
FROM positions
WHERE status='CLOSED'
  AND exit_time > datetime('now', '-7 days')
GROUP BY strategy
ORDER BY pnl DESC;

-- Best and Worst Trades
SELECT '=== BEST TRADE ===' as note, strategy, symbol, ROUND(pnl, 2) as pnl
FROM positions WHERE status='CLOSED' AND exit_time > datetime('now', '-7 days')
ORDER BY pnl DESC LIMIT 1;

SELECT '=== WORST TRADE ===' as note, strategy, symbol, ROUND(pnl, 2) as pnl
FROM positions WHERE status='CLOSED' AND exit_time > datetime('now', '-7 days')
ORDER BY pnl ASC LIMIT 1;
EOF
```

---

## 🎯 SUCCESS CRITERIA

Your bots are **HEALTHY** if:

- ✅ At least one bot is running (ps aux shows process)
- ✅ No circuit breaker active (is_paused=0)
- ✅ Grid Bots: 60%+ win rate, positive PnL
- ✅ Dip Strategy: 50%+ win rate, reasonable hold times
- ✅ No errors in last 100 log lines
- ✅ Database <500MB
- ✅ Memory usage <10%
- ✅ Disk space >20% free

Your bots are **AT RISK** if:

- ⚠️ Win rates below 50%
- ⚠️ Circuit breaker triggered multiple times
- ⚠️ Memory usage >20%
- ⚠️ Many ERROR messages in logs
- ⚠️ No trades in 24+ hours (for active strategies)

Your bots are **IN TROUBLE** if:

- ❌ Negative total PnL
- ❌ Win rates <40%
- ❌ Bot crashed and won't restart
- ❌ Database corruption errors
- ❌ Out of disk space

---

## 🔗 RELATED DOCUMENTATION

- `GRID_AND_DIP_STRATEGIES_REFERENCE.md` - Expected performance benchmarks
- `docs/ARCHITECTURE_ENHANCEMENTS_AND_ROADMAP.md` - Enhancement roadmap
- `LIVE_TRADING_TRANSITION_GUIDE.md` - Production deployment checklist

---

**Last Updated:** 2026-01-06
**Next Review:** Weekly (every Sunday)
