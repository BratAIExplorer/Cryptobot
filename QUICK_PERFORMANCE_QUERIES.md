# Quick Performance Queries

Run these on VPS to check bot performance.

## Setup

```bash
cd /root/cryptobot_v3
DB="data/test_adapter_binance_paper.db"
```

---

## 🚀 Quick Checks (Copy-Paste)

### 1. Position Summary by Symbol & Status

```bash
sqlite3 $DB "SELECT symbol, status, COUNT(*) as count FROM positions GROUP BY symbol, status;"
```

**Expected Output** (after 24 hours):
```
BTC/USDT|OPEN|2-5
ETH/USDT|OPEN|1-3
```

---

### 2. Total Positions Created

```bash
sqlite3 $DB "SELECT COUNT(*) as total_positions FROM positions;"
```

**Expected**: 3-8 positions after 24 hours

---

### 3. Positions in Last 24 Hours

```bash
sqlite3 $DB "SELECT symbol, COUNT(*) as count_24h FROM positions WHERE datetime(buy_timestamp) > datetime('now', '-24 hours') GROUP BY symbol;"
```

**Expected**: Both BTC and ETH should show activity

---

### 4. Profit/Loss Summary

```bash
sqlite3 $DB "SELECT symbol, COUNT(*) as closed, ROUND(SUM(profit), 2) as total_pnl, ROUND(AVG(profit), 2) as avg_pnl FROM positions WHERE status='CLOSED' GROUP BY symbol;"
```

**Expected**: May be 0 initially (positions need time to close)

---

### 5. Overall P&L

```bash
sqlite3 $DB "SELECT ROUND(SUM(profit), 2) as total_pnl FROM positions WHERE status='CLOSED';"
```

**Expected**: Small positive number (+$1 to +$5 after 24h)

---

### 6. Win Rate

```bash
sqlite3 $DB "SELECT symbol, COUNT(*) as total, SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins, ROUND(100.0 * SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) || '%' as win_rate FROM positions WHERE status='CLOSED' GROUP BY symbol;"
```

**Expected**: 80%+ win rate

---

### 7. Open Positions Detail

```bash
sqlite3 $DB ".mode column" ".headers on" "SELECT id, symbol, ROUND(buy_price, 2) as price, datetime(buy_timestamp) as opened FROM positions WHERE status='OPEN' ORDER BY buy_timestamp DESC;"
```

---

### 8. Most Recent Position

```bash
sqlite3 $DB "SELECT id, symbol, status, ROUND(buy_price, 2) as price, datetime(buy_timestamp) as time FROM positions ORDER BY buy_timestamp DESC LIMIT 1;"
```

**Shows**: When last position was created

---

### 9. Bot Status

```bash
sqlite3 $DB ".mode column" ".headers on" "SELECT name, status, total_trades, ROUND(total_pnl, 2) as pnl, ROUND(wallet_balance, 2) as balance FROM bots;"
```

**Expected**:
- Status: RUNNING
- Both BTC and ETH bots listed
- Balance: ~$500 total

---

### 10. Check Exchange (Verify BINANCE only)

```bash
sqlite3 $DB "SELECT exchange, COUNT(*) FROM positions GROUP BY exchange;"
```

**Expected Output**:
```
BINANCE|X
```

**Should NOT see MEXC or LUNO**

---

## 🔍 Detailed Analysis

### Hourly Activity (Last 24 Hours)

```bash
sqlite3 $DB ".mode column" ".headers on" "SELECT strftime('%Y-%m-%d %H:00', buy_timestamp) as hour, COUNT(*) as positions FROM positions WHERE datetime(buy_timestamp) > datetime('now', '-24 hours') GROUP BY hour ORDER BY hour DESC;"
```

Shows position creation by hour

---

### All Trades (Last 24 Hours)

```bash
sqlite3 $DB ".mode column" ".headers on" "SELECT symbol, side, COUNT(*) as count, ROUND(AVG(price), 2) as avg_price FROM trades WHERE datetime(timestamp) > datetime('now', '-24 hours') GROUP BY symbol, side;"
```

Shows BUY vs SELL activity

---

### Oldest Open Position Age

```bash
sqlite3 $DB "SELECT symbol, ROUND((julianday('now') - julianday(buy_timestamp)) * 24, 1) || ' hours' as age FROM positions WHERE status='OPEN' ORDER BY buy_timestamp ASC LIMIT 1;"
```

---

### Grid Bot Activity Check

```bash
sqlite3 $DB "SELECT strategy, COUNT(*) FROM positions GROUP BY strategy;"
```

**Expected**:
```
Test Grid Bot BTC|X
Test Grid Bot ETH|Y
```

Both should show activity

---

## 🚨 Health Checks

### Check for RISK STOP Issues

**Not in database - check logs:**
```bash
cd /root/cryptobot_v3
grep "RISK STOP" test_proven_config.log | tail -5
```

**Expected**: Should be EMPTY (no RISK STOP since fix)

---

### Check Both Bots Evaluating

```bash
cd /root/cryptobot_v3
tail -200 test_proven_config.log | grep "DEBUG.*Evaluating"
```

**Expected**:
```
[DEBUG] Evaluating Test Grid Bot BTC - Type: Grid
[DEBUG] Evaluating Test Grid Bot ETH - Type: Grid
```

Both should appear

---

### Check Grid Activity

```bash
cd /root/cryptobot_v3
tail -200 test_proven_config.log | grep "GRID DEBUG"
```

**Expected**:
```
[GRID DEBUG] BTC/USDT: Price=$..., Lower=$85000, Upper=$110000
[GRID DEBUG] ETH/USDT: Price=$..., Lower=$2800, Upper=$4200
```

---

## 📊 Benchmark Comparison

### After 24 Hours (Expected)

| Metric | Expected | Check Query |
|--------|----------|-------------|
| Total Positions | 3-8 | `SELECT COUNT(*) FROM positions;` |
| BTC Positions | 2-5 | `SELECT COUNT(*) FROM positions WHERE symbol='BTC/USDT';` |
| ETH Positions | 1-3 | `SELECT COUNT(*) FROM positions WHERE symbol='ETH/USDT';` |
| Closed Trades | 0-2 | `SELECT COUNT(*) FROM positions WHERE status='CLOSED';` |
| Win Rate | 80%+ | See query #6 above |
| Exchange | BINANCE only | See query #10 above |

### After 48 Hours (Expected)

| Metric | Expected |
|--------|----------|
| Total Positions | 10-20 |
| Closed Trades | 5-10 |
| Total P&L | +$5 to +$20 |
| Win Rate | 80-95% |
| Errors | 0 critical |

---

## 🎯 Success Criteria

**Test PASSES if** (after 48 hours):
- ✅ Both BTC and ETH have created positions
- ✅ No RISK STOP messages in logs
- ✅ Win rate 80%+
- ✅ Positive P&L
- ✅ Zero critical errors
- ✅ All positions on BINANCE exchange

**Test FAILS if**:
- ❌ Only one bot trading (BTC or ETH)
- ❌ RISK STOP blocking trades
- ❌ Win rate < 70%
- ❌ Critical errors or crashes
- ❌ MEXC or LUNO positions appear

---

## 🔄 Running Full Performance Check

**Automated script** (runs all queries above):

```bash
cd /root/cryptobot_v3
bash check_bot_performance.sh
```

Generates comprehensive report with all metrics.

---

## 📅 When to Check

**First 6 Hours**: Every hour
- Verify both bots creating positions
- Confirm no RISK STOP
- Check logs for errors

**6-24 Hours**: Every 4-6 hours
- Monitor position count increasing
- Check for any closed trades with profit
- Verify steady activity

**24-48 Hours**: Every 12 hours
- Check overall P&L
- Verify win rate
- Prepare for GO/NO-GO decision

**At 48 Hours**: Final evaluation
- Run full performance check
- Compare vs expected benchmarks
- Make production deployment decision
