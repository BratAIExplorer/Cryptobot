# Safety Systems - 100% Customizable, Scalable & Robust

## Overview

All safety systems are **100% customizable** via YAML configuration - **NO code changes required**.

This addresses your requirements for:
- ✅ **100% Customizable** - All limits in YAML config
- ✅ **Scalable** - Supports unlimited bot instances
- ✅ **Robust** - Fail-safe design with fallbacks

---

## How It Works

### Before (Hardcoded - Bad ❌)
```python
# OLD WAY - limits hardcoded in code
kill_switch = EmergencyKillSwitch(
    max_daily_loss_usd=50.0,  # Hardcoded!
    max_weekly_loss_usd=150.0  # Hardcoded!
)
```

### After (Configuration-Driven - Good ✅)
```python
# NEW WAY - 100% from config file
from core.safety import get_safety_config

config = get_safety_config('config/safety_limits.yaml')
configs = config.get_all_configs(
    exchange='BINANCE',
    mode='live',
    strategy='GridBot',  # Optional
    scaling_preset='micro'  # Optional
)

# All parameters loaded from YAML automatically
kill_switch = EmergencyKillSwitch(**configs['kill_switch'])
```

**To change limits:** Just edit `config/safety_limits.yaml` - NO code changes!

---

## Configuration Structure

```yaml
# config/safety_limits.yaml

# 1. Global defaults (fallback)
defaults:
  kill_switch:
    max_daily_loss_usd: 50.0
    max_weekly_loss_usd: 150.0

# 2. Exchange-specific
exchanges:
  BINANCE:
    # 3. Mode-specific
    live:
      kill_switch:
        max_daily_loss_usd: 50.0  # Strict for real money

    paper:
      kill_switch:
        max_daily_loss_usd: 100.0  # More tolerant for testing

# 4. Strategy-specific overrides
strategies:
  GridBot:
    capital_limits:
      max_position_size_usd: 200.0  # Custom for GridBot
      max_open_positions: 6

# 5. Scaling presets
scaling_presets:
  micro:  # $100 capital
    kill_switch:
      max_daily_loss_usd: 10.0
    capital_limits:
      max_position_size_usd: 25.0

  large:  # $10,000 capital
    kill_switch:
      max_daily_loss_usd: 500.0
    capital_limits:
      max_position_size_usd: 2500.0
```

---

## Hierarchical Override System

Configuration is applied in priority order (highest wins):

```
1. Emergency overrides (highest priority)
2. Scaling presets (micro/small/medium/large)
3. Strategy overrides (GridBot/MomentumBot)
4. Exchange + Mode (BINANCE/live)
5. Exchange defaults (BINANCE)
6. Global defaults (lowest priority)
```

**Example:** Binance live GridBot with micro preset:
- Starts with global defaults
- Applies BINANCE defaults
- Applies BINANCE/live overrides
- Applies GridBot strategy overrides
- Applies micro preset (highest priority)

---

## Paper vs Live Separation

### Separate Kill Switches - YES! ✅

Each bot instance has its own kill switch state file:

```
data/
├── binance/
│   ├── live/
│   │   └── kill_switch_state.json    # Live bot kill switch
│   └── paper/
│       └── kill_switch_state.json    # Paper bot kill switch (separate!)
├── luno/
│   └── monitor/
│       └── kill_switch_state.json    # Monitor bot kill switch
```

**Benefits:**
- ✅ Paper losses don't halt live trading
- ✅ Live halt doesn't stop paper testing
- ✅ Different loss tolerances
- ✅ Independent recovery

---

## Scalability Examples

### Scenario 1: Start with $100 (Micro)

**Edit config/safety_limits.yaml:**
```yaml
# Use in bot initialization:
# scaling_preset='micro'
```

**Result:**
- Max daily loss: $10
- Max position size: $25
- Max open positions: 3
- Max total exposure: $75

### Scenario 2: Scale to $2,000 (Medium)

**Edit config/safety_limits.yaml:**
```yaml
# Use in bot initialization:
# scaling_preset='medium'
```

**Result:**
- Max daily loss: $100
- Max position size: $500
- Max open positions: 6
- Max total exposure: $2,000

**NO CODE CHANGES REQUIRED!**

### Scenario 3: Scale to $10,000 (Large)

**Edit config/safety_limits.yaml:**
```yaml
# Use in bot initialization:
# scaling_preset='large'
```

**Result:**
- Max daily loss: $500
- Max position size: $2,500
- Max open positions: 8
- Max total exposure: $10,000

**STILL NO CODE CHANGES!**

---

## Robustness Features

### 1. Fail-Safe Fallbacks

If YAML config is missing or corrupted:
```python
# Automatically falls back to safe defaults
defaults = {
    'kill_switch': {
        'max_daily_loss_usd': 50.0,  # Conservative
        'max_weekly_loss_usd': 150.0
    }
}
```

### 2. Configuration Validation

```python
loader = SafetyConfigLoader('config/safety_limits.yaml')
is_valid = loader.validate_config()  # Checks for errors

if not is_valid:
    # Automatically uses safe defaults
    logger.error("Config invalid, using defaults")
```

### 3. Runtime Reconfiguration

```python
# Update YAML file, then:
loader.reload_config()  # Picks up new limits without restart
```

### 4. Emergency Global Halt

```yaml
emergency:
  global_halt: true  # Immediately halts ALL bots
```

---

## Real-World Usage

### Example 1: Multiple Binance Bots

```python
# Live GridBot on Binance ($500 capital)
bot1 = ConfigurableTradingBot(
    exchange='BINANCE',
    mode='live',
    strategy='GridBot',
    scaling_preset='small'
)

# Live MomentumBot on Binance ($500 capital)
bot2 = ConfigurableTradingBot(
    exchange='BINANCE',
    mode='live',
    strategy='MomentumBot',
    scaling_preset='small'
)

# Paper TestBot on Binance (testing new strategy)
bot3 = ConfigurableTradingBot(
    exchange='BINANCE',
    mode='paper'
)
```

**Each bot has:**
- ✅ Separate kill switch state
- ✅ Strategy-specific limits
- ✅ Customized from config
- ✅ Independent operation

### Example 2: LUNO Monitor (No Trading)

```python
# Monitor only - no trading allowed
luno_monitor = ConfigurableTradingBot(
    exchange='LUNO',
    mode='monitor'
)

# Automatically configured with:
# - max_position_size: $0
# - max_open_positions: 0
# - All trading disabled
```

---

## How to Customize

### Step 1: Identify Your Needs

- Starting capital: $100 / $500 / $2,000 / $10,000?
- Risk tolerance: Conservative / Moderate / Aggressive?
- Exchange: BINANCE / LUNO / MEXC?
- Mode: paper / live / monitor?
- Strategy: GridBot / MomentumBot / Custom?

### Step 2: Edit YAML Config

```bash
nano config/safety_limits.yaml
```

### Step 3: Choose Configuration Level

**Option A: Use Scaling Preset (Easiest)**
```python
bot = ConfigurableTradingBot(
    exchange='BINANCE',
    mode='live',
    scaling_preset='micro'  # or small/medium/large
)
```

**Option B: Custom Exchange/Mode Config**
```yaml
# Edit config/safety_limits.yaml
exchanges:
  BINANCE:
    live:
      kill_switch:
        max_daily_loss_usd: 75.0  # Custom value
```

**Option C: Strategy-Specific Override**
```yaml
strategies:
  MyCustomBot:
    capital_limits:
      max_position_size_usd: 300.0
      max_open_positions: 5
```

### Step 4: Deploy

```python
# NO code changes needed!
bot = ConfigurableTradingBot(
    exchange='BINANCE',
    mode='live',
    strategy='MyCustomBot'
)
```

---

## Testing Your Configuration

### Validate Configuration
```bash
python core/safety/config_loader.py
```

**Output:**
```
Configuration valid: True
✅ All tests complete
```

### Test Integration
```bash
python examples/safety_integration_example.py
```

**Output:**
```
Example 1: Binance LIVE - MICRO preset ($100 capital)
  Kill switch: Daily $10.0, Weekly $30.0
  Capital limits: Max position $25.0, Max 3 positions

Kill switch active: True
Reason: Daily loss limit exceeded: $11.00 >= $10.00
✅ Safety systems working correctly
```

---

## Configuration Templates

### Conservative (Low Risk)
```yaml
custom_preset:
  kill_switch:
    max_daily_loss_usd: 25.0   # Very tight
    max_weekly_loss_usd: 75.0
  capital_limits:
    max_position_size_usd: 100.0
    max_open_positions: 2
    max_total_exposure_usd: 200.0
  slippage_protection:
    max_slippage_percent: 0.1  # Very tight (0.1%)
```

### Moderate (Balanced)
```yaml
custom_preset:
  kill_switch:
    max_daily_loss_usd: 50.0
    max_weekly_loss_usd: 150.0
  capital_limits:
    max_position_size_usd: 250.0
    max_open_positions: 4
    max_total_exposure_usd: 1000.0
  slippage_protection:
    max_slippage_percent: 0.2  # Default
```

### Aggressive (Higher Risk)
```yaml
custom_preset:
  kill_switch:
    max_daily_loss_usd: 100.0  # More tolerant
    max_weekly_loss_usd: 300.0
  capital_limits:
    max_position_size_usd: 500.0
    max_open_positions: 8
    max_total_exposure_usd: 3000.0
  slippage_protection:
    max_slippage_percent: 0.5  # More tolerant (0.5%)
```

---

## Benefits Summary

### 100% Customizable ✅
- All limits in YAML config
- NO hardcoded values in code
- Change without redeployment
- Runtime reconfigurable

### Scalable ✅
- Supports unlimited bot instances
- Each bot has independent limits
- Grows from $100 to $100,000+ without code changes
- Add new exchanges via config

### Robust ✅
- Fail-safe design (defaults to HALT if uncertain)
- Automatic fallbacks if config missing
- Configuration validation
- Separate kill switches prevent cascading failures
- Emergency global halt capability

---

## Next Steps

1. **Review config/safety_limits.yaml**
   - Understand the structure
   - Identify which preset matches your capital

2. **Test with Paper Mode**
   - Run with paper mode first
   - Validate limits work as expected
   - Adjust config as needed

3. **Start with Micro Preset**
   - Use `scaling_preset='micro'` for $100 test
   - Validate kill switch triggers correctly
   - Confirm capital limits enforced

4. **Scale Up Gradually**
   - Move to 'small' preset ($500)
   - Then 'medium' preset ($2,000)
   - Finally 'large' preset ($10,000+)

5. **Customize for Your Needs**
   - Create custom strategy configs
   - Tune limits based on performance
   - Add exchange-specific tweaks

---

## Support

**Configuration Questions:**
- Review: `config/safety_limits.yaml` (comprehensive examples)
- Test: `python core/safety/config_loader.py`
- Examples: `python examples/safety_integration_example.py`

**Integration Questions:**
- Review: `examples/safety_integration_example.py`
- Reference: `AI_HANDOVER_PHASE1_SAFETY.md`

**Emergency:**
```yaml
# Edit config/safety_limits.yaml
emergency:
  global_halt: true  # Stops ALL bots immediately
```

---

**END OF CUSTOMIZATION GUIDE**

*Everything is 100% customizable. Change `config/safety_limits.yaml` to adjust any limit without touching code.*
