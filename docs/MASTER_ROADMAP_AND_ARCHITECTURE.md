# 📘 Master Project Documentation: Architecture & Roadmap

> **Status**: Assessment & Monitoring Phase
> **Current Phase**: Milestone 5 (VPS Deployment & Monitoring)
> **Version**: V3.1.0 (VPS Hardened)

---

## 🏗️ Architecture Overview

### Core Design: The Adapter Pattern
The system has moved from a monolithic `UnifiedExchange` to a modular **Adapter Pattern**.

*   **Goal**: Decoupling, Stability, and Strict Data Separation.
*   **Core Components**:
    *   **Interfaces**: `BaseExchangeAdapter` (Strict contract).
    *   **Adapters**: `MexcAdapter` (Legacy), `BinanceAdapter` (Production), `LunoAdapter` (Deprecated/Disabled).
    *   **Factory**: `ExchangeFactory` for instantiation.
    *   **Safety**: `ExchangeHealthMonitor` (Background latency & heartbeat checks).
    *   **Config**: `AdapterConfig` (Centralized, priority-based configuration).

### Data Architecture: Physical Separation
Databases are no longer shared. Data is isolated by exchange to prevent cross-contamination.
*   `data/trades_paper.db` (Unified V3 Paper DB)
*   `data/binance/trades.db` (Production Ready)

---

## 🗺️ Milestone Plan (6-Week Roadmap)

### ✅ Milestone 1: Core Foundation (Week 1)
*   [x] Implement `BaseExchangeAdapter`, `MexcAdapter`, `BinanceAdapter`.
*   [x] Implement `LunoAdapter`.
*   [x] Implement Physical Database Separation.
*   [x] Implement `ExchangeHealthMonitor` (Priority 1 Enhancement).
*   [x] Establish Git Strategy (Main Branch Swap).

### ✅ Milestone 2: Grid Bot Integration (Week 2)
*   [x] **Port Grid Strategy**: Move logic from `engine.py` to `strategies/grid_strategy.py`.
*   [x] **Enhance Strategy Base**: Ensure `BaseStrategyEnhanced` handles all safety checks.
*   [x] **Testing**: Verify Grid Bot works on Binance (Paper Mode).

### ✅ Milestone 3: Buy-the-Dip Migration (Week 3)
*   [x] **Port Dip Strategy**: Move logic to `strategies/dip_strategy_v3.py`.
*   [x] **Integrate Confluence**: connect V2 Confluence Engine to new Strategy class.
*   [x] **Testing**: Verify Dip Bot on multiple pairs.

### ✅ Milestone 4: Multi-Exchange Support (Week 4)
*   [x] **Multi-Adapter Engine**: Update Engine to hold multiple adapters simultaneously.
*   [x] **Routing Logic**: Strategy-to-Exchange routing.

### ✅ Milestone 5: VPS Deployment & Hardening (Week 5 - COMPLETED)
*   [x] **VPS Environment**: Python 3, venv, Git setup.
*   [x] **Deployment**: Successful clone and run on VPS.
*   [x] **Bug Fixes**:
    *   Fixed `BinanceAdapter` initialization race condition.
    *   Fixed `Analysis` script pathing.
    *   Removed `LUNO`/`MEXC` ghost logging.
*   [x] **Safety Gates**:
    *   Restricted to **Grid Bot** ($250/ea) and **Dip Bot** ($1000).
    *   Disabled experimental SMA/Momentum/Gem bots.

### 🔭 Milestone 6: Monitoring & Live Transition (Next Steps)
*   [ ] **Monitor Paper Trading** (24h period).
*   [ ] **Analyze Log Data**: Verify profits and strategy execution.
*   [ ] **Switch to Live**: Change `--mode paper` to `--mode live`.
*   [ ] **Capital Drift**: Implement equity erosion protection.

---

## 🛠️ Challenges & Fixes (Knowledge Base)

| Issue | Root Cause | Fix Applied |
| :--- | :--- | :--- |
| **"BinanceAdapter has no attribute exchange"** | Race condition in `__init__`. Base class called before specific init. | Reordered initialization: `self.exchange=None` before `super().__init__`. |
| **"Luno/MEXC warnings"** | Legacy code in `engine.py` checked all adapters. | Disabled `_check_luno` and changed default Resilience target to `'BINANCE'`. |
| **"90 Pairs Analyzed"** | Pillar C legacy watchlist injected extra pairs. | Disabled Component C for VPS V3 safety. |
| **"apt_pkg not found"** | User ran `analyze_trades.py` without `python3`. | Updated instructions to always use `python3 <script>`. |

---

## 🌟 Future Features
*   **Dashboard V3**: Multi-tab view for different exchanges.
*   **Telegram V2**: Interactive commands.
*   **Backtesting Engine**: Fast, local backtesting using stored DB data.

---

## 🔖 Strategies Configuration (VPS V3)

| Strategy | Status | Budget | Config |
| :--- | :--- | :--- | :--- |
| **Grid Bot (BTC)** | ✅ 100% Active | $250 | $25 Grids, Market Neutral |
| **Grid Bot (ETH)** | ✅ 100% Active | $250 | $25 Grids, Market Neutral |
| **Buy-the-Dip** | ✅ 100% Active | $1000 | Top 10 Coins, No Stop Loss |
| **SMA Trend** | 🛑 Disabled | - | Logic V2.0 (Pending) |
| **Momentum** | 🛑 Disabled | - | Logic V1.0 (Review) |
| **Hidden Gems** | 🛑 Disabled | - | High Risk (Disabled) |

---

## 📝 Change Log

### [2026-01-07] - V3.1.0 VPS Hardening
*   **Fix**: Critical race condition in Adapter base class.
*   **Fix**: Removed legacy exchange dependencies from Engine.
*   **Config**: Finalized VPS Budget ($1500 Total).
*   **Docs**: Updated Master Roadmap.

### [2026-01-06] - V3.0.0 Architecture Shift
*   **Refactor**: Replaced `UnifiedExchange` with `ExchangeFactory` + Adapters.
*   **Feat**: Added `ExchangeHealthMonitor`.

