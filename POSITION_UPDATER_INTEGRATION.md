# Position Updater Fix - Manual Integration Guide

## Problem
Position `current_price` is never updated after creation, causing:
- All P&L calculations show 0%
- Take-profit logic never triggers
- Bot appears to be "holding" but is actually blind to price movements

## Solution Implemented

### 1. Added to `core/logger.py` (✅ DONE)
New method `update_open_position_prices(exchange_interface)` at line ~212

### 2. Integration Needed in `core/engine.py` (⚠️ MANUAL STEP)

**Location**: Find where the bot evaluates strategies (search for "evalu" or where strategies run)

**Add this code BEFORE strategy evaluation:**

```python
# Update position prices before evaluating (Position Updater Fix - Jan 21, 2026)
try:
    updated = self.logger.update_open_position_prices(self.exchange_manager.adapters['BINANCE'])
    if updated > 0:
        print(f"[POSITION UPDATE] Refreshed prices for {updated} open positions")
except Exception as e:
    print(f"[POSITION UPDATE] Non-critical error: {e}")
    # Continue execution - don't crash bot
```

**Alternative Location**: In `run_bot.py` around line 355, add BEFORE `engine.run_cycle()`:

```python
# Update positions before each cycle
try:
    # Access the correct adapter based on your setup
    binance_adapter = engine.exchange_manager.adapters.get('BINANCE')
    if binance_adapter:
        updated = engine.logger.update_open_position_prices(binance_adapter)
except:
    pass  # Silent fail - don't crash bot
```

## Testing

Run local test:
```bash
python test_position_updater.py
```

Expected: Position price should update from entry price to current market price.

## Deployment Checklist

- [x] Added `update_open_position_prices` to `core/logger.py`
- [ ] Integrated updater call in engine/run loop
- [ ] Tested locally
- [ ] Committed to git
- [ ] Deployed to VPS
- [ ] Monitored for 30 minutes post-deployment
