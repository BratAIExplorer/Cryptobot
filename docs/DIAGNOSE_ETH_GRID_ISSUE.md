# Diagnostic Guide: ETH Grid Bot Not Trading

**Issue**: After 17+ hours (210+ cycles), test has only 2 BTC positions and ZERO ETH positions
**ETH Price**: $3,093 (IN RANGE: $2,800 - $4,200)
**Expected**: Should have ~5-10 positions total (BTC + ETH combined)

---

## Quick Diagnostics to Run on VPS

Run these commands on your VPS at `/root/cryptobot_v3`:

### 1. Check if ETH Bot is Being Evaluated

```bash
cd /root/cryptobot_v3

# Look for ETH bot evaluation messages
tail -1000 test_proven_config.log | grep "Test Grid Bot ETH"

# Expected output:
# [DEBUG] Evaluating Test Grid Bot ETH - Type: Grid
# ✅ Grid Bot ETH configured (PROVEN parameters)

# If you DON'T see evaluation messages, ETH bot is not running
```

### 2. Check for ETH Strategy Initialization

```bash
cd /root/cryptobot_v3

# Look for ETH grid initialization
tail -1000 test_proven_config.log | grep -E "DynamicGrid.*ETH|Initialized.*ETH"

# Expected output:
# [DynamicGrid] Initialized ETH/USDT: Dynamic ATR Mode (Mult: 2.5)
# [Grid] ETH/USDT: Initialized with static range $2800-$4200

# If missing, strategy instance wasn't created
```

### 3. Check for ETH-Specific Errors

```bash
cd /root/cryptobot_v3

# Look for any ETH errors
grep -i "eth" test_proven_config.log | grep -iE "error|exception|fail|traceback"

# Also check bot.log
grep -i "eth" bot.log | grep -iE "error|exception|fail|traceback" | tail -20
```

### 4. Check ETH Signal Generation

```bash
cd /root/cryptobot_v3

# Look for ETH BUY signals
tail -1000 test_proven_config.log | grep -E "ETH.*BUY|Grid Entry.*ETH"

# Look for ETH grid debug messages
tail -1000 test_proven_config.log | grep "GRID DEBUG.*ETH"

# Expected: Should see grid checking messages if bot is running
```

### 5. Check Budget/Exposure Limits

```bash
cd /root/cryptobot_v3

# Query database for exposure
sqlite3 data/test_adapter_binance_paper.db "
SELECT
    symbol,
    COUNT(*) as positions,
    ROUND(SUM(CASE WHEN status='OPEN' THEN buy_price * amount ELSE 0 END), 2) as total_exposure
FROM positions
GROUP BY symbol;
"

# Check for exposure warnings
tail -1000 test_proven_config.log | grep -i "exposure.*eth"
```

### 6. Full Cycle Output (Recent)

```bash
cd /root/cryptobot_v3

# Get last 3 complete cycles
tail -200 test_proven_config.log

# Look for:
# - "Evaluating Test Grid Bot ETH"
# - "[GRID] ETH/USDT: Checking BUY opportunities"
# - "[GRID DEBUG] ETH/USDT: Price=..."
```

---

## Possible Root Causes

### Scenario A: ETH Bot Not Created
**Symptom**: No "[DynamicGrid] Initialized ETH/USDT" message in logs
**Cause**: Strategy instance creation failed during `add_bot()`
**Fix**: Check for Python exceptions during startup

### Scenario B: ETH Bot Created But Not Evaluated
**Symptom**: Strategy initialized, but no "[DEBUG] Evaluating Test Grid Bot ETH" messages
**Cause**: Bot config may have been skipped in engine loop
**Fix**: Verify `active_bots` list contains both BTC and ETH

### Scenario C: ETH Bot Evaluated But No Signals
**Symptom**: Evaluation messages exist, but no "[GRID] ETH/USDT: Checking BUY opportunities"
**Cause**:
- Grid calculation failing silently
- Current price outside grid range (unlikely - we verified it's in range)
- All grid levels already have positions (unlikely - no positions exist)

### Scenario D: Signals Generated But Not Executed
**Symptom**: Grid BUY messages exist, but no trades executed
**Cause**:
- Exposure limit reached (check max_exposure_per_coin)
- Insufficient balance
- Exchange API error (paper trading shouldn't have this)
- Execute_trade failing for ETH specifically

---

## Expected Debug Output (Normal Operation)

If ETH bot is working correctly, you should see this pattern every cycle:

```
🔄 Cycle #XXX
====================================
[DEBUG] Evaluating Test Grid Bot BTC - Type: Grid
[GRID DEBUG] BTC/USDT: Price=$95000.00, Lower=$85000, Upper=$110000
[GRID] BTC/USDT: Checking BUY opportunities, grids=20

[DEBUG] Evaluating Test Grid Bot ETH - Type: Grid
[GRID DEBUG] ETH/USDT: Price=$3093.00, Lower=$2800, Upper=$4200
[GRID] ETH/USDT: Checking BUY opportunities, grids=30

📊 Active Positions: X
```

---

## Immediate Action Items

1. **Run Diagnostic 1**: Confirm ETH bot is being evaluated
   - If NO → Bot not added to active_bots (configuration issue)
   - If YES → Proceed to diagnostic 2

2. **Run Diagnostic 2**: Confirm ETH strategy initialized
   - If NO → Strategy creation failed (check for Python errors)
   - If YES → Proceed to diagnostic 3

3. **Run Diagnostic 3**: Check for ETH errors
   - If ERRORS found → Fix the specific error
   - If NO errors → Proceed to diagnostic 4

4. **Run Diagnostic 4**: Check signal generation
   - If NO signals → Grid calculation issue
   - If signals exist → Proceed to diagnostic 5

5. **Run Diagnostic 5**: Check if signals are being executed
   - If execution failing → Identify why execute_trade is blocking

---

## What to Report Back

Please run the diagnostics and share:

1. Output of Diagnostic #1 (ETH evaluation check)
2. Output of Diagnostic #2 (ETH initialization check)
3. Full output of Diagnostic #6 (last 200 lines of log)

This will help identify exactly where in the flow ETH bot is failing.

---

## Theory: Most Likely Causes

Based on the symptoms (17 hours, only BTC trading, ETH not trading at all):

**Most Likely**: ETH bot strategy instance not created or not in active_bots list
- This would explain complete absence of ETH trades
- BTC working suggests Grid logic itself is fine
- Configuration or initialization issue specific to second bot

**Less Likely**: Grid calculation failing for ETH
- Would still see evaluation messages
- Would see error logs

**Unlikely**: Market conditions preventing trading
- Price confirmed in range
- Grid should trigger at multiple levels across range
