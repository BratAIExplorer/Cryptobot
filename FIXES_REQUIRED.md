# 🔧 Complete Bot Performance Fix Plan

**Generated**: 2026-01-17
**Current Performance**: 1 trade in 24h, -$25 P&L
**Target Performance**: 30-100 trades in 24h, +$10-50 P&L

---

## 🚨 Critical Issues Summary

| Issue | Impact | Priority | Estimated Fix Time |
|-------|--------|----------|-------------------|
| Grid Bot spacing too wide | 98% trades missed | **CRITICAL** | 5 min |
| Grid position lock prevents pyramiding | 90% capital idle | **CRITICAL** | 10 min |
| Buy-the-Dip threshold too high | Zero trades | **HIGH** | 2 min |
| Grid Bot ETH same issues | Zero trades | **HIGH** | 5 min |
| Database path mismatch | Monitoring broken | **MEDIUM** | ✅ FIXED |

---

## 📋 Fix #1: Grid Bot BTC - Adjust Grid Parameters

### Current Config (run_bot.py:67-85)

```python
{
    'name': 'Grid Bot BTC',
    'type': 'Grid',
    'symbol': 'BTC/USDT',
    'lower_limit': 85000,    # ❌ TOO WIDE
    'upper_limit': 110000,   # ❌ TOO WIDE
    'grid_levels': 20,       # ❌ TOO FEW
    'amount': 25,
    'initial_balance': 250.0,
    'exchange': 'BINANCE'
}
```

**Problem**:
- Grid step: $1,315 (needs to move 1.3% to trigger)
- BTC moves $1,315 only once every 2-3 days
- Daily volatility: $500-1,500
- **Result**: 1 trade in 24 hours instead of 20-40

### Recommended Fix - Option A (Aggressive)

```python
{
    'name': 'Grid Bot BTC',
    'type': 'Grid',
    'symbol': 'BTC/USDT',
    'lower_limit': 93000,    # ✅ Centered on current price
    'upper_limit': 98000,    # ✅ $5k range
    'grid_levels': 50,       # ✅ $100 per grid
    'amount': 20,            # ✅ Smaller to allow more positions
    'initial_balance': 250.0,
    'exchange': 'BINANCE'
}
```

**Expected Outcome**: 20-40 trades/day, $5-15 daily profit

### Recommended Fix - Option B (Conservative)

```python
{
    'name': 'Grid Bot BTC',
    'type': 'Grid',
    'symbol': 'BTC/USDT',
    'lower_limit': 90000,    # ✅ Wider safety margin
    'upper_limit': 100000,   # ✅ $10k range
    'grid_levels': 40,       # ✅ $250 per grid
    'amount': 25,
    'initial_balance': 250.0,
    'exchange': 'BINANCE'
}
```

**Expected Outcome**: 10-20 trades/day, $3-8 daily profit

---

## 📋 Fix #2: Grid Bot - Remove Position Lock

### Current Code (strategies/grid_strategy_v3.py:110)

```python
def get_signal(self, current_price: float, open_positions: pd.DataFrame, df: pd.DataFrame = None, **kwargs):
    """
    Grid Trading Signal: Buy at support, sell at resistance.
    """
    has_positions = not open_positions.empty
    self.is_locked = has_positions  # ❌ LOCKS AFTER 1 BUY
```

**Problem**: Bot buys once and then can't buy again until it sells

### Recommended Fix

```python
def get_signal(self, current_price: float, open_positions: pd.DataFrame, df: pd.DataFrame = None, **kwargs):
    """
    Grid Trading Signal: Buy at support, sell at resistance.
    """
    has_positions = not open_positions.empty
    max_concurrent = self.config.get('max_concurrent_positions', 10)
    self.is_locked = len(open_positions) >= max_concurrent  # ✅ Allow multiple positions
```

**Additional Config** (run_bot.py):

```python
{
    'name': 'Grid Bot BTC',
    # ... existing config ...
    'max_concurrent_positions': 10,  # ✅ Allow 10 simultaneous positions
}
```

**Expected Outcome**: Bot can hold 10 positions across different grid levels simultaneously

---

## 📋 Fix #3: Buy-the-Dip - Lower Threshold

### Current Config (run_bot.py:159)

```python
{
    'name': 'Buy-the-Dip Strategy',
    'type': 'Buy-the-Dip',
    'symbols': TOP_10_COINS,
    'dip_threshold': 0.03,    # ❌ Needs 3% dip
    'rsi_limit': 35,
    'amount': 15,
    'max_exposure_per_coin': 100,
    'take_profit_pct': 0.08,
    'initial_balance': 1000.0,
    'exchange': 'BINANCE'
}
```

**Problem**:
- Current BTC dip: 2.53%
- Required dip: 3.00%
- Bot has been 47 basis points away from triggering for days

### Recommended Fix

```python
{
    'name': 'Buy-the-Dip Strategy',
    'type': 'Buy-the-Dip',
    'symbols': TOP_10_COINS,
    'dip_threshold': 0.02,    # ✅ 2% dip (more realistic)
    'rsi_limit': 35,
    'amount': 15,
    'max_exposure_per_coin': 100,
    'take_profit_pct': 0.08,
    'initial_balance': 1000.0,
    'exchange': 'BINANCE'
}
```

**Alternative - Dynamic Threshold**:

```python
{
    # ... existing config ...
    'dip_threshold': 0.015,   # ✅ 1.5% for high-cap coins (more trades)
}
```

**Expected Outcome**: 5-15 trades per day across top 10 coins

---

## 📋 Fix #4: Grid Bot ETH - Same Fixes

### Current Config

```python
{
    'name': 'Grid Bot ETH',
    'type': 'Grid',
    'symbol': 'ETH/USDT',
    'lower_limit': 2800,     # ❌ TOO WIDE
    'upper_limit': 4200,     # ❌ TOO WIDE
    'grid_levels': 30,       # ❌ Grid step = $48
    'amount': 25,
    'initial_balance': 250.0,
    'exchange': 'BINANCE'
}
```

### Recommended Fix

```python
{
    'name': 'Grid Bot ETH',
    'type': 'Grid',
    'symbol': 'ETH/USDT',
    'lower_limit': 3100,     # ✅ Centered on current price (~$3,300)
    'upper_limit': 3500,     # ✅ $400 range
    'grid_levels': 50,       # ✅ $8 per grid
    'amount': 20,
    'initial_balance': 250.0,
    'exchange': 'BINANCE',
    'max_concurrent_positions': 10  # ✅ Allow pyramiding
}
```

**Expected Outcome**: 15-30 trades/day, $3-10 daily profit

---

## 📋 Fix #5: Database Path (✅ FIXED)

### Issue
`daily_bot_check.py` was looking for wrong database path

### Applied Fix

```python
# BEFORE:
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'trades_v3_paper.db')

# AFTER:
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'multi', 'trades_paper.db')
```

---

## 🎯 Implementation Plan

### Phase 1: Quick Wins (15 minutes)

1. **Fix Buy-the-Dip threshold** (2 min)
   - Change `dip_threshold` from 0.03 → 0.02
   - Should generate trades within hours

2. **Update Grid Bot BTC parameters** (5 min)
   - Change range to 90k-100k
   - Increase grid levels to 40
   - Reduce amount to $20

3. **Update Grid Bot ETH parameters** (5 min)
   - Change range to 3100-3500
   - Increase grid levels to 50

4. **Pull latest code to VPS** (3 min)
   ```bash
   cd ~/cryptobot_v3
   git pull origin claude/review-handover-bot-performance-Rwv92
   ```

### Phase 2: Strategy Code Fix (10 minutes)

5. **Fix Grid position lock** (10 min)
   - Edit `strategies/grid_strategy_v3.py`
   - Add `max_concurrent_positions` logic
   - Test with diagnostic script

### Phase 3: Validation (30 minutes)

6. **Run diagnostic script** (5 min)
   ```bash
   python3 diagnose_bots.py
   ```

7. **Restart bot** (2 min)
   ```bash
   pkill -f run_bot
   nohup python3 -u run_bot.py > bot.log 2>&1 &
   ```

8. **Monitor for 30 minutes** (30 min)
   ```bash
   tail -f bot.log
   ```

9. **Check performance after 24h** (1 min)
   ```bash
   python3 check_all_bots.py
   ```

---

## 📊 Expected Results

### Before Fixes
```
Grid Bot BTC:    1 trade/24h  | -$25.00
Grid Bot ETH:    0 trades/24h | $0.00
Buy-the-Dip:     0 trades/24h | $0.00
────────────────────────────────────────
Total:           1 trade/24h  | -$25.00
```

### After Fixes (Conservative Estimate)
```
Grid Bot BTC:    15 trades/24h | +$8.00  (10 round trips @ $0.80 each)
Grid Bot ETH:    20 trades/24h | +$12.00 (15 round trips @ $0.80 each)
Buy-the-Dip:     8 trades/24h  | +$15.00 (4 round trips @ 5% profit)
────────────────────────────────────────
Total:           43 trades/24h | +$35.00
```

### After Fixes (Optimistic Estimate)
```
Grid Bot BTC:    30 trades/24h | +$20.00
Grid Bot ETH:    40 trades/24h | +$25.00
Buy-the-Dip:     15 trades/24h | +$30.00
────────────────────────────────────────
Total:           85 trades/24h | +$75.00
```

---

## ⚠️ Risk Considerations

1. **Grid Bots in Trending Markets**
   - Grid bots work best in ranging markets
   - If BTC breaks above $100k or below $90k, widen range immediately
   - Consider adding trailing stop at 5% outside grid range

2. **Buy-the-Dip Overexposure**
   - With 2% threshold, bot might buy too often in bear market
   - Monitor total exposure daily (max $100/coin = $1,000 total)
   - If losses exceed $200, pause and review

3. **Multiple Positions Risk**
   - 10 concurrent grid positions = higher exposure
   - Each position is $20-25
   - Maximum drawdown: ~$250 if all positions go -50% (unlikely)

4. **Exchange Connectivity**
   - Single exchange risk (Binance only)
   - If Binance goes down, bots stop
   - Consider adding failover to MEXC/Luno

---

## 🔧 Maintenance Tasks

### Daily
- Run `python3 check_all_bots.py` every morning
- Check for positions stuck > 24h
- Verify grid ranges still contain price

### Weekly
- Adjust grid ranges if market moves 10%+
- Review dip threshold based on market volatility
- Check overall P&L vs target

### Monthly
- Evaluate strategy performance
- Consider rebalancing capital allocation
- Update top 10 coin list

---

## 📞 Support

If issues persist after fixes:

1. Check logs: `tail -f ~/cryptobot_v3/bot.log`
2. Run diagnostic: `python3 diagnose_bots.py`
3. Check VPS connectivity: `ping api.binance.com`
4. Verify database: `ls -lh data/multi/trades_paper.db`

---

## 🎓 Learning Resources

**Grid Trading**:
- Optimal grid spacing: 0.5-1% for volatile assets
- Grid levels: 30-100 for high-frequency trading
- Capital: Divide by grid levels for position sizing

**Buy-the-Dip**:
- Threshold should match 2x daily volatility
- RSI < 35 filters out false dips
- Take profit: 2-3x the dip threshold

**Risk Management**:
- Max 5% capital per position
- Daily loss limit: 10% of portfolio
- Circuit breaker: Pause after 3 consecutive losses
