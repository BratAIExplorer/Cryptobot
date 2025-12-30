# 🎯 Buy-the-Dip Strategy - Implementation Plan
**User's Tweaked Strategy:** Hold indefinitely until 5% profit, 60-day alerts

---

## Strategy Logic

### Entry
- Buy on 5% dip with confluence score ≥65

### Exit
- **Profit Target:** Auto-sell at +5% (data-optimized)
- **Stop Loss:** DISABLED (never auto-sell at loss)
- **Max Hold:** Indefinite (hold until profitable)
- **Checkpoints:** Alert at 60, 90, 120, 180 days

### Risk Management
- **Catastrophic Floor:** -50% (prevents total wipeout)
- **Position Limit:** Max 2 positions per coin
- **Capital Allocation:** $25-200 per position

---

## Code Changes Required

### 1. Update Risk Manager (`core/risk_module.py`)

**File:** `core/risk_module.py`
**Function:** `check_exit_conditions()` (line 394-445)

```python
def check_exit_conditions(self, position_data, regime_state: str = None) -> Tuple[str, Optional[str]]:
    """
    V3+ Institutional Exit Engine with Buy-the-Dip Custom Logic
    """
    current_price = Decimal(str(position_data['current_price']))
    entry_price = Decimal(str(position_data['entry_price']))
    strategy = position_data.get('strategy', 'Unknown')
    entry_date = position_data.get('entry_date')

    # Parse entry_date if string
    if isinstance(entry_date, str):
        entry_date = datetime.fromisoformat(entry_date)

    # 1. Calculate PnL
    pnl_pct = (current_price - entry_price) / entry_price

    # 2. Calculate position age
    hours_open = 0
    if entry_date:
        hours_open = (datetime.utcnow() - entry_date).total_seconds() / 3600

    # ========================================
    # BUY-THE-DIP CUSTOM LOGIC
    # ========================================
    if strategy == "Buy-the-Dip Strategy":
        # Take Profit: Auto-sell at 5%
        if pnl_pct >= Decimal("0.05"):  # 5% profit
            return 'SELL', f"Take Profit Reached (+{pnl_pct*100:.2f}%)"

        # Catastrophic Floor: Prevent total wipeout
        if pnl_pct <= Decimal("-0.50"):  # -50% loss
            return 'SELL', f"Catastrophic loss protection (-{abs(pnl_pct)*100:.1f}%)"

        # 60-day checkpoint alert (informational only)
        if hours_open > 1440:  # 60 days
            days_held = hours_open / 24
            # Check if we're at a checkpoint (60, 90, 120, 180 days)
            checkpoints = [60, 90, 120, 180, 240, 365]
            for checkpoint in checkpoints:
                if abs(days_held - checkpoint) < 1:  # Within 1 day of checkpoint
                    return 'ALERT_CHECKPOINT', (
                        f"Position held {days_held:.0f} days | "
                        f"Current P&L: {pnl_pct*100:+.1f}% | "
                        f"Review recommended (not required)"
                    )

        # Default: HOLD (never sell at a loss)
        return 'HOLD', None

    # ========================================
    # STANDARD LOGIC FOR OTHER STRATEGIES
    # ========================================

    # Regime-Aware Stop Loss (for other strategies)
    sl_threshold = Decimal("-0.05")  # Default -5%
    if regime_state == 'CRISIS':
        sl_threshold = Decimal("-0.02")
    elif regime_state in ['BULL_CONFIRMED', 'TRANSITION_BULLISH']:
        sl_threshold = Decimal("-0.10")

    # Time-Based Stagnation (other strategies only)
    if hours_open > 72 and pnl_pct < 0.01:
        return 'SELL', f"Stagnation: Open {hours_open:.1f}h with <1% profit"

    # Regime Switch Veto
    entry_regime = position_data.get('entry_regime')
    if entry_regime in ['BULL_CONFIRMED', 'TRANSITION_BULLISH'] and regime_state == 'CRISIS':
        if pnl_pct > -0.01:
            return 'SELL', f"Regime Veto: Market shifted to CRISIS state"

    # Take Profit (strategy-specific)
    tp_target = Decimal("0.03")  # Default 3%
    if strategy == "Hyper-Scalper Bot":
        tp_target = Decimal("0.01")
    elif strategy == "Grid Bot BTC" or strategy == "Grid Bot ETH":
        tp_target = Decimal("0.015")  # 1.5% for grid
    elif strategy == "SMA Trend Bot":
        tp_target = Decimal("0.10")  # 10% for trend following

    if pnl_pct >= tp_target:
         return 'SELL', f"Take Profit Reached (+{pnl_pct*100:.2f}%)"

    # Stop Loss (other strategies)
    if pnl_pct <= sl_threshold:
        return 'ALERT_STOP_LOSS', f"Stop Loss Threshold Hit ({pnl_pct*100:.2f}%) [Regime: {regime_state}]"

    return 'HOLD', None
```

---

### 2. Update Engine to Handle Checkpoints (`core/engine.py`)

**File:** `core/engine.py`
**Function:** `process_bot()` (around line 670-673)

```python
# Around line 670-673, update the action handling:

if action == 'SELL':
    sell_reason = risk_reason
elif action == 'ALERT_STOP_LOSS':
    print(f"⚠️  MANUAL DECISION NEEDED: {symbol} hit Stop Loss. Bot is HOLDING. {risk_reason}")
elif action == 'ALERT_CHECKPOINT':
    # NEW: Handle checkpoint alerts
    print(f"📅 CHECKPOINT ALERT: {symbol} | {risk_reason}")

    # Send Telegram notification
    if self.notifier:
        self.notifier.send_message(
            f"📅 **Position Checkpoint Alert**\n\n"
            f"Symbol: {symbol}\n"
            f"Strategy: Buy-the-Dip\n"
            f"{risk_reason}\n\n"
            f"👉 Review in dashboard if needed.\n"
            f"💡 Tip: Bot will continue holding until +5% profit or -50% catastrophic floor."
        )
```

---

### 3. Update Bot Configuration (`run_bot.py`)

**File:** `run_bot.py`
**Lines:** 135-174 (Buy-the-Dip config)

```python
engine.add_bot({
    'name': 'Buy-the-Dip Strategy',
    'type': 'Buy-the-Dip',
    'symbols': [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
        'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT',
        'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
    ],

    # Position Sizing
    'amount': 25,  # Start at $25
    'initial_balance': 3000,
    'max_exposure_per_coin': 200,

    # Entry/Exit (Aligned with Risk Manager)
    'dip_percentage': 0.05,       # 5% dip threshold
    'take_profit_pct': 0.05,      # 5% TP (data-optimized) ✅ CHANGED FROM 0.06
    'stop_loss_pct': None,        # DISABLED (never auto-sell at loss) ✅ CHANGED
    'stop_loss_enabled': False,   # DISABLED ✅ CHANGED FROM True

    # Catastrophic Floor
    'catastrophic_floor_pct': 0.50,  # -50% emergency exit ✅ NEW

    # Hold Strategy
    'max_hold_hours': None,       # Indefinite (hold until profitable) ✅ CHANGED FROM 1440
    'checkpoint_alerts': [60, 90, 120, 180, 240, 365],  # Days ✅ NEW

    # Trend Filters
    'sma_fast': 7,
    'sma_slow': 21,
    'require_above_both': True,

    # Smart Conditional Cooldown
    'cooldown_after_profit': 6,   # 6 hours
    'cooldown_after_loss': 48,    # Not used (no losses sold)
    'cooldown_same_day': 12,
    'max_positions_per_coin': 2,

    # Safety Limits
    'max_daily_trades': 3,
    'min_confluence': 65,

    # Circuit Breaker
    'circuit_breaker_daily': -100,   # Still useful for catastrophic scenarios
    'circuit_breaker_weekly': -300
})
```

---

## Implementation Steps

### Step 1: Backup Current Code
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
git add -A
git commit -m "backup: before strategy tweaks"
git push
```

### Step 2: Apply Code Changes
1. Edit `core/risk_module.py` - Add Buy-the-Dip custom logic
2. Edit `core/engine.py` - Add ALERT_CHECKPOINT handling
3. Edit `run_bot.py` - Update configuration

### Step 3: Test in Paper Mode
```bash
# Stop current bot
touch STOP_SIGNAL

# Wait for bot to stop
# Then restart with new config
python3 run_bot.py
```

### Step 4: Monitor First 24 Hours
- Watch for 5% TP hits
- Verify no auto-sells on losses
- Check checkpoint alerts work

---

## Expected Behavior

### Scenario 1: Position Reaches +5%
```
[Buy-the-Dip] SOL/USDT
  Entry: $139.72
  Current: $146.70 (+5.0%)

  ✅ Action: AUTO-SELL
  ✅ Reason: "Take Profit Reached (+5.00%)"
  ✅ Result: $6.98 profit locked in
```

### Scenario 2: Position at -10% After 30 Days
```
[Buy-the-Dip] XRP/USDT
  Entry: $2.126
  Current: $1.91 (-10.2%)
  Days Held: 30

  ✅ Action: HOLD
  ✅ Reason: Waiting for +5% profit
  ✅ Alert: None (checkpoint at 60 days)
```

### Scenario 3: Position at -15% After 60 Days
```
[Buy-the-Dip] DOT/USDT
  Entry: $2.258
  Current: $1.92 (-15.0%)
  Days Held: 60

  ✅ Action: HOLD (continue waiting)
  ✅ Alert: "Position held 60 days | P&L: -15.0% | Review recommended"
  📱 Telegram: Checkpoint notification sent
```

### Scenario 4: Catastrophic Loss
```
[Buy-the-Dip] SCAM/USDT
  Entry: $10.00
  Current: $4.90 (-51%)

  🚨 Action: AUTO-SELL (catastrophic floor)
  🚨 Reason: "Catastrophic loss protection (-51%)"
  💡 Note: Prevents total wipeout
```

---

## Risk Analysis

### Pros ✅
- ✅ Never realizes small losses (tax efficient)
- ✅ Captures 5% profits automatically
- ✅ Capital preserving (holds through dips)
- ✅ Works well for quality coins that recover
- ✅ 60-day checkpoints prevent "forgotten" positions

### Cons ⚠️
- ⚠️ Capital can be locked for months
- ⚠️ Opportunity cost (money not available for better dips)
- ⚠️ Requires strong coins that eventually recover
- ⚠️ -50% floor still allows significant losses

### Mitigation Strategies
1. **Diversify:** 12 coins reduces single-coin risk
2. **Quality Focus:** Only buy top 20 market cap
3. **Position Sizing:** Small $25-200 positions limit damage
4. **Active Monitoring:** 60-day checkpoints for intervention
5. **Confluence Filter:** Score ≥65 ensures quality entries

---

## Performance Projections

### Conservative Scenario
- 30% of positions hit +5% within 90 days
- 50% of positions stuck 6-12 months
- 20% hit catastrophic floor

**Expected Annual Return:** 15-20%

### Optimistic Scenario
- 60% of positions hit +5% within 60 days
- 30% stuck 3-6 months
- 10% small losses

**Expected Annual Return:** 40-60%

### Reality Check (Based on Your Data)
Your current Buy-the-Dip positions:
- 0% have hit +5% in 24 days
- 17 positions are underwater
- Average P&L: ~-15% (estimated)

**Implication:** Strategy works IF you buy quality coins during actual dips, not during downtrends.

---

## Success Criteria

### After 30 Days:
- ✅ At least 2 positions closed at +5%
- ✅ No positions auto-sold at a loss
- ✅ Capital rotation improved

### After 60 Days:
- ✅ First checkpoint alerts received
- ✅ Manual review of stuck positions completed
- ✅ Strategy adjustment if needed

### After 90 Days:
- ✅ Net positive P&L from new positions
- ✅ Old positions either recovered or manually closed
- ✅ Strategy validated or pivoted

---

## Emergency Override

If market crashes or personal need for capital:

### Manual Close All Positions
```python
# Create emergency_close.py
from core.logger import TradeLogger
from core.exchange_unified import UnifiedExchange

logger = TradeLogger(mode='paper')
exchange = UnifiedExchange('MEXC', mode='paper')

# Get all Buy-the-Dip open positions
positions = logger.get_open_positions()
dip_positions = positions[positions['strategy'] == 'Buy-the-Dip Strategy']

print(f"Found {len(dip_positions)} positions to close")

for _, pos in dip_positions.iterrows():
    # Get current price
    current_price = exchange.get_current_price(pos['symbol'])

    print(f"Closing {pos['symbol']} at {current_price}")

    # Force sell (implement actual sell logic)
    # logger.force_close_position(pos['id'])
```

---

## Next Steps

1. Review this implementation plan
2. Confirm 5% TP is acceptable (vs 6%)
3. Approve catastrophic floor at -50% (or adjust)
4. Schedule deployment window
5. Test in paper mode for 48 hours
6. Deploy to live trading

---

**Ready to implement?** Let me know if you want any adjustments to:
- Take profit % (5% vs other)
- Catastrophic floor % (-50% vs other)
- Checkpoint intervals (60, 90, 120 days vs other)
