# 🎯 BINANCE-FIRST ARCHITECTURE & DEPLOYMENT PLAN

**Date:** January 8, 2026
**Status:** Draft for Approval
**Priority:** CRITICAL - Production Deployment Roadmap

---

## 🚨 EXECUTIVE SUMMARY

### Critical Findings

**CURRENT STATE:**
- ❌ **NO BOTS RUNNING** (neither Binance nor MEXC)
- ⚠️ **Last Binance Trading:** Dec 1-5, 2025 (147 trades, +$277 profit, then STOPPED)
- ⚠️ **MEXC Trading:** Dec 5-30, 2025 (270 trades, +$9,667 profit, then STOPPED)
- ❌ **Architecture:** Hardcoded to MEXC (run_bot.py:59)
- ⚠️ **Root Cause:** Unknown why bots stopped on both exchanges

**TARGET STATE:**
- ✅ **Binance** = PRIMARY trading exchange
- ✅ **LUNO** = Monitoring + intelligence only (no trading bots)
- ⚠️ **MEXC** = EXCLUDED for now (future optional via adapters)

**RECOMMENDATION:**
**DO NOT RESTART BOTS** until architecture is Binance-ready.
Current code is hardcoded to MEXC and will trade on wrong exchange.

---

## 📊 HISTORICAL PERFORMANCE ANALYSIS

### Binance Trading (Dec 1-5, 2025)

| Bot | Trades | PnL | Status |
|-----|--------|-----|--------|
| Hyper-Scalper Bot | 134 | **+$276.96** | ⚠️ Stopped Dec 5 |
| SMA Trend Bot | 5 | $0.00 | Idle |
| Buy-the-Dip | 8 | $0.00 | Idle |

**Key Metrics:**
- Total Trades: 147
- Trading Volume: $117,987
- Duration: 4 days
- **Why Stopped:** Unknown - requires investigation

**Symbols Traded:** BTC, ETH, SOL, ADA, DOGE, DOT, XRP, ATOM, UNI, NEAR, APT, ICP, PEPE

---

### MEXC Trading (Dec 5-30, 2025) - ⚠️ IGNORE THIS DATA

| Bot | Trades | PnL | Notes |
|-----|--------|-----|-------|
| Grid Bot ETH | 112 | +$6,474 | **Do not migrate to Binance** |
| Grid Bot BTC | 48 | +$1,729 | Different fee structure |
| Hidden Gem Monitor | 110 | +$1,462 | MEXC-specific symbols |

**⚠️ CRITICAL:** These results are MEXC-specific and should NOT be used for Binance projections due to:
- Different fee structures (MEXC: 0.025% vs Binance: 0.1%)
- Different order book depth
- Different available symbols
- Different API rate limits

**Action:** Archive this data, focus on Binance validation.

---

## 🏗️ ARCHITECTURE ROADMAP

### Phase 1: CRITICAL - Binance Foundation (Week 1)
**Goal:** Make system Binance-ready without hardcoded exchange dependencies

#### Milestone 1.1: Adapter Pattern Implementation (3 days)
**Why Critical:**
Current code hardcodes `exchange='MEXC'` in run_bot.py:59. Without adapters, you risk:
- Accidentally trading on MEXC when you meant Binance
- Can't run Binance and LUNO simultaneously
- Every exchange change requires code edits

**Deliverables:**
```
core/adapters/
├── __init__.py
├── base_adapter.py         # Abstract interface
├── binance_adapter.py      # PRIMARY - Binance implementation
└── luno_adapter.py         # MONITORING ONLY - Read-only
```

**Acceptance Criteria:**
- [ ] No hardcoded `exchange='MEXC'` anywhere
- [ ] Can switch Binance ↔ LUNO with config change only
- [ ] Each adapter declares capabilities (trading vs monitoring)
- [ ] All existing Binance functionality works through adapter

**Files to Modify:**
- `run_bot.py` - Remove line 59 hardcoded MEXC
- `core/engine.py` - Use adapter factory
- DELETE: Hardcoded MEXC references
- NEW: Adapter architecture

---

#### Milestone 1.2: Exchange-Scoped Database (2 days)
**Why Critical:**
Prevent Binance/LUNO data contamination. One corrupted query shouldn't affect both.

**Deliverables:**
```
data/
├── binance/
│   ├── trades.db           # Binance trading data
│   ├── positions.db        # Open positions
│   └── bot_status.db       # Bot health metrics
├── luno/
│   ├── portfolio.db        # HODL tracking
│   └── intelligence.db     # Market data for future purchases
└── shared/
    └── regime.db           # Market regime (shared intelligence)
```

**Acceptance Criteria:**
- [ ] Separate SQLite file per exchange
- [ ] Binance queries can't touch LUNO data
- [ ] Migration script for historical Binance data
- [ ] All trades tagged with exchange name

**Data Migration:**
```bash
# Migrate old Binance data (Dec 1-5)
python scripts/migrate_binance_data.py \
  --source data/trades.db.bak_Dec9 \
  --dest data/binance/trades.db
```

---

#### Milestone 1.3: Exchange Kill Switches (2 days)
**Why Critical:**
Both Binance and MEXC bots mysteriously stopped. You need emergency controls.

**Deliverables:**
```python
# Independent kill switches per exchange
kill_switch_binance.activate(reason="High latency detected")
kill_switch_luno.activate(reason="Manual pause")

# Binance continues trading unaffected
```

**Triggers:**
- **API Latency:** Auto-pause if >500ms for 3 consecutive calls
- **Order Failure Rate:** Auto-pause if >5% orders fail
- **Manual Override:** Telegram command `/kill binance`
- **Circuit Breaker:** Daily loss limit exceeded

**Acceptance Criteria:**
- [ ] Can kill Binance without affecting LUNO monitoring
- [ ] Auto-pause on API degradation
- [ ] Telegram alert on activation
- [ ] Requires manual approval to resume

---

#### Milestone 1.4: LUNO Monitoring-Only Mode (1 day)
**Why Critical:**
LUNO is for HODL tracking, not active trading. Prevent accidental trades.

**Deliverables:**
```python
class LunoAdapter(BaseAdapter):
    """
    Read-only adapter for portfolio monitoring
    Trading methods raise NotImplementedError
    """

    def fetch_balance(self):
        return self.exchange.fetch_balance()  # ✅ OK

    def create_order(self, *args):
        raise PermissionError("LUNO is monitoring-only!")  # ❌ BLOCKED
```

**Acceptance Criteria:**
- [ ] Can fetch LUNO balances
- [ ] Can fetch LUNO prices
- [ ] CANNOT place orders (hard-coded block)
- [ ] LUNO data stored in `data/luno/portfolio.db`

---

### Phase 2: Production Readiness (Week 2-3)
**Goal:** Binance bot ready for paper trading validation

#### Milestone 2.1: Position Reconciliation (2 days)
**Why:** Detect when database doesn't match Binance reality

**Implementation:**
```python
# Every 5 minutes:
db_positions = get_db_positions('binance')
api_positions = binance_adapter.fetch_positions()

if mismatch_detected:
    alert_telegram("⚠️ Position drift on Binance!")
    pause_binance_trading()
```

**Acceptance Criteria:**
- [ ] 5-minute reconciliation loop
- [ ] Alert on >$1 discrepancy
- [ ] Auto-pause on critical mismatch
- [ ] Manual override available

---

#### Milestone 2.2: Binance Health Monitoring (2 days)
**Why:** Detect exchange issues BEFORE they cause losses

**Monitors:**
```python
binance_health = {
    'api_latency': check_latency(),      # Alert if >500ms
    'order_success_rate': check_orders(), # Alert if <95%
    'system_status': check_binance_api(), # Check status page
    'rate_limits': check_rate_usage(),    # Alert at 80%
}
```

**Acceptance Criteria:**
- [ ] Latency alerts within 60 seconds
- [ ] Auto-pause on degradation
- [ ] Dashboard shows health status
- [ ] Logs all health checks

---

#### Milestone 2.3: API Key Security (2 days)
**Why:** Protect production Binance API keys

**Requirements:**
```bash
# Binance API key restrictions:
✅ Enable: Spot Trading, Read Account Info
❌ Disable: Withdrawals, Margin Trading, Futures
✅ IP Whitelist: <your VPS IP>
✅ Key Rotation: Every 90 days
```

**Implementation:**
- [ ] Keys stored encrypted at rest
- [ ] Keys loaded from environment only
- [ ] Pre-flight check validates permissions
- [ ] Documentation for key setup

---

### Phase 3: Binance Validation (Week 3-4)
**Goal:** Prove Binance bots work before live capital

#### Milestone 3.1: Paper Trading Test (72 hours)
**Why:** Validate bots on Binance paper trading

**Configuration:**
```python
engine = TradingEngine(
    mode='paper',
    exchange='Binance',  # ✅ Using adapter
    db_path='data/binance/trades.db'
)

# Test with small positions
grid_bot = {
    'amount': 20,  # $20 per order
    'initial_balance': 500,  # $500 test allocation
}
```

**Success Criteria:**
- [ ] Zero crashes for 72 hours
- [ ] All orders execute successfully
- [ ] Database reconciliation 100% accurate
- [ ] Health monitoring detects no issues
- [ ] At least 20 trades executed

---

#### Milestone 3.2: Live Micro-Test ($100, 48 hours)
**Why:** Final validation with real capital

**Configuration:**
```python
mode='live'
initial_capital = 100  # $100 ONLY
max_position_size = 10  # $10 max per trade
daily_loss_limit = 20   # Stop at -$20
```

**Success Criteria:**
- [ ] No technical errors
- [ ] Position reconciliation perfect
- [ ] Kill switches respond correctly
- [ ] Can manually pause/resume
- [ ] P&L tracking accurate

**Proceed to Full Deployment If:**
- ✅ No technical failures
- ✅ P&L ± 5% of paper trading expectations
- ✅ All safety systems work

---

### Phase 4: LUNO Monitoring Integration (Week 4-5)
**Goal:** Add LUNO portfolio tracking alongside Binance trading

#### Milestone 4.1: LUNO Read-Only Adapter (2 days)

**Deliverables:**
```python
# Monitor LUNO holdings
luno_monitor = LunoAdapter(mode='monitoring')

portfolio = {
    'BTC': luno_monitor.get_balance('BTC'),
    'ETH': luno_monitor.get_balance('ETH'),
    'XRP': luno_monitor.get_balance('XRP'),
}

# Share intelligence with Binance bots
regime = detect_market_regime(luno_prices + binance_prices)
```

**Use Cases:**
- Track long-term HODL balances
- Aggregate portfolio value (Binance + LUNO)
- Share price data for correlation analysis
- Alert on good accumulation opportunities

**Acceptance Criteria:**
- [ ] Fetches LUNO balances every 15 min
- [ ] Stores in `data/luno/portfolio.db`
- [ ] Dashboard shows combined portfolio
- [ ] Trading methods are BLOCKED

---

#### Milestone 4.2: Cross-Exchange Intelligence (3 days)

**Shared Intelligence Layer:**
```python
# Market regime affects both exchanges
regime_detector = RegimeDetector(
    sources=['binance', 'luno']  # Combined data
)

# If market is CRISIS:
- Pause Binance trading
- Monitor LUNO for DCA opportunities
- Alert when regime shifts to BEAR/BULL
```

**Acceptance Criteria:**
- [ ] Regime detection uses both exchanges
- [ ] Correlation tracking prevents duplicates
- [ ] Shared data stored in `data/shared/`
- [ ] Each exchange can operate independently

---

### Phase 5: Scale & Optimize (Month 2+)
**Goal:** Optimize Binance performance, prepare for optional MEXC

#### Milestone 5.1: Binance Strategy Optimization (Week 5-8)

**Focus Areas:**
1. **Grid Bots** - Proven on MEXC, adapt for Binance fees
2. **Buy-the-Dip** - Investigate why 0 trades on old Binance run
3. **SMA Trend** - Debug entry conditions
4. **Remove:** Broken strategies (Dip Sniper, etc.)

**Approach:**
- 2-week backtest on Binance historical data
- Adjust parameters for 0.1% fees (vs MEXC 0.025%)
- Validate on paper trading
- Deploy incrementally

---

#### Milestone 5.2: MEXC Optional Adapter (Week 9-10)
**Why Deferred:** Only add after Binance is stable and profitable

**Criteria to Add MEXC:**
- ✅ Binance profitable for 1+ month
- ✅ Adapter pattern proven stable
- ✅ User explicitly requests MEXC
- ✅ Have strategy that needs MEXC-specific symbols

**Implementation:**
```python
# Future: Easy to add MEXC
from core.adapters import BinanceAdapter, LunoAdapter, MexcAdapter

binance = BinanceAdapter(mode='live')
mexc = MexcAdapter(mode='paper')  # Test first
```

---

## 🔍 ROOT CAUSE INVESTIGATION: Why Did Bots Stop?

### Critical Questions to Answer (Week 1)

#### 1. Binance Stoppage (Dec 5)
**Hypothesis:**
- API key expired or permissions changed?
- Exchange maintenance?
- Code crash during migration to MEXC?
- Manual shutdown?

**Investigation:**
```bash
# Check logs from Dec 5
grep "2025-12-05" logs/*.log

# Check git commits on Dec 5
git log --since="2025-12-05" --until="2025-12-06"

# Check Binance API status history
```

---

#### 2. MEXC Stoppage (Dec 30)
**Hypothesis:**
- Paper trading database full?
- Circuit breaker triggered?
- VPS reboot?
- Manual shutdown for holidays?

**Investigation:**
```bash
# Check system logs
journalctl --since "2025-12-30 00:00" --until "2025-12-31 00:00"

# Check database size (72MB - not full)
# Check circuit breaker status (checked - none active)
```

---

### Preventive Measures

**Implement in Phase 1:**
```python
# Automatic restart on crash
systemd_service = """
[Unit]
Description=Binance Trading Bot
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=60
ExecStart=/usr/bin/python3 /home/user/Cryptobot/run_bot_binance.py

[Install]
WantedBy=multi-user.target
"""
```

**Monitoring:**
- [ ] Heartbeat every 5 minutes
- [ ] Alert if no heartbeat for 15 minutes
- [ ] Daily status report via Telegram
- [ ] Auto-restart on crash (with limit)

---

## 📋 DETAILED BACKLOG

### 🔴 P0: BLOCKING - MUST DO BEFORE ANY TRADING

#### P0-1: Create Binance Adapter (3 days)
**Owner:** TBD
**Priority:** CRITICAL
**Blocks:** Everything else

**Tasks:**
- [ ] Create `core/adapters/base_adapter.py`
  - Define abstract interface
  - Methods: fetch_ticker, create_order, fetch_balance, etc.
  - Capability declaration (trading/monitoring)

- [ ] Create `core/adapters/binance_adapter.py`
  - Implement all BaseAdapter methods
  - Load Binance API keys from env
  - Set fee rates (0.1% maker/taker)
  - Add rate limiting (50ms)

- [ ] Create `core/adapters/luno_adapter.py`
  - Implement read-only methods
  - Block all trading methods
  - Set to monitoring-only mode

- [ ] Update `core/engine.py`
  - Add adapter factory
  - Remove hardcoded exchange logic
  - Support multi-exchange initialization

- [ ] Update `run_bot.py`
  - Remove line 59: `exchange='MEXC'`
  - Add: `exchange='Binance'`
  - Use adapter pattern

**Acceptance Tests:**
```python
# Test Binance adapter
adapter = BinanceAdapter(mode='paper')
ticker = adapter.fetch_ticker('BTC/USDT')
assert ticker['last'] > 0

# Test LUNO monitoring
luno = LunoAdapter(mode='monitoring')
balance = luno.fetch_balance()
assert balance is not None

# Test trading block
with pytest.raises(PermissionError):
    luno.create_order('BTC/ZAR', 'buy', 0.001)
```

**Estimated:** 3 days
**Dependencies:** None
**Risk:** High (foundation for everything)

---

#### P0-2: Exchange-Scoped Database Migration (2 days)
**Owner:** TBD
**Priority:** CRITICAL
**Blocks:** P0-3, P0-4

**Tasks:**
- [ ] Create directory structure
  ```bash
  mkdir -p data/binance data/luno data/shared
  ```

- [ ] Update `core/database.py`
  - Add `exchange` parameter to Database class
  - Path resolution: `data/{exchange}/trades.db`
  - Ensure all tables have exchange column

- [ ] Create migration script
  ```python
  # scripts/migrate_to_multi_exchange.py
  # Migrate data/trades.db.bak_Dec9 → data/binance/trades.db
  # Tag all records with exchange='Binance'
  ```

- [ ] Update all queries
  - Add WHERE exchange='Binance' filters
  - Update TradeLogger
  - Update PositionManager

- [ ] Test migration
  - Verify 147 Binance trades migrated
  - Verify no data loss
  - Verify correct date ranges

**Acceptance Tests:**
```python
# After migration
binance_db = Database(exchange='binance')
trades = binance_db.get_all_trades()
assert len(trades) == 147
assert all(t['exchange'] == 'Binance' for t in trades)

# LUNO DB should be empty
luno_db = Database(exchange='luno')
assert luno_db.get_trade_count() == 0
```

**Estimated:** 2 days
**Dependencies:** P0-1
**Risk:** Medium (data migration always risky)

---

#### P0-3: Exchange Kill Switches (2 days)
**Owner:** TBD
**Priority:** CRITICAL
**Blocks:** P0-5

**Tasks:**
- [ ] Create `core/kill_switch.py`
  ```python
  class ExchangeKillSwitch:
      def __init__(self, exchange_name):
          self.exchange = exchange_name
          self.active = False

      def activate(self, reason):
          # Pause trading for this exchange
          # Send Telegram alert
          # Log to database

      def check_triggers(self):
          # Check API latency
          # Check order failure rate
          # Check circuit breaker
  ```

- [ ] Add latency monitoring
  - Track API response times
  - Alert if >500ms for 3 consecutive calls
  - Auto-activate kill switch

- [ ] Add order failure tracking
  - Count failed orders
  - Alert if >5% failure rate
  - Auto-activate kill switch

- [ ] Integrate with TradingEngine
  ```python
  engine.add_exchange('Binance', binance_adapter, kill_switch_binance)

  # Before each trade:
  if kill_switch_binance.is_active():
      skip_trade()
  ```

- [ ] Add Telegram controls
  - `/kill binance` - Manual activation
  - `/resume binance` - Requires confirmation
  - `/status binance` - Check kill switch state

**Acceptance Tests:**
```python
# Test latency trigger
kill_switch = ExchangeKillSwitch('Binance')
kill_switch.record_latency(600)  # 600ms
kill_switch.record_latency(700)
kill_switch.record_latency(800)
assert kill_switch.is_active()

# Test manual activation
kill_switch.activate("Manual test")
assert kill_switch.is_active()
assert kill_switch.reason == "Manual test"
```

**Estimated:** 2 days
**Dependencies:** P0-1, P0-2
**Risk:** Low

---

#### P0-4: LUNO Monitoring Mode (1 day)
**Owner:** TBD
**Priority:** HIGH
**Blocks:** None

**Tasks:**
- [ ] Ensure LunoAdapter blocks trading
  ```python
  def create_order(self, *args, **kwargs):
      raise PermissionError(
          "LUNO is configured for monitoring only. "
          "Trading is not permitted."
      )
  ```

- [ ] Add portfolio tracking
  ```python
  # Every 15 minutes:
  luno_portfolio = luno_adapter.fetch_balance()
  save_to_db(luno_portfolio, exchange='luno')
  ```

- [ ] Add price monitoring
  - Fetch LUNO tickers for intelligence
  - Store in `data/luno/intelligence.db`
  - Share with regime detector

- [ ] Dashboard integration
  - Show LUNO balances (read-only)
  - Show combined portfolio value
  - Clear "MONITORING ONLY" label

**Acceptance Tests:**
```python
# Test trading block
luno = LunoAdapter(mode='monitoring')
with pytest.raises(PermissionError):
    luno.create_order('BTC/ZAR', 'buy', 0.001)

# Test read operations work
balance = luno.fetch_balance()
assert 'BTC' in balance

ticker = luno.fetch_ticker('BTC/ZAR')
assert ticker['last'] > 0
```

**Estimated:** 1 day
**Dependencies:** P0-1
**Risk:** Low

---

#### P0-5: Pre-Flight Checklist (1 day)
**Owner:** TBD
**Priority:** CRITICAL
**Blocks:** Phase 3 (deployment)

**Tasks:**
- [ ] Create `scripts/pre_flight_check.py`
  ```python
  checks = [
      check_no_hardcoded_exchange(),
      check_adapter_pattern_implemented(),
      check_kill_switches_configured(),
      check_database_separated(),
      check_api_keys_valid(),
      check_api_permissions(),
      check_luno_trading_blocked(),
  ]
  ```

- [ ] API Key validation
  - Check Binance keys exist
  - Verify permissions (trading enabled, withdrawal disabled)
  - Check IP whitelist configured

- [ ] Architecture validation
  - Grep for hardcoded 'MEXC'
  - Verify adapter imports
  - Check database paths

- [ ] Safety validation
  - Kill switches respond
  - Circuit breakers configured
  - Daily loss limits set

- [ ] Generate report
  ```
  ==========================================
  PRE-FLIGHT CHECK REPORT
  ==========================================
  ✅ Adapter pattern implemented
  ✅ Kill switches configured
  ✅ Database separated
  ❌ Binance API key not found

  VERDICT: NO-GO
  FIX: Set BINANCE_API_KEY environment variable
  ==========================================
  ```

**Acceptance Tests:**
```bash
# Should pass all checks
python scripts/pre_flight_check.py
# Exit code: 0

# Should fail if MEXC hardcoded
echo "exchange = 'MEXC'" > test.py
python scripts/pre_flight_check.py
# Exit code: 1
```

**Estimated:** 1 day
**Dependencies:** P0-1, P0-2, P0-3, P0-4
**Risk:** Low

---

### 🟠 P1: HIGH PRIORITY (Week 2-3)

#### P1-1: Position Reconciliation (2 days)
**Tasks:**
- [ ] Create `core/reconciliation.py`
- [ ] 5-minute reconciliation loop
- [ ] Alert on mismatch
- [ ] Auto-pause on critical mismatch

**Estimated:** 2 days

---

#### P1-2: Binance Health Monitoring (2 days)
**Tasks:**
- [ ] Monitor API latency
- [ ] Monitor order success rate
- [ ] Check Binance status API
- [ ] Integrate with kill switches

**Estimated:** 2 days

---

#### P1-3: API Key Security Hardening (2 days)
**Tasks:**
- [ ] Encrypt keys at rest
- [ ] Key rotation script
- [ ] Document IP whitelist setup
- [ ] Validate permissions in pre-flight

**Estimated:** 2 days

---

#### P1-4: Root Cause Investigation (3 days)
**Tasks:**
- [ ] Analyze why Binance stopped (Dec 5)
- [ ] Analyze why MEXC stopped (Dec 30)
- [ ] Document findings
- [ ] Implement preventive measures

**Estimated:** 3 days

---

#### P1-5: Systemd Auto-Restart (1 day)
**Tasks:**
- [ ] Create systemd service file
- [ ] Configure auto-restart on crash
- [ ] Add restart limits
- [ ] Test crash recovery

**Estimated:** 1 day

---

### 🟡 P2: MEDIUM PRIORITY (Week 3-4)

#### P2-1: Paper Trading Validation (3 days)
**Tasks:**
- [ ] 72-hour Binance paper test
- [ ] Monitor for crashes
- [ ] Validate order execution
- [ ] Check database reconciliation

**Estimated:** 3 days (mostly waiting)

---

#### P2-2: Investigate Idle Bots (2 days)
**Tasks:**
- [ ] Debug Buy-the-Dip (0 trades on Binance)
- [ ] Debug SMA Trend (0 trades on Binance)
- [ ] Add verbose logging
- [ ] Fix or remove

**Estimated:** 2 days

---

#### P2-3: Strategy Parameter Tuning for Binance (3 days)
**Tasks:**
- [ ] Adjust Grid Bot for 0.1% fees
- [ ] Backtest on Binance data
- [ ] Compare to MEXC results
- [ ] Update configurations

**Estimated:** 3 days

---

### 🟢 P3: LOW PRIORITY (Month 2+)

#### P3-1: LUNO Intelligence Integration (3 days)
**Tasks:**
- [ ] Cross-exchange regime detection
- [ ] Correlation tracking
- [ ] DCA opportunity alerts

**Estimated:** 3 days

---

#### P3-2: MEXC Optional Adapter (5 days)
**Deferred until:** Binance profitable for 1+ month

**Tasks:**
- [ ] Create mexc_adapter.py
- [ ] Test in isolation
- [ ] Add to multi-exchange setup
- [ ] Validate no cross-contamination

**Estimated:** 5 days

---

## 📅 DETAILED TIMELINE

### Week 1: Foundation (Jan 8-14)
**Goal:** Architecture ready, no trading yet

| Day | Tasks | Owner | Status |
|-----|-------|-------|--------|
| Mon | P0-1: Start Binance adapter | TBD | 🟡 Pending approval |
| Tue | P0-1: Continue adapter work | TBD | ⚪ Not started |
| Wed | P0-1: Complete adapter + tests | TBD | ⚪ Not started |
| Thu | P0-2: Database migration | TBD | ⚪ Not started |
| Fri | P0-3: Kill switches | TBD | ⚪ Not started |
| Sat | P0-4: LUNO monitoring | TBD | ⚪ Not started |
| Sun | P0-5: Pre-flight checklist | TBD | ⚪ Not started |

**Deliverable:** Binance-ready codebase, no hardcoded exchanges

---

### Week 2: Safety & Monitoring (Jan 15-21)
**Goal:** Production-grade safety systems

| Day | Tasks | Owner | Status |
|-----|-------|-------|--------|
| Mon | P1-1: Position reconciliation | TBD | ⚪ Not started |
| Tue | P1-2: Health monitoring | TBD | ⚪ Not started |
| Wed | P1-3: API key security | TBD | ⚪ Not started |
| Thu | P1-4: Root cause investigation | TBD | ⚪ Not started |
| Fri | P1-4: Continue investigation | TBD | ⚪ Not started |
| Sat | P1-5: Systemd setup | TBD | ⚪ Not started |
| Sun | Testing & documentation | TBD | ⚪ Not started |

**Deliverable:** Production-ready safety systems

---

### Week 3: Validation (Jan 22-28)
**Goal:** Prove system works on Binance

| Day | Tasks | Owner | Status |
|-----|-------|-------|--------|
| Mon | P2-1: Start 72h paper test | TBD | ⚪ Not started |
| Tue | P2-1: Monitor paper test | TBD | ⚪ Not started |
| Wed | P2-1: Monitor paper test | TBD | ⚪ Not started |
| Thu | P2-1: Complete paper test | TBD | ⚪ Not started |
| Fri | P2-2: Debug idle bots | TBD | ⚪ Not started |
| Sat | P2-3: Strategy tuning | TBD | ⚪ Not started |
| Sun | Prepare for live micro-test | TBD | ⚪ Not started |

**Deliverable:** 72-hour clean paper run

---

### Week 4: Live Deployment (Jan 29 - Feb 4)
**Goal:** Live trading with $100 test capital

| Day | Tasks | Owner | Status |
|-----|-------|-------|--------|
| Mon | M3.2: Start $100 live test | TBD | ⚪ Not started |
| Tue | M3.2: Monitor live test | TBD | ⚪ Not started |
| Wed | M3.2: Complete live test | TBD | ⚪ Not started |
| Thu | Review results, GO/NO-GO | TBD | ⚪ Not started |
| Fri | Scale to full capital OR fix issues | TBD | ⚪ Not started |
| Sat | Monitoring | TBD | ⚪ Not started |
| Sun | Week 1 live retrospective | TBD | ⚪ Not started |

**Deliverable:** Live Binance trading with full capital (if tests pass)

---

### Week 5+: LUNO & Optimization (Feb 5+)
**Goal:** Add LUNO monitoring, optimize Binance

| Week | Focus | Status |
|------|-------|--------|
| 5 | LUNO integration (P3-1) | ⚪ Not started |
| 6-8 | Strategy optimization | ⚪ Not started |
| 9+ | Optional MEXC (if needed) | ⚪ Deferred |

---

## ⚡ IMMEDIATE NEXT STEPS (Next 24 Hours)

### Decision Required: Approve This Plan

**Questions for You:**

1. **Approve Binance-first approach?**
   - ✅ Yes, Binance is primary
   - ❌ No, different priority

2. **Approve timeline (4 weeks to live)?**
   - ✅ Conservative timeline approved
   - ⚠️ Prefer faster (higher risk)
   - ⏸️ Prefer slower (lower risk)

3. **Approve MEXC exclusion?**
   - ✅ Yes, exclude MEXC for now
   - ⚠️ No, include MEXC in Phase 1

4. **Approve LUNO monitoring-only?**
   - ✅ Yes, no LUNO trading bots
   - ❌ No, want LUNO trading

---

### If Approved, Start Immediately:

**Action 1: Create Adapter Branch (5 min)**
```bash
git checkout -b feature/binance-adapter-pattern
```

**Action 2: Create Directory Structure (5 min)**
```bash
mkdir -p core/adapters
mkdir -p data/binance data/luno data/shared
mkdir -p scripts
```

**Action 3: Start P0-1 Implementation (Today)**
```bash
# Create base adapter interface
touch core/adapters/__init__.py
touch core/adapters/base_adapter.py
touch core/adapters/binance_adapter.py
touch core/adapters/luno_adapter.py
```

**Action 4: Update run_bot.py (Today)**
```python
# Change line 59 from:
exchange='MEXC',  # ❌ Old

# To:
exchange='Binance',  # ✅ New
```

---

## 🎯 SUCCESS CRITERIA

### Week 1 Success:
- [ ] No `exchange='MEXC'` in codebase
- [ ] Adapter pattern implemented
- [ ] Pre-flight check passes
- [ ] Code review approved

### Week 2 Success:
- [ ] Kill switches respond <1 second
- [ ] Health monitoring detects issues
- [ ] Position reconciliation 100% accurate
- [ ] Root cause of stoppages understood

### Week 3 Success:
- [ ] 72 hours paper trading, zero crashes
- [ ] >20 trades executed successfully
- [ ] Database reconciliation perfect
- [ ] No memory leaks or performance issues

### Week 4 Success:
- [ ] $100 live test completes without errors
- [ ] P&L within expectations
- [ ] All safety systems validated
- [ ] GO for full capital deployment

### Month 1 Success:
- [ ] Binance trading profitable
- [ ] LUNO monitoring active
- [ ] No emergency stops
- [ ] Ready to consider MEXC (optional)

---

## 🚨 RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Binance API key issues | Medium | High | Validate in pre-flight, test permissions |
| Database migration data loss | Low | Critical | Backup before migration, dry-run test |
| Kill switches don't activate | Low | High | Unit tests, manual trigger test |
| LUNO trading accidentally enabled | Low | Medium | Hard-coded PermissionError, pre-flight check |
| Bots stop again (unknown cause) | Medium | High | Root cause investigation, systemd auto-restart |
| MEXC code accidentally runs | Medium | High | Pre-flight grep check, adapter validation |
| Paper test doesn't find issues | Medium | Medium | Long 72h test, $100 live micro-test |

---

## 📊 COST-BENEFIT ANALYSIS

### Cost of Delay (Waiting to Deploy)
- **Opportunity Cost:** ~$500/day (based on MEXC Grid Bot performance)
- **4-Week Delay Cost:** ~$14,000 in foregone profits
- **BUT:** Risk of deploying broken architecture: **-$5,000+** (potential loss)

**Verdict:** 4 weeks to do it right < risk of doing it wrong

---

### Cost of Wrong Exchange (MEXC vs Binance)
If we accidentally deployed MEXC-configured bot thinking it was Binance:
- Order routing errors
- Wrong fee calculations
- API key mismatches
- Database contamination

**Prevented by:** Adapter pattern + pre-flight checks

---

## 📄 APPENDIX

### A. Binance API Key Setup
```bash
# Generate API key at:
https://www.binance.com/en/my/settings/api-management

# Restrictions:
✅ Enable Spot & Margin Trading
❌ Disable Withdrawals
✅ Enable Reading
✅ IP Whitelist: <your VPS IP>

# Set environment variables:
export BINANCE_API_KEY="your_key_here"
export BINANCE_SECRET_KEY="your_secret_here"
```

---

### B. LUNO API Key Setup
```bash
# Generate API key at:
https://www.luno.com/wallet/security/api_keys

# Permissions:
✅ View Balances
✅ View Transactions
❌ Trading (not needed)
❌ Withdrawals (not needed)

# Set environment variables:
export LUNO_API_KEY_ID="your_key_id"
export LUNO_API_KEY_SECRET="your_secret"
```

---

### C. Database Schema Changes
```sql
-- Add exchange column to all tables
ALTER TABLE trades ADD COLUMN exchange VARCHAR(20) DEFAULT 'Binance';
ALTER TABLE positions ADD COLUMN exchange VARCHAR(20) DEFAULT 'Binance';
ALTER TABLE bot_status ADD COLUMN exchange VARCHAR(20) DEFAULT 'Binance';

-- Create indexes
CREATE INDEX idx_trades_exchange ON trades(exchange);
CREATE INDEX idx_positions_exchange ON positions(exchange);
```

---

### D. Pre-Flight Check Template
```bash
#!/bin/bash
# scripts/pre_flight_check.sh

echo "🔍 PRE-FLIGHT CHECK"
echo "=================="

# Check 1: No hardcoded MEXC
if grep -r "exchange.*=.*'MEXC'" --include="*.py" core/ run_bot.py; then
    echo "❌ FAIL: Hardcoded MEXC found"
    exit 1
fi

# Check 2: Adapter pattern exists
if [ ! -f "core/adapters/binance_adapter.py" ]; then
    echo "❌ FAIL: Binance adapter not found"
    exit 1
fi

# Check 3: Environment variables
if [ -z "$BINANCE_API_KEY" ]; then
    echo "❌ FAIL: BINANCE_API_KEY not set"
    exit 1
fi

# Check 4: Database directories
if [ ! -d "data/binance" ]; then
    echo "❌ FAIL: data/binance/ not found"
    exit 1
fi

echo "✅ ALL CHECKS PASSED"
exit 0
```

---

## 🎯 FINAL RECOMMENDATION

**SENIOR ARCHITECT VERDICT:**

### Do NOT Restart Bots Until:
1. ✅ Adapter pattern implemented (P0-1)
2. ✅ Database separated (P0-2)
3. ✅ Kill switches added (P0-3)
4. ✅ Pre-flight check passes (P0-5)

### Timeline to Live Trading:
- **Week 1:** Foundation (adapters, database)
- **Week 2:** Safety (kill switches, monitoring)
- **Week 3:** Validation (paper trading)
- **Week 4:** Live deployment ($100 test → full capital)

### Priority Order:
1. 🥇 **Binance** - Primary trading exchange
2. 🥈 **LUNO** - Monitoring only (no trading)
3. 🥉 **MEXC** - Deferred (optional future addition)

### Risk Assessment:
- **Current State:** 🔴 HIGH RISK (hardcoded MEXC, no safeguards)
- **After Week 1:** 🟡 MEDIUM RISK (architecture fixed, no validation)
- **After Week 3:** 🟢 LOW RISK (validated, safe to deploy)

---

## ✅ APPROVAL REQUIRED

**Please confirm:**
- [ ] I approve the Binance-first approach
- [ ] I approve the 4-week timeline
- [ ] I approve MEXC exclusion
- [ ] I approve LUNO monitoring-only
- [ ] I'm ready to start P0-1 (Adapter Pattern)

**Once approved, we begin implementation immediately.**

---

**Document Version:** 1.0
**Last Updated:** January 8, 2026
**Status:** Awaiting Approval
**Next Review:** After Week 1 completion
