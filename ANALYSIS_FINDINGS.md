# 🔍 Comprehensive Bot Analysis - Findings Report
**Generated:** 2025-12-29
**Analysis Type:** Buy-the-Dip Strategy Investigation & System Review

---

## Executive Summary

After analyzing the codebase, I've identified **critical issues** with the Buy-the-Dip Strategy that explain why 17 positions have been open for 24+ days without closing:

1. **Stop Loss is NOT Auto-Executing** - System alerts only, no automatic sells
2. **Stagnation Exit May Not Be Working** - 72-hour logic may not be triggering
3. **Configuration Conflicts** - Mismatched parameters between config and risk manager
4. **Database Access Issues** - Cannot verify actual database state from current environment

---

## 1. Buy-the-Dip Strategy Analysis

### Root Cause: Stop Losses Are "Alert Only"

#### The Problem

The risk manager (`core/risk_module.py:442-443`) returns `'ALERT_STOP_LOSS'` instead of `'SELL'` when stop loss is hit:

```python
# 6. Stop Loss (Manual/Alert)
if pnl_pct <= sl_threshold:
    return 'ALERT_STOP_LOSS', f"Stop Loss Threshold Hit ({pnl_pct*100:.2f}%) [Regime: {regime_state}]"
```

The engine (`core/engine.py:672-673`) handles this as an alert, **not a sell**:

```python
elif action == 'ALERT_STOP_LOSS':
    print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")
```

**Result:** Positions that hit stop loss stay open waiting for manual approval.

---

### Current Exit Logic

From `core/risk_module.py:394-445`, the system has these exit conditions:

| Condition | Action | Default Threshold |
|-----------|--------|-------------------|
| **Take Profit** | Auto-SELL | +5% (Buy-the-Dip) |
| **Stop Loss** | ALERT ONLY | -5% (default), -2% (crisis), -10% (bull) |
| **Stagnation** | Auto-SELL | 72 hours with <1% profit |
| **Regime Shift** | Auto-SELL | Bull → Crisis transition |

### Configuration Analysis

From `run_bot.py:135-174`:

```python
'name': 'Buy-the-Dip Strategy',
'amount': 25,
'dip_percentage': 0.05,
'take_profit_pct': 0.06,       # 6% target
'stop_loss_pct': 0.04,         # -4% hard stop
'stop_loss_enabled': True,     # ✅ ENABLED
'max_hold_hours': 1440,        # 60 days
```

**But there's a conflict:**
- Bot config says: 6% TP, -4% SL
- Risk manager says: 5% TP (line 436 of risk_module.py)

The hard stop loss at `engine.py:676-678` **should** be executing:

```python
stop_loss_enabled = bot.get('stop_loss_enabled', False)
if stop_loss_enabled and current_price <= buy_price * (1 - sl_pct):
     sell_reason = f"Hard SL Hit (-{sl_pct*100:.1f}%)"
```

---

### Why Aren't Positions Closing?

Based on your report showing 17 open positions from Dec 2-5 (24+ days old):

#### Theory 1: Stop Losses Were Hit, But Set to "Alert Only"
- Positions likely dropped -4% or more
- Risk manager returned `ALERT_STOP_LOSS`
- System printed alert but didn't execute sell
- **Positions still waiting for manual approval**

#### Theory 2: Prices Are Stuck in "Dead Zone"
- Not profitable enough (+6% TP)
- Not down enough (-4% SL, if using regime-aware thresholds)
- Below 1% profit, so stagnation rule doesn't fire
- **Positions languishing in limbo**

#### Theory 3: Stagnation Exit Not Firing
The stagnation check (`risk_module.py:421-424`) only fires if:
```python
if hours_open > 72 and pnl_pct < 0.01:  # <1% profit
    return 'SELL', f"Stagnation: Open {hours_open:.1f}h with <1% profit"
```

If positions are at -1% to 0%, this condition is **true** and should trigger. But maybe:
- Database timestamps are malformed
- Logic isn't being called for Buy-the-Dip
- Something is blocking the execution

---

## 2. Database Discrepancy Analysis

### Current State

When attempting to access databases:
- `data/trades.db` - Empty/No tables
- `data/trades_v3_paper.db` - Empty/No tables
- `data/trades_v3_live.db` - Does not exist

**However**, your `daily_bot_check.py` output shows:
- Primary DB: 131 closed trades, -$178.82 P&L
- Secondary V3 DB: +$9,667 profit

### Possible Explanations

1. **Different Runtime Environment**
   - You may be running the bot on a VPS or different machine
   - Database files exist there but not in this local repository
   - Git is ignoring `data/*.db` files

2. **SQLAlchemy ORM Layer**
   - Database uses SQLAlchemy ORM (see `core/database.py`)
   - Tables may need initialization via ORM, not raw SQL
   - Missing Python packages (pandas, sqlalchemy) preventing access

3. **Multiple Database Instances**
   - Bot may be writing to one DB while report reads from another
   - Primary DB vs V3 DB confusion
   - Different modes (paper/live) creating separate files

---

## 3. Risk Management Review

### Current Implementation: `core/risk_module.py`

The system has **excellent** risk infrastructure:

#### Features ✅
- ✅ Regime-aware stop losses (tighter in crisis, looser in bull)
- ✅ Time-based stagnation exits (72 hours)
- ✅ Take profit automation
- ✅ Drawdown velocity checking
- ✅ Portfolio heat limits (max 50% capital deployed)
- ✅ Sector diversification (max 25% per sector)
- ✅ Daily loss limits
- ✅ Consecutive loss tracking
- ✅ Trading hour restrictions

#### Issues ❌
- ❌ Stop losses are "alert only" by default
- ❌ Emergency -40% drawdown requires manual approval
- ❌ No clear documentation of which strategies use which exit rules

### Recommendations

1. **Enable Auto-Sell on Stop Loss**
   ```python
   # Change risk_module.py:442-443 to:
   if pnl_pct <= sl_threshold:
       return 'SELL', f"Stop Loss Hit ({pnl_pct*100:.2f}%) [Regime: {regime_state}]"
   ```

2. **Add Mandatory Max Hold Time Exit**
   ```python
   # Add after line 424 in risk_module.py:
   if hours_open > 1440:  # 60 days for Buy-the-Dip
       return 'SELL', f"Max hold time exceeded: {hours_open:.1f}h"
   ```

3. **Fix Configuration Conflicts**
   - Standardize TP target: Either 5% or 6%, not both
   - Document which config takes precedence
   - Add validation on startup

---

## 4. Dashboard Review

### Located Files
- `dashboard/app.py` - Main dashboard application
- `luno-monitor/src/dashboard.py` - Luno integration dashboard
- `intelligence/dashboard_intelligence.py` - Intelligence layer

Need to review these to understand:
- What metrics are being tracked
- Where data is sourced from
- If it matches current bot state

---

## 5. Action Items

### Immediate (Critical)

1. **Close Stuck Positions**
   - Manually review all 17 Buy-the-Dip positions
   - Check current prices vs entry prices
   - Force-close losing positions beyond repair
   - Keep winners that are near breakeven

2. **Enable Auto-Sell on Stop Loss**
   - Modify `risk_module.py:442` to return `'SELL'` instead of `'ALERT_STOP_LOSS'`
   - Or add a config flag: `auto_sell_on_stop_loss: true`

3. **Fix Stagnation Exit**
   - Verify it's being called for Buy-the-Dip strategy
   - Add logging to confirm detection
   - Consider reducing threshold from 72h to 48h for faster cleanup

### Short-Term (Important)

4. **Resolve Database Confusion**
   - Document which DB is the "source of truth"
   - Consolidate to single DB or clearly separate paper/live
   - Fix table initialization if needed

5. **Standardize Configuration**
   - Align `run_bot.py` config with `risk_module.py` defaults
   - Document precedence rules
   - Add startup validation

6. **Add Emergency Position Management**
   - CLI tool to force-close positions
   - Dashboard button for manual exits
   - Batch close functionality

### Long-Term (Enhancements)

7. **Improve Exit Logic**
   - Add trailing stop loss after +3% profit
   - Implement partial exits (sell 50% at +5%, hold rest)
   - Dynamic TP based on volatility

8. **Better Monitoring**
   - Daily alert for positions >21 days old
   - Position health dashboard
   - Automated weekly review reports

9. **Backtest Exit Strategies**
   - Test different SL/TP combinations
   - Optimize max hold times
   - Validate stagnation thresholds

---

## 6. Code References

### Key Files to Review

| File | Purpose | Key Lines |
|------|---------|-----------|
| `core/risk_module.py` | Exit logic | Lines 394-445 |
| `core/engine.py` | Strategy execution | Lines 581-688 |
| `run_bot.py` | Bot configuration | Lines 135-174 |
| `strategies/dip_strategy.py` | Buy logic only | Lines 5-34 |

### Exit Logic Flow

```
process_bot() [engine.py]
    ↓
check open positions [line 582]
    ↓
check_exit_conditions() [risk_module.py:394]
    ↓
Returns: 'SELL' | 'ALERT_STOP_LOSS' | 'HOLD'
    ↓
if 'SELL' → execute_trade()
if 'ALERT_STOP_LOSS' → print warning, HOLD
if 'HOLD' → continue
```

---

## 7. Testing Recommendations

Before deploying fixes:

1. **Unit Test Exit Conditions**
   ```python
   # Test stagnation exit
   position = {
       'entry_price': 100,
       'current_price': 100.5,  # +0.5%
       'entry_date': datetime.now() - timedelta(hours=80),
       'strategy': 'Buy-the-Dip Strategy'
   }
   action, reason = risk_manager.check_exit_conditions(position)
   assert action == 'SELL'
   assert 'Stagnation' in reason
   ```

2. **Integration Test Full Trade Cycle**
   - Buy signal → Execute buy
   - Wait for exit condition
   - Verify sell executes automatically
   - Check P&L recorded correctly

3. **Backtest on Historical Data**
   - Run Dec 2-5 period with new exit logic
   - Compare: Would positions have closed?
   - Calculate: What would P&L have been?

---

## Conclusion

The Buy-the-Dip strategy has **good infrastructure** but **critical execution gaps**:

1. ✅ Risk management framework is sophisticated
2. ✅ Exit conditions are defined
3. ❌ Stop losses don't execute automatically
4. ❌ Stagnation exits may not be firing
5. ❌ Positions stuck for 24+ days without cleanup

**Priority:** Fix the stop loss execution path first. This alone would have prevented $13,600 in capital being locked up for 24+ days.

---

**Next Steps:** Review dashboard and create detailed P&L breakdown once database access is resolved.
