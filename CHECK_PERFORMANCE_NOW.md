# 📊 Check Bot Performance NOW

**Run these commands on your VPS to check current test performance**

---

## 🚀 QUICK STATUS CHECK

```bash
cd /root/cryptobot_v3

# 1. Quick Monitor (Shows overall health)
bash monitor_bot.sh
```

**Expected Output**:
- 🟢 HEALTHY = Bots trading, no blockers
- 🟡 STARTING = Still initializing (wait 10 min)
- 🔴 BLOCKED = Check for errors

---

## 📊 DETAILED PERFORMANCE ANALYSIS

### **Command 1: Position Summary**
```bash
cd /root/cryptobot_v3

sqlite3 data/test_adapter_binance_paper.db "
SELECT
    symbol,
    status,
    COUNT(*) as count,
    ROUND(AVG(entry_price), 2) as avg_entry_price
FROM positions
GROUP BY symbol, status;
"
```

**What to Look For**:
```
BTC/USDT|OPEN|5|90250.00     ← 5 open BTC positions, avg entry $90,250
ETH/USDT|OPEN|3|3100.50      ← 3 open ETH positions, avg entry $3,100
BTC/USDT|CLOSED|2|89800.00   ← 2 closed BTC positions (completed trades)
```

---

### **Command 2: Total Positions Created**
```bash
cd /root/cryptobot_v3

sqlite3 data/test_adapter_binance_paper.db "
SELECT COUNT(*) as total_positions FROM positions;
"
```

**What to Look For**:
```
10-20   = Good progress (first 12 hours)
20-40   = Excellent (24 hours)
40+     = Outstanding (48 hours)
```

---

### **Command 3: Win Rate & Profit Analysis**
```bash
cd /root/cryptobot_v3

# Note: In paper mode, profit calculation may be simplified
# This query shows closed positions
sqlite3 data/test_adapter_binance_paper.db "
SELECT
    symbol,
    COUNT(*) as closed_positions
FROM positions
WHERE status='CLOSED'
GROUP BY symbol;
"
```

---

### **Command 4: Recent Activity (Last 10 Positions)**
```bash
cd /root/cryptobot_v3

sqlite3 data/test_adapter_binance_paper.db "
SELECT
    symbol,
    quantity,
    entry_price,
    status,
    datetime(created_at) as created
FROM positions
ORDER BY id DESC
LIMIT 10;
"
```

**What to Look For**:
- Recent timestamps (within last hour = bot is active)
- Mix of BTC and ETH (both bots working)
- Reasonable entry prices (BTC: $85K-$110K, ETH: $2.8K-$4.2K)

---

### **Command 5: Hourly Activity Breakdown**
```bash
cd /root/cryptobot_v3

sqlite3 data/test_adapter_binance_paper.db "
SELECT
    strftime('%Y-%m-%d %H:00', created_at) as hour,
    COUNT(*) as positions_created
FROM positions
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;
"
```

**What to Look For**:
```
2026-01-12 15:00|3    ← 3 positions in 3pm hour
2026-01-12 14:00|5    ← 5 positions in 2pm hour
2026-01-12 13:00|2    ← 2 positions in 1pm hour
```
This shows trading frequency over time.

---

### **Command 6: Exchange Verification**
```bash
cd /root/cryptobot_v3

sqlite3 data/test_adapter_binance_paper.db "
SELECT exchange, COUNT(*) as count
FROM positions
GROUP BY exchange;
"
```

**Expected Output**:
```
BINANCE|15    ← All positions should be BINANCE only
```

**Red Flag**: If you see MEXC, there's still contamination!

---

## 📈 COMPREHENSIVE PERFORMANCE SCRIPT

```bash
cd /root/cryptobot_v3

# Run the comprehensive check script
bash check_bot_performance.sh
```

This will show all of the above in one report.

---

## 📝 CHECK LOG FOR RECENT ACTIVITY

### **Last 30 Lines (Quick View)**
```bash
cd /root/cryptobot_v3
tail -30 test_proven_config.log
```

**Look For**:
```
✅ [GRID] Bypassing confluence check
[BUY] BTC/USDT: Opening $25 position at $90,671.32
✅ Grid Bot BTC configured (Risk Manager compliant)
```

**Red Flags**:
```
[SKIP] Risk Manager Reject    ← Still blocking! (shouldn't happen with AGGRESSIVE)
RISK STOP: Daily loss limit   ← Bot stopped trading
Drawdown limit exceeded        ← Bot paused
```

---

### **Check for BUY Orders (Last 100 Lines)**
```bash
cd /root/cryptobot_v3
tail -100 test_proven_config.log | grep "BUY"
```

**Expected**:
```
[Test Grid Bot BTC] Grid BUY Signal: Grid Entry at 90263.16
[Test Grid Bot ETH] Grid BUY Signal: Grid Entry at 3089.66
```

---

### **Check for Risk Manager Rejections**
```bash
cd /root/cryptobot_v3
tail -200 test_proven_config.log | grep "SKIP"
```

**Expected**: EMPTY (no rejections with AGGRESSIVE profile)

**If you see rejections**: Risk Manager is still blocking - need to investigate

---

## 🕐 TEST RUNTIME CALCULATOR

```bash
cd /root/cryptobot_v3

# Get test start time from log
head -50 test_proven_config.log | grep "STARTING ADAPTER TEST"

# Get current time
date

# Calculate hours elapsed
```

---

## 🎯 PERFORMANCE BENCHMARKS

### **By Runtime**:

| Hours Elapsed | Min Positions | Target Positions | Excellent |
|--------------|---------------|------------------|-----------|
| 1-2 hours | 0-1 | 2-3 | 4+ |
| 4-6 hours | 2-4 | 5-8 | 10+ |
| 12 hours | 5-10 | 10-15 | 20+ |
| 24 hours | 10-20 | 20-30 | 40+ |
| 48 hours | 20-40 | 40-60 | 80+ |

---

## 🚨 TROUBLESHOOTING

### **If Position Count = 0 After 2+ Hours**:

**Check 1: Process Running?**
```bash
ps aux | grep test_adapter_paper.py
```

**Check 2: Log Has Activity?**
```bash
tail -50 test_proven_config.log | grep "Cycle #"
```

**Check 3: Any Errors?**
```bash
tail -100 test_proven_config.log | grep -i "error\|exception"
```

**Check 4: Risk Manager Blocking?**
```bash
tail -100 test_proven_config.log | grep "SKIP\|RISK STOP\|Drawdown"
```

---

### **If Only BTC or Only ETH Trading**:

**Check Both Bots Evaluating**:
```bash
tail -100 test_proven_config.log | grep "Evaluating Test Grid Bot"
```

**Expected**:
```
[DEBUG] Evaluating Test Grid Bot BTC - Type: Grid
[DEBUG] Evaluating Test Grid Bot ETH - Type: Grid
```

**If missing one**: That bot isn't being evaluated - check config

---

## 📊 EXPECTED PERFORMANCE SNAPSHOT

### **After 6-12 Hours** (Healthy Test):
```bash
$ sqlite3 data/test_adapter_binance_paper.db "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;"

BTC/USDT|OPEN|3
BTC/USDT|CLOSED|2
ETH/USDT|OPEN|4
ETH/USDT|CLOSED|3

Total: 12 positions (5 closed, 7 open)
```

---

## 📞 REPORT RESULTS

After running the checks, please provide:

1. **Monitor Output**:
   ```bash
   bash monitor_bot.sh
   ```
   Copy full output

2. **Position Summary**:
   ```bash
   sqlite3 data/test_adapter_binance_paper.db "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;"
   ```
   Copy output

3. **Runtime**:
   - When did test start?
   - How many hours elapsed?

4. **Any Errors?**:
   ```bash
   tail -50 test_proven_config.log
   ```
   Copy last 50 lines

---

**I can then analyze and tell you**:
- ✅ Is performance matching expectations?
- ✅ Are both bots trading?
- ✅ Win rate and profit trends
- ⚠️ Any issues to address
- 🎯 Projected 48-hour results

---

## 🎯 QUICK HEALTH CHECK (1 Command)

```bash
cd /root/cryptobot_v3 && echo "=== QUICK HEALTH CHECK ===" && echo "" && echo "Test Running:" && ps aux | grep test_adapter_paper.py | grep -v grep && echo "" && echo "Total Positions:" && sqlite3 data/test_adapter_binance_paper.db "SELECT COUNT(*) FROM positions;" && echo "" && echo "By Symbol:" && sqlite3 data/test_adapter_binance_paper.db "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;" && echo "" && echo "Last 5 Positions:" && sqlite3 data/test_adapter_binance_paper.db "SELECT symbol, ROUND(entry_price,2), status, datetime(created_at) FROM positions ORDER BY id DESC LIMIT 5;"
```

Copy-paste this ONE command for instant health report!
