# Adapter Pattern - Paper Trading Test Quick Start

**Date**: 2026-01-09
**Purpose**: Test adapter architecture core with ZERO risk
**Duration**: 24-48 hours recommended
**VPS Path**: `/root/cryptobot_v3`

---

## What This Test Does

✅ Tests adapter pattern core (Factory + MEXC Adapter)
✅ Runs Grid Bot BTC with proven parameters
✅ Paper trading only (NO real money)
✅ Isolated database (won't affect old bots)
✅ Simple monitoring and validation

❌ Does NOT test Priority 1 enhancements yet (health monitor, config manager, enhanced base)
❌ Does NOT affect your running LIVE bots in `/Antigravity/...`

---

## Prerequisites

Before starting, ensure:
- ✅ You're on VPS at `/root/cryptobot_v3`
- ✅ Branch `feature/adapter-refactor` is checked out and up-to-date
- ✅ Your LIVE bots in `/Antigravity/...` are running normally
- ✅ You have MEXC API keys configured (for paper mode data access)

---

## Step 1: Prepare Environment

```bash
cd /root/cryptobot_v3

# Verify branch
git status
# Should show: On branch feature/adapter-refactor

# Check API keys (paper mode still needs them for market data)
grep -E "MEXC_API_KEY|MEXC_SECRET_KEY" .env* 2>/dev/null || echo "Need to set API keys"

# If API keys not set, create/update .env file
# nano .env
# Add:
# MEXC_API_KEY=your_api_key_here
# MEXC_SECRET_KEY=your_secret_key_here
```

---

## Step 2: Start Test

```bash
cd /root/cryptobot_v3

# Option A: Run in foreground (see live output)
python3 test_adapter_paper.py

# Option B: Run in background (recommended)
nohup python3 test_adapter_paper.py > test_adapter.log 2>&1 &

# Option C: Run in screen (can detach/reattach)
screen -S adapter-test
python3 test_adapter_paper.py
# Press Ctrl+A then D to detach
# screen -r adapter-test to reattach
```

---

## Step 3: Monitor Test (During 24-48 hours)

### Quick Status Check
```bash
cd /root/cryptobot_v3

# Check if running
ps aux | grep test_adapter_paper.py | grep -v grep

# Check recent logs
tail -50 test_adapter.log  # if using nohup
tail -50 bot.log           # engine logs

# Check for errors
grep -E "ERROR|Exception|CRITICAL" test_adapter.log | tail -20
grep -E "ERROR|Exception|CRITICAL" bot.log | tail -20
```

### Performance Check
```bash
cd /root/cryptobot_v3

# Check database for trades
sqlite3 data/test_adapter_mexc_paper.db "SELECT COUNT(*) as total_positions FROM positions;"

# Check open positions
sqlite3 data/test_adapter_mexc_paper.db "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;"

# Check closed trades (after a few hours)
sqlite3 data/test_adapter_mexc_paper.db "
SELECT
    COUNT(*) as closed_trades,
    ROUND(SUM(realized_pnl), 2) as total_pnl,
    ROUND(AVG(realized_pnl), 2) as avg_pnl
FROM positions
WHERE status='CLOSED' AND realized_pnl IS NOT NULL;
"

# Check recent activity
sqlite3 data/test_adapter_mexc_paper.db "
SELECT
    symbol,
    status,
    ROUND(realized_pnl, 2) as pnl,
    datetime(entry_time) as entry
FROM positions
ORDER BY entry_time DESC
LIMIT 10;
"
```

### Adapter Health Check
```bash
# Check kill switch status
grep "Kill Switch" test_adapter.log | tail -5

# Check adapter initialization
grep "Adapter:" test_adapter.log | head -5

# Check for adapter errors
grep -i "adapter" bot.log | grep -iE "error|fail|exception" | tail -10
```

---

## Step 4: Compare with Benchmarks

After 24 hours, compare results with proven parameters:

| Metric | Expected (from docs) | Actual | Status |
|--------|---------------------|--------|---------|
| Trades/day | 5-10 grid fills | ? | ✅/❌ |
| Avg profit/trade | ~$1.50 | ? | ✅/❌ |
| Grid range | $85K-$110K | ? | ✅/❌ |
| Errors | 0-2 minor | ? | ✅/❌ |
| Kill switch trips | 0 | ? | ✅/❌ |

**Success Criteria**:
- ✅ No critical errors
- ✅ Trades executing in grid range
- ✅ Profit per trade close to $1.50
- ✅ No kill switch activations
- ✅ Database logging working

---

## Step 5: Stop Test

### Graceful Shutdown
```bash
cd /root/cryptobot_v3

# Create stop signal
touch STOP_SIGNAL

# Wait for graceful shutdown (up to 5 minutes)
# Check if stopped
ps aux | grep test_adapter_paper.py | grep -v grep
```

### Force Stop (if needed)
```bash
# Find PID
ps aux | grep test_adapter_paper.py | grep -v grep

# Kill process
kill <PID>

# Or kill all instances
pkill -f test_adapter_paper.py
```

---

## Step 6: Review Results

```bash
cd /root/cryptobot_v3

# Full stats query
sqlite3 data/test_adapter_mexc_paper.db "
SELECT
    'Total Positions' as metric,
    COUNT(*) as value
FROM positions
UNION ALL
SELECT
    'Closed Trades',
    COUNT(*)
FROM positions
WHERE status='CLOSED'
UNION ALL
SELECT
    'Total PnL',
    ROUND(SUM(realized_pnl), 2)
FROM positions
WHERE status='CLOSED'
UNION ALL
SELECT
    'Win Rate %',
    ROUND(100.0 * SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM positions
WHERE status='CLOSED';
"

# Check for anomalies
echo "=== Checking for anomalies ==="
grep -c "ERROR" bot.log
grep -c "Exception" bot.log
grep -c "Kill Switch ACTIVE" test_adapter.log
```

---

## Decision Tree After Test

### ✅ Test PASSED (Expected Results)
- Trades executing normally
- PnL close to benchmarks
- No critical errors
- Kill switch never activated

**Next Step**:
- Keep running for full 48 hours
- Then proceed to **Milestone 2: Integrate Priority 1 Enhancements**

---

### ⚠️ Test PARTIAL (Minor Issues)
- Trades executing but slower than expected
- PnL slightly off benchmarks
- 1-2 minor errors

**Next Step**:
- Investigate minor issues
- Check API key permissions
- Verify market conditions (BTC price in range?)
- Fix and re-test

---

### ❌ Test FAILED (Critical Issues)
- No trades executed
- Critical errors in logs
- Kill switch activated
- Database not updating

**Next Step**:
- Review error logs thoroughly
- Check adapter implementation
- Verify API keys and permissions
- Report issue with full error logs

---

## Comparison with OLD Bots

While test runs, also check your LIVE bots for comparison:

```bash
# OLD LIVE bot performance (last 24h)
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE
sqlite3 data/trades_v3_live.db "
SELECT
    COUNT(*) as trades,
    ROUND(SUM(realized_pnl), 2) as pnl
FROM positions
WHERE exit_time > datetime('now', '-24 hours')
AND status='CLOSED';
"

# NEW adapter test performance (last 24h)
cd /root/cryptobot_v3
sqlite3 data/test_adapter_mexc_paper.db "
SELECT
    COUNT(*) as trades,
    ROUND(SUM(realized_pnl), 2) as pnl
FROM positions
WHERE exit_time > datetime('now', '-24 hours')
AND status='CLOSED';
"
```

**Note**: Paper trading results won't match LIVE exactly (different slippage, fills), but pattern should be similar.

---

## Safety Notes

✅ **What's SAFE**:
- This test is paper trading only
- Old LIVE bots completely unaffected
- Separate database (no data conflicts)
- Can stop anytime with zero impact
- Can delete test database and restart

⚠️ **What to AVOID**:
- Don't modify old bot directories during test
- Don't use same database as LIVE bots
- Don't run multiple test instances (database conflicts)
- Don't switch to LIVE mode without full validation

---

## Troubleshooting

### Test won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip3 list | grep -E "ccxt|pandas|requests"

# Check file permissions
ls -la test_adapter_paper.py  # Should be readable
```

### No trades executing
```bash
# Check BTC price is in grid range
# Grid: $85,000 - $110,000
# If BTC outside range, grid won't trade

# Check API key permissions
grep "API" bot.log | grep -i "error\|fail" | tail -5

# Check kill switch
grep "Kill Switch" bot.log | tail -5
```

### Database errors
```bash
# Check database file
ls -la data/test_adapter_mexc_paper.db

# Check for locks
lsof data/test_adapter_mexc_paper.db 2>/dev/null || echo "Not locked"

# If locked by old process, stop it
pkill -f test_adapter_paper.py
rm data/test_adapter_mexc_paper.db  # Remove and restart
```

---

## Expected Timeline

- **Hour 0-1**: Bot starts, initializes adapter, fetches market data
- **Hour 1-4**: First grid levels placed (if BTC in range)
- **Hour 4-12**: First grid fills and re-buys (should see 2-5 trades)
- **Hour 12-24**: Consistent grid trading (5-10 trades)
- **Hour 24-48**: Validate stability and performance

---

## What Happens Next

### After Successful Test
1. ✅ Adapter core validated
2. 📋 Document results
3. 🚀 Proceed to Milestone 2: Integrate Priority 1 Enhancements
4. 🧪 Test enhancements in paper mode (another 1-2 weeks)
5. 🎯 Consider LIVE migration (only after full validation)

### If Test Needs Improvement
1. 🔍 Analyze issues
2. 🛠️ Fix problems
3. 🔄 Re-test
4. ✅ Validate before proceeding

---

## Questions to Answer

After test completion:

- ✅ Did adapter pattern work as expected?
- ✅ Were trades executed correctly?
- ✅ Did database logging work?
- ✅ Was PnL calculation accurate?
- ✅ Did kill switch behave correctly?
- ✅ Were there any critical errors?
- ✅ Is performance similar to old architecture?

If all answers are YES, proceed to Milestone 2.
If any NO, investigate and fix before proceeding.

---

## Support Files

Related documentation:
- `docs/CURRENT_ARCHITECTURE_STATUS.md` - Architecture status
- `docs/GRID_AND_DIP_STRATEGIES_REFERENCE.md` - Proven parameters
- `docs/ARCHITECTURE_ENHANCEMENTS_AND_ROADMAP.md` - Full roadmap
- `docs/BOT_STATUS_REVIEW_GUIDE.md` - Monitoring guide

---

**Remember**: This is a TEST. Take your time. Don't rush to LIVE trading. The goal is to validate the adapter core works correctly before integrating more complex features.
