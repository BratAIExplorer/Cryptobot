# 🤖 AI Handover: CryptoBot V3 Project Status

> **Date**: 2026-01-08  
> **Target**: AI Agent / Developer Handover  
> **Status**: VPS Deployed (Paper Mode)

---

## 🏗️ Architecture & Context

### 1. Core Architecture (Adapter Pattern)
The project has been refactored from a monolithic `UnifiedExchange` to a modular **Adapter Pattern**.
- **Adapters**: `BinanceAdapter` (Primary), `MexcAdapter` (Legacy/Inactive), `LunoAdapter` (Secondary/MYR focus).
- **Interface**: `BaseExchangeAdapter` defines the strict contract for all exchange interactions.
- **Factory**: `ExchangeFactory` handles instantiation.
- **Observability**: `ExchangeHealthMonitor` runs background heartbeats for latency and connectivity.

### 2. Strategy Routing (Engine V3)
`TradingEngine` now handles multiple bots with specific exchange routing.
- **Grid Bots (BTC/ETH)**: Routed to Binance. Budget $250 each.
- **Buy-the-Dip Strategy**: Routed to Binance. Budget $1000.
- **Other Bots**: SMA, Momentum, and Hidden Gems are currently **DISABLED** for stability.

---

## 🚀 Current Project State: VPS Deployment

### Environment Details
- **VPS Host**: `srv1010193` (`ssh root@72.60.40.29`)
- **Deployment Path**: `~/cryptobot_v3`
- **Python**: 3.10+ (Use `python3` explicitly).
- **Control**: Running via foreground terminal (consider `screen` or `pm2` for long-term).

### Database Configuration
- **Path**: `data/trades_paper.db` (Unified V3 Paper DB).
- **Separation**: Data is isolated by exchange adapter where necessary, but the primary paper trading log is centralized for the dashboard.

---

## ✅ Completed Tasks (Completed Jan 2026)
1. **Adapter Refactor**: Decoupled CCXT logic from strategy logic.
2. **VPS Launch**: Successfully deployed V3 code to remote server.
3. **Critical Bug Fixes**:
    - **Race Condition**: `BinanceAdapter` had an `AttributeError` because `super().__init__` called the health monitor before `self.exchange` was ready. Fixed by reordering and adding safety checks.
    - **Legacy Noise**: Removed Luno/MEXC ghost warnings and Pillar C correlation matrix overhead (90 pairs).
    - **Command Handler**: Accounted for broken `apt_pkg` on Ubuntu causing `analyze_trades.py` to fail if not run with `python3`.

---

## ⏳ Pending Technical Backlog

### Phase 1: Monitoring & Validation (Current Priority)
- [ ] **Observe Logs**: Bot has been running for ~24-48h. Verify first trades have occurred.
- [ ] **Profit Validation**: Run `python3 analyze_trades.py` on VPS to confirm net profit accounts for fees correctly.
- [ ] **Go/No-Go Decision**: Evaluate transition to `--mode live`.

### Phase 2: Unified Command Center (Milestone 7)
- [ ] **Multi-Page Streamlit**: Consolidate `dashboard/app.py`, `intelligence/dashboard_intelligence.py`, and `luno-monitor` into one interface.
- [ ] **Luno Intelligence**: Integrate the `RegulatoryScorer` into the Luno view.
- [ ] **Dashboard Logic**: Implement a `ContextManager` to switch between Live/Paper data sources seamlessly.

### Phase 3: Risk & Safety
- [ ] **Capital Drift Protection**: Implement logic to halt bot if account equity drops below a specific % of starting capital.
- [ ] **Unified Alerts**: Consolidate Telegram notifications for all bots.

---

## 🧠 Intelligence Routing Map
The system uses `MasterDecisionEngine` to route assets based on classification:
- **Technical/Trend**: Routed to `ConfluenceFilter` (RSI, MA, Sentiment).
- **Fundamental/Regulatory**: Routed to `RegulatoryScorer` (ETF flows, SEC status, Institutional adoption).
- **Use Case**: Grid/Dip bots use Technical. Long-term Luno holds should use Regulatory.

---

## 🔧 Debugging Tips for AI Agents
1. **Always use `python3`**: The VPS `CommandNotFound` handler is broken; running `.py` files directly results in `ModuleNotFoundError: No module named 'apt_pkg'`.
2. **Race Conditions**: Be careful when adding logic to `BaseExchangeAdapter.__init__`. Child adapters MUST initialize their CCXT objects before health monitors start polling.
3. **Environment**: `load_dotenv()` is critical in all entry points (`run_bot.py`, `go_no_go.py`).
4. **Resilience**: The `ExchangeResilienceManager` defaults to "BINANCE" now to avoid legacy MEXC messages.

---

## 📖 Key Documentation
- `docs/MASTER_ROADMAP_AND_ARCHITECTURE.md`: Technical benchmarks.
- `docs/PRODUCT_STRATEGY_2026.md`: UX and product-level vision.
- `docs/VPS_DEPLOYMENT_GUIDE_V3.md`: Step-by-step update process.

---

## 🔄 CURRENT SESSION (2026-01-15)

### Session Context
**Branch**: `claude/check-dashboard-status-VNa0U`
**Previous Branch**: `claude/priority1-enhancements-lXrIG` (8 commits unpushed due to HTTP 403)
**User Role**: Senior Product & Crypto Specialist & Senior Full Stack Lead

### Tasks In Progress

#### ✅ Completed This Session
- [x] Switched to correct branch `claude/check-dashboard-status-VNa0U`
- [x] Reviewed dashboard status (Running on port 8501)
- [x] Reviewed previous session context (8 commits stuck)

#### 🔄 Currently Working On

**Task 1: Update AI HANDOVER Document** ⏳ IN PROGRESS
- **File**: `docs/AI_HANDOVER.md`
- **Changes**: Adding session tracking section
- **Status**: Writing now

**Task 2: Check BOT Performance** ⏳ PENDING
- **Files to Check**:
  - `data/trades_v3.db` or `data/trades_paper.db` (database queries)
  - Log files (location TBD - need to find on VPS)
  - `core/engine.py` (check if running)
- **Queries**: Position count, win rate, P&L, error logs
- **Expected Path**: `/home/user/Cryptobot` OR `/root/cryptobot_v3` (verify)

**Task 3: Fix HTTP 403 Git Error** ⏳ PENDING
- **Issue**: 8 commits on branch `claude/priority1-enhancements-lXrIG` cannot push
- **Files Involved**: Git configuration
- **Solutions to Try**:
  1. Use GitHub Personal Access Token
  2. Configure SSH keys
  3. Direct HTTPS authentication
- **Reference**: `FIX_GIT_403_ERROR.md` (exists on other branch)

**Task 4: Push Pending Commits** ⏳ PENDING
- **Branch**: `claude/priority1-enhancements-lXrIG`
- **Commits**: 8 total (including critical adapter fix)
- **Prerequisite**: Task 3 must complete first
- **Files in Commits**:
  - `core/engine.py` (CRITICAL: adapter method fix)
  - `docs/MASTER_REFERENCE.md`
  - `docs/AI_HANDOVER_STATUS.md`
  - `docs/CODE_MANAGEMENT_GUIDE.md`
  - `FIX_GIT_403_ERROR.md`
  - `apply_adapter_fix.sh`
  - `adapter_fix.patch`

**Task 5: Deploy Critical Bug Fix to VPS** ⏳ PENDING
- **File**: `core/engine.py` lines 1295-1310
- **Bug**: Using `fetch_balance()` instead of `get_balance('USDT')`
- **VPS Path**: `/root/cryptobot_v3/core/engine.py` OR `/home/user/Cryptobot/core/engine.py`
- **Method**: Manual edit OR pull after push succeeds OR use patch file
- **Critical**: Do NOT restart if paper test still running

**Task 6: Verify Deployment** ⏳ PENDING
- **Checks**:
  - Portfolio snapshots no longer error
  - Log shows `get_balance('USDT')` working
  - No `AttributeError: 'BinanceAdapter' object has no attribute 'fetch_balance'`
- **Files to Monitor**:
  - Log file (path TBD)
  - Database health checks

**Task 7: Strategic Recommendations** ⏳ PENDING
- **Deliverable**: Next phase roadmap
- **Based on**: BOT performance results from Task 2

### Path Clarification Needed
**QUESTION**: Which VPS path are we using?
- Previous session mentioned: `/root/cryptobot_v3`
- Current dashboard at: `/home/user/Cryptobot`
- **Action**: Verify during Task 2

### Files Modified This Session
1. `docs/AI_HANDOVER.md` - This file (adding session tracking)
2. (More to be added as tasks complete)

### Critical Notes
- ⚠️ Paper test may be running - do NOT interrupt until verification
- ⚠️ 8 commits contain critical bug fix for adapter pattern
- ⚠️ Dashboard is operational on port 8501
- ⚠️ User requires AI HANDOVER update BEFORE each task execution

---
**Last Updated**: 2026-01-15 (Current Session)
**End of Handover.**🤖
