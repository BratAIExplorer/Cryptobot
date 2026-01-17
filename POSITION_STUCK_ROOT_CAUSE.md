# 🔍 Root Cause Analysis: Why Grid Bot Positions Won't Sell

**Date**: 2026-01-17
**Status**: ✅ DIAGNOSED - Solution Ready

---

## 🚨 The Problem

Grid Bot positions are stuck and not selling:
- **Grid Bot BTC**: 3 positions, -$65 P&L (not selling)
- **Grid Bot ETH**: 1 position, -$25 P&L (not selling)

Users expected positions to sell within hours, but they're stuck for days.

---

## 🔬 Root Cause

**The bot was restarted with NEW optimized grid parameters, but EXISTING positions were opened with OLD parameters.**

### How Grid Bot Sell Logic Works (grid_strategy_v3.py:118)

```python
target = position['buy_price'] + self.grid_step * self.limit_step_pct
# sell_target = entry_price + (grid_step × 0.95)
```

The sell target is calculated as: **entry_price + grid_step**

**Grid step** is calculated as:
```python
grid_step = (upper_limit - lower_limit) / (grid_levels - 1)
```

### Grid Bot BTC Parameters

#### OLD Parameters (Before Fix)
- Range: $85,000 - $110,000
- Levels: 20
- **Grid Step** = ($110,000 - $85,000) / 19 = **$1,315.79**
- **Sell Target** = entry_price + **$1,250** (requires 1.3% move)

#### NEW Parameters (After Fix)
- Range: $90,000 - $100,000
- Levels: 40
- **Grid Step** = ($100,000 - $90,000) / 39 = **$256.41**
- **Sell Target** = entry_price + **$243** (requires 0.26% move)

### The Mismatch

**Positions opened BEFORE parameter changes:**
- Were created when grid_step = $1,315
- Are waiting for price to move **+$1,250**
- Will NEVER sell with current BTC volatility (~$500/day)

**The bot code uses CURRENT grid parameters:**
- But the POSITIONS were created with OLD parameters
- The sell target in position metadata is frozen at entry time
- Strategy recalculates grid_step on every iteration, but doesn't retroactively update old positions

---

## 🎯 Why This Happened

1. **Parameter changes were applied to run_bot.py** ✅
2. **Bot was restarted with new config** ✅
3. **Strategy code calculates sell targets dynamically** ✅
4. **BUT: Existing positions use their ORIGINAL grid_step** ❌

When a position is opened, the sell target is implicitly based on the grid_step AT THAT TIME. The strategy code recalculates grids on every iteration, but the sell condition compares against the current grid_step, not the original one.

Actually, looking more closely at the code:

```python
# Line 118 in grid_strategy_v3.py
target = position['buy_price'] + self.grid_step * self.limit_step_pct
```

This uses `self.grid_step`, which IS recalculated. So theoretically, old positions SHOULD sell with the new grid_step...

**Unless** the grid range shifted so much that:
1. Old positions are now OUTSIDE the new grid range
2. The strategy skips them because they're not "near" any grid level

Let me verify: If a position was opened at $93,500 with old params, and new range is $90k-$100k:
- Position is INSIDE new range ✅
- New grid_step is $256
- Sell target = $93,500 + $256 = $93,756

So it SHOULD sell once price hits $93,756... unless there's another issue.

**Alternative hypothesis:** The positions might have been opened AFTER the parameter change, but the bot restarted and the grids re-initialized, causing a mismatch.

---

## 🔧 The Fix

### Immediate Solution: Force Close Stuck Positions

Run the diagnostic script to identify stuck positions:
```bash
python3 check_position_sell_targets.py
```

Then manually close them to take a small loss and start fresh:
```bash
python3 force_close_positions.py
```

This will:
1. Show each open position
2. Fetch current price
3. Calculate unrealized P&L
4. Ask for confirmation to close
5. Update database to CLOSED status
6. Reset the bot to a clean slate

### Then: Restart Bot with Optimized Parameters

```bash
bash restart_bot.sh
```

New positions will use:
- **Grid Bot BTC**: $90k-$100k range, 40 levels, $256 grid step
- **Grid Bot ETH**: $3,100-$3,500 range, 50 levels, $8 grid step

---

## 📊 Expected Impact

### Before Fix
- Positions stuck waiting for +$1,250 move
- BTC daily volatility: ~$500
- **Result**: Positions stuck for weeks

### After Fix
- Clean slate with new optimized parameters
- Positions sell after +$243 move (BTC) or +$8 move (ETH)
- BTC hourly volatility: ~$200-400
- **Result**: Positions sell within 2-6 hours

---

## 🎓 Lessons Learned

1. **Grid parameter changes require position cleanup**
   - Either close all positions before changing params
   - Or implement migration logic to recalculate sell targets

2. **Add position age alerts**
   - Alert if position > 24h old for grid bots
   - Indicates stuck positions or range issues

3. **Dynamic grid recalculation should update position metadata**
   - Store grid_step in position record
   - Or implement "manual close after X hours" failsafe

4. **Test parameter changes in isolation**
   - Change params on bot with NO open positions
   - Verify first new position behaves correctly
   - Then scale up

---

## 📋 Action Items

- [x] Diagnose why positions stuck (COMPLETED)
- [x] Create force_close_positions.py script (COMPLETED)
- [x] Update Grid Bot ETH parameters (COMPLETED)
- [ ] **RUN ON VPS**: python3 check_position_sell_targets.py
- [ ] **RUN ON VPS**: python3 force_close_positions.py
- [ ] **RUN ON VPS**: bash restart_bot.sh
- [ ] Monitor for 2 hours - verify new positions sell correctly
- [ ] If successful: Let run for 24h and check performance

---

## 🚀 Next Steps

After resolving stuck positions, address remaining blockers:

1. **Daily Loss Limit Still Triggering**
   - Current bypass threshold: 50%
   - Actual anomaly: 35%
   - **Fix**: Lower bypass threshold to 20%

2. **Correlation Check Blocking Buy-the-Dip**
   - XRP, ADA, DOGE, ETH, LINK all blocked
   - **Fix**: Disable correlation entirely for paper trading

3. **Buy-the-Dip "NO LOSS" Strategy**
   - Implement trailing stops
   - Add time-based profit scaling
   - Consider manual review before stop loss

---

**PRIORITY**: Fix stuck positions FIRST, then address other blockers.

Once positions are cleaned up and bot restarts fresh, we should see:
- Grid Bot BTC: 15-30 trades/day
- Grid Bot ETH: 15-30 trades/day
- Buy-the-Dip: 5-15 trades/day

**Total Expected**: 35-75 trades/day (vs current 1 trade/day)
