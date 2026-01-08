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
**End of Handover.**🤖
