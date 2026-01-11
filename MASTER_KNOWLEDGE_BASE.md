# 🤖 Cryptobot - Master Knowledge Base & Living Documentation

**Version**: 2026-01-11
**Last Updated**: 2026-01-11 09:00 UTC
**Session**: claude/priority1-enhancements-lXrIG
**Status**: 🟢 ACTIVE DEVELOPMENT - Grid Bot Test Running

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Environment & Paths](#environment--paths)
3. [Architecture](#architecture)
4. [Critical Issues & Resolutions](#critical-issues--resolutions)
5. [File Inventory](#file-inventory)
6. [Configuration Guide](#configuration-guide)
7. [Testing Procedures](#testing-procedures)
8. [Deployment Guide](#deployment-guide)
9. [Current Status](#current-status)
10. [Next Steps](#next-steps)

---

## Project Overview

### What is This Project?

**Cryptobot** is a cryptocurrency trading bot system with multiple strategies:
- **Grid Bot**: Mean reversion strategy with fixed price levels
- **Buy-the-Dip**: Opportunistic dip buying with long hold periods
- **SMA Trend**: Trend-following based on moving averages

### Key Features
- Multi-exchange support via adapter pattern (Binance, MEXC, Luno)
- Paper trading mode for zero-risk testing
- Risk management with daily loss limits
- Grid trading with static and dynamic ranges
- Real-time Telegram notifications
- SQLite database for trade tracking
- Resilience management for API failures

### Technology Stack
- **Language**: Python 3.x
- **Database**: SQLite
- **Exchanges**: CCXT library
- **Deployment**: VPS (Ubuntu/Debian Linux)
- **Version Control**: Git + GitHub
- **Architecture**: Adapter pattern with factory design

---

## Environment & Paths

### Development Environment (Local)

**Base Path**: `/home/user/Cryptobot`

**Key Directories**:
```
/home/user/Cryptobot/
├── core/                      # Core engine and modules
│   ├── engine.py             # Main trading engine
│   ├── logger.py             # Database and trade logging
│   ├── risk_module.py        # Risk management
│   ├── exchanges/            # Exchange adapter implementations
│   │   ├── base_adapter.py
│   │   ├── binance_adapter.py
│   │   ├── mexc_adapter.py
│   │   └── exchange_factory.py
│   ├── resilience.py         # Exchange health monitoring
│   └── notifier.py           # Telegram integration
├── strategies/               # Trading strategies
│   ├── grid_strategy_v2.py  # Dynamic Grid Bot
│   └── base_strategy.py     # Base strategy class
├── utils/                    # Utility functions
│   └── indicators.py        # Technical indicators (RSI, SMA, ATR)
├── data/                     # Databases and cache files
│   ├── *.db                 # SQLite databases
│   └── known_symbols_*.json # Exchange symbol cache
├── docs/                     # Documentation
├── tests/                    # Test files
└── *.py                      # Test scripts and utilities
```

### Production Environment (VPS)

**Base Path**: `/root/cryptobot_v3`

**Important Notes**:
- VPS runs Ubuntu/Debian Linux
- Python 3.x installed
- Git repository cloned from GitHub
- Environment variables set for API keys
- Cron jobs may be configured (check with `crontab -l`)

**Active Branch on VPS**: `claude/priority1-enhancements-lXrIG`

**VPS Structure** (mirrors local):
```
/root/cryptobot_v3/
├── core/                     # Same as local
├── strategies/               # Same as local
├── data/                     # Production databases
│   ├── test_adapter_binance_paper.db  # Current test DB
│   └── *.db                 # Other databases
├── test_adapter_paper.py    # Active test script
├── test_proven_config.log   # Current test logs
└── bot.log                   # General bot logs
```

### Path Mapping

| Component | Local Path | VPS Path | Notes |
|-----------|-----------|----------|-------|
| Repository Root | `/home/user/Cryptobot` | `/root/cryptobot_v3` | Different base directories |
| Test Database | `data/test_adapter_binance_paper.db` | `data/test_adapter_binance_paper.db` | Relative path, same |
| Test Script | `test_adapter_paper.py` | `test_adapter_paper.py` | Same filename |
| Test Logs | Not applicable | `test_proven_config.log` | VPS only |
| Bot Logs | `bot.log` | `bot.log` | Same filename |

---

## Architecture

### Current Architecture: Adapter Pattern

**Design Goal**: Support multiple exchanges with clean separation of concerns

#### Core Components

1. **BaseExchangeAdapter** (`core/exchanges/base_adapter.py`)
   - Abstract base class defining exchange interface
   - Methods: `fetch_ohlcv()`, `create_order()`, `fetch_balance()`, etc.
   - All exchange-specific code isolated to adapters

2. **ExchangeFactory** (`core/exchanges/exchange_factory.py`)
   - Factory pattern for creating exchange adapters
   - Returns appropriate adapter based on exchange name
   - Supports: 'BINANCE', 'MEXC', 'LUNO'

3. **Concrete Adapters**
   - `BinanceAdapter` (`core/exchanges/binance_adapter.py`)
   - `MexcAdapter` (`core/exchanges/mexc_adapter.py`)
   - `LunoAdapter` (`core/exchanges/luno_adapter.py`)

4. **TradingEngine** (`core/engine.py`)
   - Main orchestration engine
   - Exchange-agnostic (uses adapter interface)
   - Manages strategies, risk, and execution

#### Data Flow

```
User Request
    ↓
TradingEngine
    ↓
ExchangeFactory.create_adapter(exchange_name)
    ↓
Specific Adapter (e.g., BinanceAdapter)
    ↓
CCXT Library
    ↓
Exchange API
```

### Strategy Pattern

**Current Strategies**:

1. **DynamicGridStrategy** (`strategies/grid_strategy_v2.py`)
   - Mean reversion with grid levels
   - ATR-based dynamic range (currently disabled, using static)
   - State: Locked when positions open, unlocked when empty
   - Buy/Sell logic based on grid levels

2. **Buy-the-Dip** (in engine.py)
   - Opportunistic buying on price drops
   - Long hold periods (60-365+ days)
   - Time-weighted take profit targets
   - Catastrophic floor stops

3. **SMA Trend** (in engine.py)
   - Golden cross/death cross signals
   - Trend-following approach

### Database Schema

**Database**: SQLite V3

**Key Tables** (from logger.py):

1. **positions**
   - Tracks open and closed positions
   - Columns: id, symbol, strategy, exchange, buy_price, amount, status, buy_timestamp, close_timestamp, close_price, profit, etc.

2. **trades**
   - Records all trades (buy/sell)
   - Columns: id, strategy, symbol, side, price, amount, timestamp, fee, rsi, position_id, engine_version

3. **bots**
   - Bot status tracking
   - Columns: name, status, total_trades, total_pnl, wallet_balance, last_updated

4. **circuit_breaker**
   - Safety mechanism state
   - Columns: is_open, reason, opened_at, total_losses, closed_at

5. **system_health**
   - Component health monitoring
   - Columns: component, status, message, metrics, last_updated

---

## Critical Issues & Resolutions

### Issue #1: MEXC Contamination (RESOLVED)

**Date**: 2026-01-09 to 2026-01-10

**Problem**: Despite selecting BINANCE exchange, system was creating MEXC positions and tracking MEXC latency.

**Root Cause**: Multiple hardcoded "MEXC" references in code:
1. `core/engine.py:50` - `ExchangeResilienceManager("MEXC")`
2. `core/engine.py:68` - `known_symbols_mexc.json`
3. `core/engine.py:350` - Always ran LUNO confluence monitoring
4. `core/logger.py:62,98` - Default parameter `exchange='MEXC'`

**Resolution**:
```python
# engine.py:50 - BEFORE
self.resilience_manager = ExchangeResilienceManager("MEXC")

# engine.py:50 - AFTER
self.resilience_manager = ExchangeResilienceManager(self.exchange_name)

# engine.py:68 - BEFORE
self.known_symbols_path = os.path.join(root_dir, 'data', 'known_symbols_mexc.json')

# engine.py:68 - AFTER
self.known_symbols_path = os.path.join(root_dir, 'data', f'known_symbols_{self.exchange_name.lower()}.json')

# engine.py:350 - BEFORE
self._check_luno_confluence_alerts()

# engine.py:350 - AFTER
# self._check_luno_confluence_alerts()  # DISABLED

# logger.py:62 - BEFORE
def log_trade(self, ..., exchange='MEXC', ...):

# logger.py:62 - AFTER
def log_trade(self, ..., exchange=None, ...):
    if exchange is None:
        exchange = self.exchange_name
```

**Verification**: Database now shows only BINANCE positions

**Files Modified**:
- `core/engine.py`
- `core/logger.py`

---

### Issue #2: Risk Manager Portfolio Mismatch (RESOLVED) ⚠️ CRITICAL

**Date**: 2026-01-11

**Problem**: After 17+ hours, bot created only 2 BTC positions and 0 ETH positions. All trading stopped with error:
```
🔴 RISK STOP: Daily loss limit reached: 98.50% (limit: 10.0%)
```

**Suspected Issue**: ETH Grid strategy not initializing (WRONG)

**Actual Root Cause**: Risk Manager initialized with default $10,000 portfolio, but test has only $500 actual capital.

**Calculation**:
```python
# risk_module.py initialization (WRONG)
portfolio_value = Decimal("10000")        # Default
daily_start_value = Decimal("10000")      # Baseline for loss calculation

# Actual test capital
BTC bot: initial_balance = 250
ETH bot: initial_balance = 250
Total: $500

# Each cycle, engine updates:
portfolio_value = $500  # Actual balance

# Daily loss check:
current_loss_pct = (($10,000 - $500) / $10,000) * 100
                 = 95% to 98.5% "loss"

# Risk Manager blocks trading:
if current_loss_pct > 10.0%:  # MODERATE risk level
    return False, "Daily loss limit reached: 98.50%"
```

**Why ETH Had 0 Positions**:
1. BTC Grid Bot created 2 positions first
2. After 2 positions, Risk Manager calculated ~98.5% loss
3. **ALL trading blocked** for both BTC and ETH
4. ETH never got a chance to create positions
5. Bot ran for 17+ hours in blocked state

**Resolution** - Added to `test_adapter_paper.py:109-116`:
```python
# ⚠️ CRITICAL FIX: Update Risk Manager with actual starting capital
# Risk Manager defaults to $10,000, but our test has only $500
# Without this, it thinks we lost 95% and blocks all trading!
total_initial_balance = sum(bot.get('initial_balance', 0) for bot in engine.active_bots)
from decimal import Decimal
engine.risk_manager.update_portfolio_value(Decimal(str(total_initial_balance)))
engine.risk_manager.daily_start_value = Decimal(str(total_initial_balance))
print(f"✅ Risk Manager initialized with ${total_initial_balance} starting capital", flush=True)
```

**Verification**:
- Startup shows: "✅ Risk Manager initialized with $500 starting capital"
- No RISK STOP messages in logs
- Both BTC and ETH bots evaluate every cycle

**Impact**: 17 hours of test time wasted, no performance data collected

**Files Modified**:
- `test_adapter_paper.py` (lines 109-116 added)

**Related Commits**:
- `a0d87d4` - fix: CRITICAL - Risk Manager blocking trades due to portfolio mismatch

---

### Issue #3: ETH Upper Limit Wrong (RESOLVED)

**Date**: 2026-01-10

**Problem**: ETH Grid Bot configured with $3,600 upper limit instead of proven $4,200

**Root Cause**: Initial test used $3,600 based on estimate, but OLD proven bot used $4,200

**Resolution**: Updated test_adapter_paper.py:
```python
# BEFORE
'upper_limit': 3600,    # Wrong

# AFTER
'upper_limit': 4200,    # PROVEN: $4.2K upper ($1.4K range) - FIXED!
```

**Verification**: Config now matches OLD proven parameters exactly

**Files Modified**:
- `test_adapter_paper.py`

---

## File Inventory

### Core Files - Modified

#### 1. `core/engine.py`

**Purpose**: Main trading engine orchestration

**Location**:
- Local: `/home/user/Cryptobot/core/engine.py`
- VPS: `/root/cryptobot_v3/core/engine.py`

**Size**: ~1,400 lines

**Key Methods**:
- `__init__()` - Initialize engine with exchange adapter
- `add_bot()` - Register bot configuration
- `run_cycle()` - Main loop for trading cycle
- `process_bot()` - Execute logic for single bot
- `execute_trade()` - Execute buy/sell orders
- `check_circuit_breaker()` - Safety mechanism

**Recent Changes**:

1. **Line 50** (MEXC fix):
```python
# BEFORE
self.resilience_manager = resilience_manager or ExchangeResilienceManager("MEXC")

# AFTER
self.resilience_manager = resilience_manager or ExchangeResilienceManager(self.exchange_name)
```

2. **Line 68** (MEXC fix):
```python
# BEFORE
self.known_symbols_path = os.path.join(root_dir, 'data', 'known_symbols_mexc.json')

# AFTER
self.known_symbols_path = os.path.join(root_dir, 'data', f'known_symbols_{self.exchange_name.lower()}.json')
```

3. **Line 350** (LUNO disable):
```python
# BEFORE
self._check_luno_confluence_alerts()

# AFTER
# self._check_luno_confluence_alerts()  # DISABLED for BINANCE-only testing
```

4. **Lines 629-634** (Error logging for Grid):
```python
# ADDED: Check if strategy instance exists
if not strategy_instance:
    print(f"❌ [GRID ERROR] Strategy instance NOT FOUND for '{bot['name']}'!")
    print(f"   Available strategies: {list(self.strategies.keys())}")
    print(f"   Symbol: {symbol}")
    continue
```

**Dependencies**:
- ExchangeFactory (for adapter creation)
- TradeLogger (database operations)
- RiskManager (risk checks)
- TelegramNotifier (alerts)
- Indicators (RSI, SMA, ATR)
- DynamicGridStrategy (Grid Bot logic)

---

#### 2. `core/logger.py`

**Purpose**: Database operations and trade logging

**Location**:
- Local: `/home/user/Cryptobot/core/logger.py`
- VPS: `/root/cryptobot_v3/core/logger.py`

**Size**: ~800 lines

**Key Methods**:
- `log_trade()` - Record trade in database
- `open_position()` - Create new position record
- `close_position()` - Close position and calculate profit
- `get_open_positions()` - Query open positions
- `get_pnl_summary()` - Calculate profit/loss
- `get_wallet_balance()` - Calculate current balance

**Recent Changes**:

1. **Line 44** (Store exchange name):
```python
# ADDED
self.exchange_name = exchange_name if exchange_name else 'UNKNOWN'
```

2. **Line 62** (Remove MEXC default):
```python
# BEFORE
def log_trade(self, ..., exchange='MEXC', ...):

# AFTER
def log_trade(self, ..., exchange=None, ...):
    # Use logger's exchange name if not explicitly provided
    if exchange is None:
        exchange = self.exchange_name
```

3. **Line 98** (Remove MEXC default):
```python
# BEFORE
def open_position(self, ..., exchange='MEXC'):

# AFTER
def open_position(self, ..., exchange=None):
    # Use logger's exchange name if not explicitly provided
    if exchange is None:
        exchange = self.exchange_name
```

**Database Tables** (created by this module):
- positions
- trades
- bots
- circuit_breaker
- system_health
- portfolio_snapshots
- new_coin_watchlist

---

#### 3. `core/risk_module.py`

**Purpose**: Risk management and portfolio protection

**Location**:
- Local: `/home/user/Cryptobot/core/risk_module.py`
- VPS: `/root/cryptobot_v3/core/risk_module.py`

**Size**: ~640 lines

**Key Classes**:
- `RiskLevel` - Enum for risk tolerance (CONSERVATIVE, MODERATE, AGGRESSIVE)
- `RiskLimits` - Risk parameters dataclass
- `RiskManager` - Main risk management logic

**Key Methods**:
- `check_daily_loss_limit()` - Check if daily loss exceeded (LINE 168-187)
- `check_cooldown()` - Check if in cooldown period
- `validate_new_trade()` - Master validation before trades
- `check_portfolio_heat()` - Check total exposure
- `update_portfolio_value()` - Update current portfolio value

**Critical Issue** (LINE 638):
```python
def setup_safe_trading_bot(user_risk_level: str) -> 'RiskManager':
    return RiskManager(
        limits=RiskLimits.from_risk_level(level),
        portfolio_value=Decimal("10000")  # ⚠️ HARDCODED DEFAULT - Issue #2 root cause
    )
```

**Note**: This default value caused Issue #2. Fix applied in test script instead of modifying this file.

**Risk Limits (MODERATE)**:
- Max position size: 2.0% of portfolio
- Max daily loss: 10.0%
- Max drawdown: 20.0%
- Max concurrent positions: 5
- Consecutive loss limit: 4
- Cooldown after losses: 30 minutes

---

#### 4. `test_adapter_paper.py`

**Purpose**: Paper trading test script for adapter pattern

**Location**:
- Local: `/home/user/Cryptobot/test_adapter_paper.py`
- VPS: `/root/cryptobot_v3/test_adapter_paper.py`

**Size**: ~170 lines

**Purpose**: Test Grid Bot strategy with PROVEN parameters from OLD bots

**Configuration**:
```python
VERSION_ID = "2026.01.09-ADAPTER-TEST-BINANCE"
TRADING_MODE = 'paper'
EXCHANGE = 'BINANCE'
```

**Bot Configurations**:

**BTC Grid Bot**:
```python
{
    'name': 'Test Grid Bot BTC',
    'type': 'Grid',
    'symbols': ['BTC/USDT'],
    'amount': 25,           # $25 per trade
    'grid_levels': 20,      # 20 levels
    'atr_multiplier': 2.0,  # 2.0 ATR
    'atr_period': 14,
    'lower_limit': 85000,   # $85K lower
    'upper_limit': 110000,  # $110K upper ($25K range)
    'initial_balance': 250, # $250 budget
    'max_exposure_per_coin': 250
}
```

**ETH Grid Bot**:
```python
{
    'name': 'Test Grid Bot ETH',
    'type': 'Grid',
    'symbols': ['ETH/USDT'],
    'amount': 25,           # $25 per trade
    'grid_levels': 30,      # 30 levels
    'atr_multiplier': 2.5,  # 2.5 ATR
    'atr_period': 14,
    'lower_limit': 2800,    # $2.8K lower
    'upper_limit': 4200,    # $4.2K upper ($1.4K range)
    'initial_balance': 250, # $250 budget
    'max_exposure_per_coin': 250
}
```

**Critical Addition** (Lines 109-116):
```python
# ⚠️ CRITICAL FIX: Update Risk Manager with actual starting capital
# Risk Manager defaults to $10,000, but our test has only $500
# Without this, it thinks we lost 95% and blocks all trading!
total_initial_balance = sum(bot.get('initial_balance', 0) for bot in engine.active_bots)
from decimal import Decimal
engine.risk_manager.update_portfolio_value(Decimal(str(total_initial_balance)))
engine.risk_manager.daily_start_value = Decimal(str(total_initial_balance))
print(f"✅ Risk Manager initialized with ${total_initial_balance} starting capital", flush=True)
```

**Test Loop**:
```python
while engine.is_running:
    if check_stop_signal():
        break
    engine.run_cycle()
    time.sleep(300)  # 5 minutes between cycles
```

**Stop Mechanism**: Creates `STOP_SIGNAL` file in root directory

**Database**: `data/test_adapter_binance_paper.db`

**Logs**: `test_proven_config.log` (on VPS)

---

#### 5. `strategies/grid_strategy_v2.py`

**Purpose**: Dynamic Grid Bot strategy implementation

**Location**:
- Local: `/home/user/Cryptobot/strategies/grid_strategy_v2.py`
- VPS: `/root/cryptobot_v3/strategies/grid_strategy_v2.py`

**Size**: ~166 lines

**Class**: `DynamicGridStrategy`

**Key Features**:
- ATR-based dynamic range (currently disabled via line 89)
- Static range enforcement with upper/lower limits
- Grid locking when positions are open
- Buy signals when price near grid level
- Sell signals when profit target reached

**Grid Calculation** (Lines 37-60):
```python
def calculate_grids(self, df):
    """Calculate grid levels based on SMA +/- ATR * multiplier"""
    sma = calculate_sma(df['close'], self.ma_period).iloc[-1]
    atr = calculate_atr(df, self.atr_period).iloc[-1]

    half_range = atr * self.atr_multiplier
    self.lower_limit = sma - half_range
    self.upper_limit = sma + half_range

    self.grids = np.linspace(self.lower_limit, self.upper_limit, self.grid_levels)
```

**Static Range Enforcement** (Line 89):
```python
# FORCE STATIC GRIDS FOR PROFITABILITY
if False and not self.is_locked and df is not None:  # Disabled by False
    if self.calculate_grids(df):
        pass
```

**Signal Logic** (Lines 105-152):
1. Check for SELL opportunities (existing positions with profit)
2. Check for BUY opportunities (price near grid level without existing position)
3. Stop-grid protection (don't buy below lower limit)
4. Grid level matching with tolerance

**Debug Output** (Line 72):
```python
print(f"[GRID DEBUG] {self.symbol}: Price=${current_price:.2f}, Lower=${self.lower_limit}, Upper=${self.upper_limit}")
```

**No Recent Changes**: This file working as designed

---

### Core Files - Unchanged (Reference Only)

#### 6. `core/exchanges/base_adapter.py`

**Purpose**: Abstract base class for exchange adapters

**Methods** (must be implemented by subclasses):
- `fetch_ohlcv()`
- `create_order()`
- `fetch_balance()`
- `fetch_ticker()`
- `fetch_order_book()`

#### 7. `core/exchanges/binance_adapter.py`

**Purpose**: Binance-specific exchange implementation

**Currently Active**: This adapter is being used in current test

#### 8. `core/exchanges/exchange_factory.py`

**Purpose**: Factory for creating exchange adapters

**Method**: `create_adapter(exchange_name, mode)`

#### 9. `utils/indicators.py`

**Purpose**: Technical indicator calculations

**Functions**:
- `calculate_rsi()` - Relative Strength Index
- `calculate_sma()` - Simple Moving Average
- `calculate_atr()` - Average True Range
- `calculate_ema()` - Exponential Moving Average

---

### Documentation Files - Created This Session

#### 10. `DEPLOY_RISK_FIX.md`

**Purpose**: Step-by-step deployment guide for Risk Manager fix

**Location**: Repository root

**Contents**:
- Quick deployment commands
- Verification steps
- Expected outputs
- Troubleshooting

**Created**: 2026-01-11 (commit c4b6585)

---

#### 11. `docs/GRID_BOT_ISSUE_RESOLUTION.md`

**Purpose**: Complete investigation and resolution documentation for Issue #2

**Location**: `docs/` directory

**Contents**:
- Executive summary
- Investigation timeline
- Root cause analysis
- The fix with code samples
- Lessons learned
- Verification checklist

**Created**: 2026-01-11 (commit 66ca1ad)

**Size**: ~309 lines

---

#### 12. `docs/DIAGNOSE_ETH_GRID_ISSUE.md`

**Purpose**: Diagnostic procedures for Grid Bot issues

**Location**: `docs/` directory

**Contents**:
- Quick diagnostics commands
- Root cause scenarios
- Expected debug output
- Decision tree for troubleshooting

**Created**: 2026-01-11 (commit bf91d46)

---

#### 13. `diagnose_eth_grid.sh`

**Purpose**: Automated diagnostic script

**Location**: Repository root

**Usage**:
```bash
cd /root/cryptobot_v3
bash diagnose_eth_grid.sh > diagnostic_output.txt
```

**Checks**:
1. Is ETH bot being evaluated?
2. Was ETH strategy initialized?
3. Are there ETH-specific errors?
4. Are signals being generated?
5. Database position counts
6. Active bots configured
7. Recent cycle activity

**Created**: 2026-01-11 (commit bf91d46)

**Executable**: Yes (`chmod +x`)

---

#### 14. `docs/ETH_GRID_ISSUE_SUMMARY.md`

**Purpose**: Summary of ETH Grid Bot investigation (before resolution)

**Location**: `docs/` directory

**Status**: Historical - Issue now resolved

**Created**: 2026-01-11 (commit 217260c)

---

#### 15. `VPS_ACTION_REQUIRED.md`

**Purpose**: Quick action guide for VPS deployment

**Location**: Repository root

**Contents**:
- Copy-paste commands for VPS
- What to look for
- Success checklist
- Troubleshooting

**Created**: 2026-01-11 (commit 4f655ac)

**Updated**: 2026-01-11 (after fix deployed)

---

#### 16. `fix_grid_debug_logging.py`

**Purpose**: Automation script for adding Grid Bot error logging

**Location**: Repository root

**Usage**: Applied manually, no need to run again

**Created**: 2026-01-11 (commit bf91d46)

---

### Diagnostic/Analysis Scripts

#### 17. `analyze_binance_markets.py`

**Purpose**: Analyze Binance markets for volatility and volume

**Location**: Repository root

**Created**: 2026-01-10 (during investigation)

**Usage**:
```bash
python3 analyze_binance_markets.py
```

**Output**:
- Top 20 coins by 24h volume
- Coins with 4-10% movement (ideal volatility)
- Grid bot candidates
- Buy-the-dip candidates

---

## Configuration Guide

### Environment Variables

**Required for Production**:

```bash
# Binance API Keys
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"

# Telegram Notifications
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Optional: CryptoPanic News
export CRYPTOPANIC_API_KEY="your_api_key"
```

**Set on VPS**:
```bash
# Add to ~/.bashrc or ~/.bash_profile
echo 'export BINANCE_API_KEY="..."' >> ~/.bashrc
echo 'export BINANCE_API_SECRET="..."' >> ~/.bashrc
echo 'export TELEGRAM_BOT_TOKEN="..."' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="..."' >> ~/.bashrc
source ~/.bashrc
```

---

### Risk Manager Configuration

**Current Setting**: MODERATE

**To Change** (in test script or production script):
```python
# Option 1: Pass custom risk manager
from core.risk_module import setup_safe_trading_bot
risk_manager = setup_safe_trading_bot('conservative')  # or 'aggressive'

engine = TradingEngine(
    mode='paper',
    exchange='BINANCE',
    risk_manager=risk_manager
)

# Option 2: Modify after creation (for fixing portfolio value)
from decimal import Decimal
engine.risk_manager.update_portfolio_value(Decimal("500"))
engine.risk_manager.daily_start_value = Decimal("500")
```

**Risk Levels**:

| Level | Max Position | Max Daily Loss | Max Drawdown | Max Positions | Cooldown |
|-------|--------------|----------------|--------------|---------------|----------|
| Conservative | 1.0% | 5.0% | 15.0% | 3 | 60 min |
| Moderate | 2.0% | 10.0% | 20.0% | 5 | 30 min |
| Aggressive | 5.0% | 15.0% | 25.0% | 8 | 15 min |

---

### Exchange Configuration

**Switching Exchanges**:

```python
# In test script
EXCHANGE = 'BINANCE'  # or 'MEXC', 'LUNO'

engine = TradingEngine(
    mode='paper',
    exchange=EXCHANGE,
    db_path=f'data/test_adapter_{EXCHANGE.lower()}_paper.db'
)
```

**Exchange-Specific Notes**:

- **BINANCE**: Most stable, high volume, recommended for production
- **MEXC**: More volatile coins, higher risk
- **LUNO**: Limited pairs, mainly BTC/ETH

---

### Grid Bot Configuration

**Template**:
```python
{
    'name': 'Grid Bot NAME',
    'type': 'Grid',
    'symbols': ['SYMBOL/USDT'],
    'amount': 25,              # Trade size in USDT
    'grid_levels': 20,         # Number of grid levels
    'atr_multiplier': 2.0,     # Range multiplier
    'atr_period': 14,          # ATR calculation period
    'lower_limit': 85000,      # Minimum price (static range)
    'upper_limit': 110000,     # Maximum price (static range)
    'initial_balance': 250,    # Starting capital for this bot
    'max_exposure_per_coin': 250  # Maximum exposure limit
}
```

**Parameter Guidelines**:

- **amount**: Trade size should be 1-5% of initial_balance
- **grid_levels**: More levels = more trades = more fees. 10-30 recommended.
- **Range**: Should cover expected price movement. Too wide = no trades, too narrow = outside range.
- **initial_balance**: Total capital allocated to this bot
- **max_exposure_per_coin**: Safety limit, typically = initial_balance

---

### Database Configuration

**Database Naming Convention**:
```
test_adapter_{exchange}_{mode}.db

Examples:
- test_adapter_binance_paper.db
- test_adapter_mexc_live.db
- trading_bot_binance_live.db
```

**Database Location**:
- All databases stored in `data/` directory
- Automatically created if doesn't exist
- SQLite V3 format

**Backup Procedure**:
```bash
# On VPS
cd /root/cryptobot_v3/data
cp test_adapter_binance_paper.db test_adapter_binance_paper.db.backup_$(date +%Y%m%d_%H%M%S)
```

---

## Testing Procedures

### Current Test: Grid Bot Paper Trading

**Objective**: Validate adapter pattern with PROVEN Grid Bot parameters

**Test Configuration**:
- Exchange: BINANCE
- Mode: Paper trading (zero risk)
- Duration: 48 hours
- Capital: $500 ($250 BTC + $250 ETH)
- Strategies: 2 Grid Bots (BTC and ETH)

**Test Script**: `test_adapter_paper.py`

**Expected Results** (48 hours):
- Total positions: 10-20 (combined BTC + ETH)
- Closed trades: 5-10 with profit
- Win rate: 80%+
- Total P&L: +$5 to +$20 (in stable market)
- Zero critical errors

**Monitoring**:

```bash
# On VPS - Monitor live
tail -f /root/cryptobot_v3/test_proven_config.log

# Check positions
sqlite3 /root/cryptobot_v3/data/test_adapter_binance_paper.db \
  "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;"

# Check for errors
grep -i error /root/cryptobot_v3/test_proven_config.log | tail -20

# Check for RISK STOP (should be NONE after fix)
grep "RISK STOP" /root/cryptobot_v3/test_proven_config.log
```

**Success Criteria**:
- ✅ No RISK STOP messages
- ✅ Both BTC and ETH creating positions
- ✅ Grid SELL signals executed with profit
- ✅ No critical errors or exceptions
- ✅ Exchange resilience stable

**Failure Criteria**:
- ❌ RISK STOP appearing (portfolio mismatch not fixed)
- ❌ Only one bot trading (strategy instance issue)
- ❌ No positions after 6 hours (grid logic issue)
- ❌ Crash/exception causing bot to stop

---

### How to Run a New Test

**1. Prepare Test Script**:

```python
#!/usr/bin/env python3
import time
import sys
import os
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.engine import TradingEngine

# Configuration
EXCHANGE = 'BINANCE'
MODE = 'paper'
DB_PATH = f'data/my_test_{EXCHANGE.lower()}_{MODE}.db'

# Initialize engine
engine = TradingEngine(
    mode=MODE,
    exchange=EXCHANGE,
    db_path=DB_PATH
)

# Add bot(s)
engine.add_bot({
    'name': 'My Test Bot',
    'type': 'Grid',
    'symbols': ['BTC/USDT'],
    'amount': 50,
    'grid_levels': 10,
    'atr_multiplier': 2.0,
    'atr_period': 14,
    'lower_limit': 85000,
    'upper_limit': 110000,
    'initial_balance': 1000,
    'max_exposure_per_coin': 1000
})

# CRITICAL: Fix Risk Manager portfolio value
total_initial_balance = sum(bot.get('initial_balance', 0) for bot in engine.active_bots)
engine.risk_manager.update_portfolio_value(Decimal(str(total_initial_balance)))
engine.risk_manager.daily_start_value = Decimal(str(total_initial_balance))
print(f"✅ Risk Manager initialized with ${total_initial_balance} starting capital")

# Run loop
while engine.is_running:
    engine.run_cycle()
    time.sleep(300)  # 5 minutes
```

**2. Deploy to VPS**:

```bash
# On local machine
git add my_test.py
git commit -m "Add new test script"
git push origin your-branch-name

# On VPS
cd /root/cryptobot_v3
git pull origin your-branch-name
```

**3. Run Test**:

```bash
# On VPS
cd /root/cryptobot_v3
nohup python3 my_test.py > my_test.log 2>&1 &
echo $!  # Note the PID
```

**4. Monitor**:

```bash
tail -f my_test.log
```

**5. Stop Test**:

```bash
# Graceful stop (if check_stop_signal implemented)
touch STOP_SIGNAL

# Force stop
kill <PID>
```

---

## Deployment Guide

### Initial VPS Setup

**1. Install Prerequisites**:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip git -y

# Install required Python packages
pip3 install ccxt pandas numpy python-telegram-bot requests python-dotenv
```

**2. Clone Repository**:

```bash
cd /root
git clone https://github.com/YourUsername/Cryptobot.git cryptobot_v3
cd cryptobot_v3
```

**3. Set Environment Variables**:

```bash
# Create .env file
cat > .env << 'EOF'
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EOF

# Or add to ~/.bashrc
echo 'export BINANCE_API_KEY="..."' >> ~/.bashrc
source ~/.bashrc
```

**4. Test Installation**:

```bash
python3 -c "import ccxt; print('CCXT OK')"
python3 -c "import pandas; print('Pandas OK')"
python3 -c "from core.engine import TradingEngine; print('Engine OK')"
```

---

### Deploying Code Updates

**Standard Workflow**:

```bash
# On VPS
cd /root/cryptobot_v3

# Check current status
git status
git branch

# Fetch latest changes
git fetch origin

# Checkout target branch
git checkout claude/priority1-enhancements-lXrIG

# Pull latest code
git pull origin claude/priority1-enhancements-lXrIG

# Verify files updated
git log -3 --oneline
```

**If Test is Running**:

```bash
# Stop test gracefully
touch STOP_SIGNAL
sleep 10

# Or force stop
ps aux | grep python | grep test_adapter
kill <PID>

# Pull updates
git pull origin your-branch-name

# Restart test
nohup python3 test_adapter_paper.py > test_proven_config.log 2>&1 &
```

---

### Production Deployment (Future)

**⚠️ NOT YET DONE - This is the plan**:

**1. Test Must Pass**:
- 48-hour paper trading test completed
- No critical errors
- Expected profit achieved
- Risk Manager working correctly

**2. Create Production Script**:

```python
# production_grid_bot.py
TRADING_MODE = 'live'  # ⚠️ REAL MONEY
EXCHANGE = 'BINANCE'
```

**3. Production Checklist**:
- [ ] Paper trading test passed (48 hours)
- [ ] Real API keys configured (not testnet)
- [ ] Starting capital confirmed ($500 or more)
- [ ] Risk Manager set to CONSERVATIVE for first week
- [ ] Telegram notifications working
- [ ] Database backup automated
- [ ] Kill switch tested
- [ ] Stop loss limits verified

**4. Go Live** (when ready):

```bash
# On VPS
cd /root/cryptobot_v3
nohup python3 production_grid_bot.py > production.log 2>&1 &

# Monitor closely for first 24 hours
tail -f production.log
```

---

## Current Status

### Test in Progress

**Started**: 2026-01-11 08:54 UTC

**Test Script**: `test_adapter_paper.py`

**Database**: `data/test_adapter_binance_paper.db`

**Logs**: `test_proven_config.log`

**PID**: 542118 (as of last check)

**Status**: 🟢 RUNNING

**Fix Applied**: ✅ Risk Manager initialized with $500 starting capital

**Expected Completion**: 2026-01-13 08:54 UTC (48 hours)

---

### Git Status

**Current Branch**: `claude/priority1-enhancements-lXrIG`

**Branch Purpose**: Adapter architecture testing and Grid Bot validation

**Last Commit**: `66ca1ad` - docs: add complete Grid Bot issue investigation and resolution

**Commits This Session** (2026-01-11):
```
66ca1ad - docs: add complete Grid Bot issue investigation and resolution
c4b6585 - docs: add deployment guide for Risk Manager fix
a0d87d4 - fix: CRITICAL - Risk Manager blocking trades due to portfolio mismatch
4f655ac - docs: add VPS action guide for ETH Grid Bot fix deployment
217260c - docs: add ETH Grid Bot issue summary and action plan
bf91d46 - feat: add comprehensive Grid Bot diagnostics and error logging
```

**Branch Status**: Ahead of remote by 0 commits (all pushed)

---

### Known Issues

**Active**:
- None currently

**Resolved**:
- ✅ Issue #1: MEXC contamination (2026-01-10)
- ✅ Issue #2: Risk Manager portfolio mismatch (2026-01-11)
- ✅ Issue #3: ETH upper limit wrong (2026-01-10)

---

### Monitoring Checklist

**Every Hour** (first 6 hours):
- [ ] Check if test still running: `ps aux | grep test_adapter`
- [ ] Check for RISK STOP: `tail -200 test_proven_config.log | grep "RISK STOP"`
- [ ] Check both bots evaluating: `tail -200 test_proven_config.log | grep "DEBUG.*Evaluating"`
- [ ] Check position count: Database query

**Once Per Day**:
- [ ] Check total positions created
- [ ] Check if any positions closed with profit
- [ ] Check for any errors: `grep -i error test_proven_config.log | tail -50`
- [ ] Verify disk space: `df -h`
- [ ] Verify logs not too large: `ls -lh *.log`

**Before Session Ends**:
- [ ] Document current status in this file
- [ ] Note any issues encountered
- [ ] Update Next Steps section
- [ ] Commit and push all changes

---

## Next Steps

### Immediate (Next 1-6 Hours)

1. **Monitor Test Startup** ✅ IN PROGRESS
   - Verify no RISK STOP messages
   - Verify both BTC and ETH bots evaluating
   - Check first positions created

2. **Verify Fix Working**
   - After 2-4 hours, check database has positions for BOTH BTC and ETH
   - Confirm no RISK STOP in logs
   - Verify positions count increasing

### Short Term (Next 1-2 Days)

3. **Complete 48-Hour Test**
   - Let test run uninterrupted
   - Monitor daily for issues
   - Collect performance data

4. **Evaluate Test Results**
   - Compare actual vs expected positions
   - Check win rate and profit
   - Verify no critical errors
   - Make GO/NO-GO decision for production

### Medium Term (Next Week)

5. **Prepare Production Deployment** (if test passes)
   - Create production script with LIVE mode
   - Set up automated backups
   - Configure monitoring alerts
   - Set Risk Manager to CONSERVATIVE for first week

6. **Document Production Setup**
   - Create production deployment guide
   - Document emergency procedures
   - Create performance benchmarks

### Long Term (Next Month)

7. **Integrate Priority 1 Enhancements**
   - Health Monitor system
   - Enhanced Adapter Config
   - Base Strategy improvements
   - Currently NOT active in test

8. **Add More Strategies**
   - Buy-the-Dip strategy testing
   - SMA Trend strategy validation
   - Multi-strategy coordination

9. **Multi-Exchange Support**
   - Test MEXC adapter
   - Test LUNO adapter
   - Cross-exchange arbitrage (future)

---

## Troubleshooting Guide

### Problem: "RISK STOP: Daily loss limit reached"

**Symptoms**: Bot stops trading, shows 95-98% loss

**Root Cause**: Risk Manager portfolio value mismatch

**Solution**: Verify Risk Manager initialization in test script:
```bash
grep "Risk Manager initialized with" test_proven_config.log
```

Should show: "✅ Risk Manager initialized with $500 starting capital"

If missing, add fix to test script (lines 109-116 of test_adapter_paper.py)

---

### Problem: Only one Grid Bot trading

**Symptoms**: BTC creates positions, ETH doesn't (or vice versa)

**Root Cause**: Strategy instance not created for one bot

**Solution**: Check logs for Grid initialization:
```bash
grep "DynamicGrid.*Initialized" test_proven_config.log
```

Should show BOTH:
- `[DynamicGrid] Initialized BTC/USDT`
- `[DynamicGrid] Initialized ETH/USDT`

Check for Grid ERROR messages:
```bash
grep "GRID ERROR" test_proven_config.log
```

---

### Problem: No positions created after many hours

**Symptoms**: Test running, no RISK STOP, but no trades

**Root Cause**: Market price outside grid range, or confluence checks blocking

**Solution**: Check grid debug messages:
```bash
tail -200 test_proven_config.log | grep "GRID DEBUG"
```

Verify current price vs configured range:
- BTC range: $85,000 - $110,000
- ETH range: $2,800 - $4,200

If price outside range, adjust grid limits in test script.

---

### Problem: Test stopped unexpectedly

**Symptoms**: Process not running, logs show error

**Solution**: Check for exception in logs:
```bash
tail -100 test_proven_config.log | grep -A 10 -i "exception\|traceback\|error"
```

Check system resources:
```bash
df -h           # Disk space
free -h         # Memory
top             # CPU usage
```

Restart test:
```bash
cd /root/cryptobot_v3
nohup python3 test_adapter_paper.py > test_proven_config.log 2>&1 &
```

---

### Problem: High latency warnings

**Symptoms**: "BINANCE performance degraded. Avg latency: XXXXms"

**Root Cause**: Network issues, VPS location, or Binance API load

**Solution**: Check network:
```bash
ping 8.8.8.8         # Internet connectivity
ping api.binance.com # Binance reachability
```

This is usually temporary and self-resolves. Bot will continue trading.

If persistent (>30 minutes), consider:
- VPS location closer to exchange
- Check VPS provider network status
- Verify no firewall blocking

---

### Problem: Database locked error

**Symptoms**: "database is locked" in logs

**Root Cause**: Multiple processes accessing same database

**Solution**: Check for duplicate processes:
```bash
ps aux | grep python | grep test_adapter
```

Kill duplicates, keep only one:
```bash
kill <PID_of_duplicate>
```

---

### Problem: Can't connect to GitHub

**Symptoms**: `git pull` fails with authentication error

**Solution**: Check SSH keys or use HTTPS:
```bash
# If using SSH, test connection
ssh -T git@github.com

# Or switch to HTTPS
git remote set-url origin https://github.com/YourUsername/Cryptobot.git
git pull origin your-branch-name
```

---

## Command Reference

### Quick Commands for VPS

```bash
# ============================================
# NAVIGATION
# ============================================
cd /root/cryptobot_v3          # Go to bot directory

# ============================================
# GIT OPERATIONS
# ============================================
git status                      # Check current status
git branch                      # Show current branch
git fetch origin               # Fetch latest changes
git pull origin BRANCH         # Pull specific branch
git checkout BRANCH            # Switch branch
git log --oneline -5          # Show recent commits

# ============================================
# PROCESS MANAGEMENT
# ============================================
ps aux | grep python | grep test_adapter  # Find test process
ps aux | grep test_adapter     # Alternative
kill PID                        # Stop process by PID
pkill -f test_adapter          # Stop by name
touch STOP_SIGNAL              # Graceful stop (if implemented)

# ============================================
# LOG MONITORING
# ============================================
tail -f test_proven_config.log              # Watch logs live
tail -100 test_proven_config.log            # Last 100 lines
tail -500 test_proven_config.log | grep ERROR  # Find errors
grep "RISK STOP" test_proven_config.log     # Search logs
grep -i error test_proven_config.log | tail -20  # Recent errors

# ============================================
# DATABASE QUERIES
# ============================================
# Position counts by symbol and status
sqlite3 data/test_adapter_binance_paper.db \
  "SELECT symbol, status, COUNT(*) FROM positions GROUP BY symbol, status;"

# All open positions
sqlite3 data/test_adapter_binance_paper.db \
  "SELECT * FROM positions WHERE status='OPEN';"

# Total profit/loss
sqlite3 data/test_adapter_binance_paper.db \
  "SELECT SUM(profit) as total_pnl FROM positions WHERE status='CLOSED';"

# Recent trades (last 10)
sqlite3 data/test_adapter_binance_paper.db \
  "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# Bot status
sqlite3 data/test_adapter_binance_paper.db \
  "SELECT * FROM bots;"

# ============================================
# FILE OPERATIONS
# ============================================
ls -lh *.log                    # List log files with sizes
ls -lh data/*.db               # List database files
du -sh data/                   # Check data directory size
df -h                          # Check disk space

# Backup database
cp data/test_adapter_binance_paper.db \
   data/test_adapter_binance_paper.db.backup_$(date +%Y%m%d_%H%M%S)

# ============================================
# SYSTEM STATUS
# ============================================
free -h                        # Memory usage
df -h                          # Disk usage
top                            # CPU and process monitor (press 'q' to quit)
uptime                         # System uptime and load

# ============================================
# TEST OPERATIONS
# ============================================
# Start test
nohup python3 test_adapter_paper.py > test_proven_config.log 2>&1 &
echo $!  # Show PID

# Check if test running
ps aux | grep test_adapter | grep -v grep

# Stop test gracefully
touch STOP_SIGNAL

# View startup messages
head -50 test_proven_config.log

# Check for RISK STOP (should be none after fix)
grep "RISK STOP" test_proven_config.log

# Check both bots evaluating
tail -200 test_proven_config.log | grep "DEBUG.*Evaluating"

# Check grid activity
tail -200 test_proven_config.log | grep "GRID DEBUG"
```

---

## Session Handover Checklist

When passing to another agent or resuming later, ensure:

### Code State
- [ ] All changes committed to Git
- [ ] All commits pushed to remote
- [ ] Current branch name documented
- [ ] No uncommitted changes: `git status` clean

### Test State
- [ ] Current test status documented (running/stopped)
- [ ] Test PID noted if running
- [ ] Last position count recorded
- [ ] Any errors documented

### Issues
- [ ] Any active issues documented in "Known Issues" section
- [ ] Workarounds documented
- [ ] Root causes identified if possible

### Updates to This Document
- [ ] Current Status section updated
- [ ] Next Steps section reviewed
- [ ] New files added to File Inventory
- [ ] New issues added to Critical Issues section
- [ ] Troubleshooting Guide updated with new solutions

### Verification
- [ ] This document committed and pushed
- [ ] All documentation files in sync
- [ ] VPS state matches documentation

---

## Glossary

**Adapter Pattern**: Design pattern isolating exchange-specific code into separate classes

**ATR (Average True Range)**: Volatility indicator used for grid range calculation

**Circuit Breaker**: Safety mechanism that stops trading after losses

**Confluence**: Agreement between multiple technical indicators

**Grid Bot**: Trading strategy using fixed price levels for buying/selling

**Grid Level**: Specific price point where bot may buy or sell

**Kill Switch**: Emergency stop mechanism for exchange issues

**Paper Trading**: Simulated trading with fake money for testing

**Position**: An open or closed trade tracked in database

**Resilience Manager**: Monitors exchange API health and latency

**Risk Manager**: Enforces portfolio protection rules (daily loss, position limits, etc.)

**Static Range**: Fixed upper/lower price limits for grid (vs dynamic ATR-based)

**Strategy Instance**: Object containing strategy state and logic

**VPS (Virtual Private Server)**: Remote Linux server running the bot 24/7

---

## Document Maintenance

### How to Update This Document

**When making code changes**:
1. Update File Inventory section with modified files
2. Add to Critical Issues if it's a bug fix
3. Update Configuration Guide if parameters changed
4. Update Current Status section

**When creating new files**:
1. Add to File Inventory with full description
2. Document purpose and usage
3. Add location (local and VPS paths)

**When deploying updates**:
1. Update Current Status section
2. Update Git Status section
3. Record test status

**When resolving issues**:
1. Move from "Known Issues" to "Critical Issues & Resolutions"
2. Document root cause
3. Document solution
4. Add to Troubleshooting Guide

### Document Version History

| Date | Version | Changes | Author/Session |
|------|---------|---------|----------------|
| 2026-01-11 | 1.0 | Initial creation | claude/priority1-enhancements-lXrIG |

---

## Contact & Support

### GitHub Repository
**URL**: https://github.com/YourUsername/Cryptobot (update with actual URL)

### Branch Naming Convention
`claude/{description}-{sessionID}`

Example: `claude/priority1-enhancements-lXrIG`

### How to Continue This Session

**For another Claude Agent**:
1. Read this entire document first
2. Check Current Status section
3. Review Next Steps section
4. Check running test: `ps aux | grep test_adapter`
5. Review recent logs: `tail -100 test_proven_config.log`
6. Continue with next task from Next Steps

**For human developer**:
1. All documentation in `docs/` directory
2. Deployment guide: `DEPLOY_RISK_FIX.md`
3. Issue resolution: `docs/GRID_BOT_ISSUE_RESOLUTION.md`
4. Quick reference: This document

---

## End of Document

**Last Updated**: 2026-01-11 09:00 UTC
**Document Status**: 🟢 CURRENT
**Test Status**: 🟢 RUNNING
**Next Review**: After 48-hour test completion

---

*This is a living document. Update it whenever significant changes are made to the codebase, configuration, or system state.*
