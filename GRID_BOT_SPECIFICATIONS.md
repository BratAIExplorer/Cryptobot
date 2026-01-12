# 🤖 Grid Bot Specifications - Current Test Configuration

**Date**: 2026-01-12
**Test Mode**: Paper Trading (Simulated)
**Exchange**: Binance (using real market data, simulated trades)
**Risk Profile**: AGGRESSIVE (5% position limit)
**Total Capital**: $500 USDT

---

## 💰 WALLET CONFIGURATION

### **Total Allocation**:
```
Total Test Capital:     $500 USDT
├── BTC Bot Budget:     $250 USDT (50%)
└── ETH Bot Budget:     $250 USDT (50%)
```

### **Per-Trade Allocation**:
```
BTC Grid Bot:           $25 USDT per trade (5% of total capital)
ETH Grid Bot:           $25 USDT per trade (5% of total capital)
```

### **Risk Manager Settings**:
```
Profile:                AGGRESSIVE
Max Position Size:      5% of portfolio per trade
Daily Loss Limit:       20% ($100 on $500)
Max Drawdown:           30% ($150 on $500)
Portfolio Start Value:  $500 USDT
```

---

## 🤖 GRID BOT #1: BTC/USDT

### **Trading Parameters**:
```yaml
Name:                   Test Grid Bot BTC
Symbol:                 BTC/USDT
Type:                   Grid Strategy
Status:                 ACTIVE
```

### **Grid Configuration**:
```yaml
Grid Levels:            20 levels
Trade Amount:           $25 per grid fill
Budget Allocation:      $250 (max exposure)
Max Exposure Per Coin:  $250 (can hold up to 10 positions @ $25 each)
```

### **Price Range** (Static Grid):
```yaml
Lower Limit:            $85,000 (grid activates below this)
Upper Limit:            $110,000 (grid activates above this)
Total Range:            $25,000 spread
Grid Spacing:           ~$1,250 per level ($25,000 / 20 levels)
```

### **Technical Indicators**:
```yaml
ATR Multiplier:         2.0x (volatility adjustment)
ATR Period:             14 candles
Entry Method:           ATR-based grid levels
Confluence Check:       BYPASSED (pure grid entry)
```

### **Expected Performance** (Based on OLD bot data):
```yaml
Trades per Day:         5-8 grid fills
Avg Profit per Trade:   $0.32 (1.27% net after fees)
Win Rate (Historical):  95%
Daily Expected Profit:  $1.60 - $2.56
Weekly Expected Profit: $11.20 - $17.92
```

---

## 🤖 GRID BOT #2: ETH/USDT

### **Trading Parameters**:
```yaml
Name:                   Test Grid Bot ETH
Symbol:                 ETH/USDT
Type:                   Grid Strategy
Status:                 ACTIVE
```

### **Grid Configuration**:
```yaml
Grid Levels:            30 levels
Trade Amount:           $25 per grid fill
Budget Allocation:      $250 (max exposure)
Max Exposure Per Coin:  $250 (can hold up to 10 positions @ $25 each)
```

### **Price Range** (Static Grid):
```yaml
Lower Limit:            $2,800 (grid activates below this)
Upper Limit:            $4,200 (grid activates above this)
Total Range:            $1,400 spread
Grid Spacing:           ~$47 per level ($1,400 / 30 levels)
```

### **Technical Indicators**:
```yaml
ATR Multiplier:         2.5x (higher volatility tolerance)
ATR Period:             14 candles
Entry Method:           ATR-based grid levels
Confluence Check:       BYPASSED (pure grid entry)
```

### **Expected Performance** (Based on OLD bot data):
```yaml
Trades per Day:         6-10 grid fills
Avg Profit per Trade:   $0.25 - $0.35 (after fees)
Win Rate (Historical):  92%
Daily Expected Profit:  $1.50 - $3.50
Weekly Expected Profit: $10.50 - $24.50
```

---

## 📡 BINANCE API CONFIGURATION

### **API Mode**: ✅ Paper Trading (Test Mode)

**What This Means**:
```yaml
Market Data:            ✅ REAL (Live prices from Binance API)
Order Execution:        📝 SIMULATED (No real money involved)
Balance Tracking:       📝 SIMULATED (Starts with $500 virtual USDT)
Trade History:          📝 LOGGED to local database
Risk:                   ✅ ZERO (No real funds at risk)
```

### **How Paper Trading Works**:

1. **Fetches Real Market Data**:
   ```python
   # Real Binance API call for current price
   ticker = exchange.fetch_ticker('BTC/USDT')
   current_price = ticker['last']  # e.g., $90,671.32
   ```

2. **Simulates Trade Execution**:
   ```python
   if self.mode == 'paper':
       # Simulated order (no real trade)
       return {
           'id': 'paper_binance_1234567890',
           'symbol': 'BTC/USDT',
           'side': 'BUY',
           'amount': 0.000276,  # ~$25 worth at $90,671
           'price': 90671.32,
           'status': 'closed',
           'mode': 'paper'  # ← Indicates simulated trade
       }
   ```

3. **Tracks Virtual Balance**:
   ```python
   # No real money, just tracking in database
   Virtual Balance: $500.00 USDT (starts)
   After Buy:       $475.00 USDT (tracking $25 trade)
   Open Position:   0.000276 BTC @ $90,671.32
   ```

### **API Credentials**:
```yaml
Required:               ❌ NO (paper mode doesn't need API keys)
Binance Test API:       ❌ NO (not using testnet)
Binance Live API:       ⚠️  OPTIONAL (only if set in environment)
Fallback:               ✅ Works without credentials in paper mode
```

**Note**: Your test is using **real Binance production prices** but with **simulated trades**. This gives you accurate market data for testing without any financial risk!

---

## 🎯 COMBINED PORTFOLIO METRICS

### **Capital Allocation**:
```yaml
Total Capital:          $500.00 USDT
├── BTC Allocation:     $250.00 (50%)
├── ETH Allocation:     $250.00 (50%)
└── Reserve/Unused:     $0.00 (100% deployed)
```

### **Position Limits**:
```yaml
Max BTC Positions:      10 positions @ $25 each = $250
Max ETH Positions:      10 positions @ $25 each = $250
Total Max Positions:    20 positions (10 BTC + 10 ETH)
Max Total Exposure:     $500 (100% of capital)
```

### **Expected Daily Performance** (Combined):
```yaml
Total Trades per Day:   10-18 grid fills (5-8 BTC + 6-10 ETH)
Daily Profit Range:     $3.10 - $6.06
Weekly Profit Range:    $21.70 - $42.42
Monthly Profit Range:   $93.00 - $181.80
```

### **Performance vs OLD Bots**:
```yaml
OLD Bots (MEXC):        $8,204 profit over test period
NEW Bots (Binance):     TBD (currently testing)
Exchange Difference:    Binance fees = MEXC fees (0.1% taker)
Expected Match:         YES (same parameters, similar fees)
```

---

## 📊 GRID STRATEGY MECHANICS

### **How Grid Trading Works**:

1. **Price Enters Range**:
   ```
   BTC Price: $90,000 (between $85K-$110K)
   └── Grid Bot ACTIVE, monitoring for entry signals
   ```

2. **Buy Signal (Price Drops)**:
   ```
   Grid Level Hit:     $89,500 (calculated via ATR)
   Action:             BUY $25 worth (~0.000279 BTC)
   Entry Price:        $89,500
   Target Sell:        $90,625 (~1.25% profit target)
   ```

3. **Sell Signal (Price Rises)**:
   ```
   Price Reaches:      $90,625
   Action:             SELL position @ $90,625
   Profit:             $1.125 (1.25%)
   After Fees:         ~$0.30 net profit (0.2% fees round trip)
   ```

4. **Repeat**:
   ```
   Grid bot continuously:
   - Buys on dips
   - Sells on rises
   - Profits from volatility
   - Works 24/7 automatically
   ```

---

## 🔧 TECHNICAL ARCHITECTURE

### **Exchange Adapter**:
```python
# Using BinanceAdapter (clean abstraction)
from core.exchanges.binance_adapter import BinanceAdapter

adapter = BinanceAdapter(mode='paper')
# ✅ Fetches real Binance prices
# 📝 Simulates order execution
# 🔒 Zero risk to real funds
```

### **Strategy Engine**:
```python
# Grid Strategy V2 (Enhanced)
from strategies.grid_strategy_v2 import DynamicGrid

strategy = DynamicGrid(
    symbol='BTC/USDT',
    levels=20,
    atr_multiplier=2.0,
    lower_limit=85000,
    upper_limit=110000
)
# ✅ ATR-based grid levels
# ✅ Static range enforcement
# ✅ Proven algorithm from OLD bots
```

### **Risk Management**:
```python
# AGGRESSIVE profile (allows $25 trades)
from core.risk_module import setup_safe_trading_bot

risk_manager = setup_safe_trading_bot('aggressive')
# ✅ 5% max position size ($25 on $500)
# ✅ 20% daily loss limit
# ✅ 30% max drawdown
# ✅ Portfolio tracking
```

---

## 📈 TEST EXPECTATIONS (48-Hour Run)

### **By Time Checkpoint**:

| Time | Expected Positions | Expected Profit | Status |
|------|-------------------|-----------------|--------|
| **0-2 hours** | 0-2 | $0-$1 | 🟡 Initializing |
| **2-6 hours** | 2-5 | $1-$2 | 🟢 Active |
| **6-12 hours** | 5-10 | $2-$4 | 🟢 Active |
| **12-24 hours** | 10-20 | $4-$8 | 🟢 Active |
| **24-48 hours** | 20-40 | $8-$16 | 🟢 Full Speed |

### **Success Criteria**:
```yaml
✅ Minimum Success:     10+ positions, 75%+ win rate, +$5 P&L
🎯 Target Success:      20+ positions, 85%+ win rate, +$10 P&L
🏆 Excellent Success:   40+ positions, 92%+ win rate, +$20 P&L
```

---

## 🔒 SAFETY FEATURES

### **Paper Trading Safeguards**:
```yaml
Real Money at Risk:     ❌ ZERO ($0.00)
Binance Account Impact: ❌ NONE (no real orders)
Worst Case Scenario:    📝 Bad data in local database
Database Location:      data/test_adapter_binance_paper.db
Reversible:             ✅ YES (just delete database & restart)
```

### **Kill Switch**:
```yaml
Manual Stop:            Create 'STOP_SIGNAL' file or Ctrl+C
Automatic Triggers:
  - Exchange disconnected (>260 failures)
  - API latency >5000ms
  - Risk Manager drawdown limit
  - Daily loss limit exceeded
```

---

## 📂 DATA & LOGS

### **Database Schema** (V3):
```sql
-- Positions table
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,              -- BTC/USDT or ETH/USDT
    position_type TEXT,       -- LONG
    quantity REAL,            -- Amount in crypto (e.g., 0.000276 BTC)
    entry_price REAL,         -- Buy price
    status TEXT,              -- OPEN or CLOSED
    created_at TIMESTAMP,
    exchange TEXT             -- BINANCE
);
```

### **Log Files**:
```yaml
Main Log:               test_proven_config.log
Bot Log:                bot.log
Database:               data/test_adapter_binance_paper.db
Monitor Script:         monitor_bot.sh
Performance Script:     check_bot_performance.sh
```

---

## 🎯 CURRENT TEST STATUS

**Started**: 2026-01-12 11:06 UTC (earlier test)
**Expected End**: 2026-01-14 11:06 UTC (48 hours)
**Monitoring**: Every 30 minutes via `monitor_bot.sh`
**Performance Check**: Available via `check_bot_performance.sh`

---

**Summary**: You have **TWO Grid Bots** (BTC + ETH) running in **paper trading mode** with **$500 virtual capital** ($250 each), using **REAL Binance market data** but **SIMULATED trades**. The configuration exactly matches your OLD profitable bots, now with the AGGRESSIVE risk profile to allow $25 trades.
