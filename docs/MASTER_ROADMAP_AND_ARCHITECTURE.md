# 📘 Master Project Documentation: Architecture & Roadmap

> **Status**: Active Development  
> **Current Phase**: Milestone 2 (Grid Bot Migration)  
> **Version**: V3.0.0 (Adapter Architecture)

---

## 🏗️ Architecture Overview

### Core Design: The Adapter Pattern
The system has moved from a monolithic `UnifiedExchange` to a modular **Adapter Pattern**.

*   **Goal**: Decoupling, Stability, and Strict Data Separation.
*   **Core Components**:
    *   **Interfaces**: `BaseExchangeAdapter` (Strict contract).
    *   **Adapters**: `MexcAdapter`, `BinanceAdapter`, `LunoAdapter`.
    *   **Factory**: `ExchangeFactory` for instantiation.
    *   **Safety**: `ExchangeHealthMonitor` (Background latency & heartbeat checks).
    *   **Config**: `AdapterConfig` (Centralized, priority-based configuration).

### Data Architecture: Physical Separation
Databases are no longer shared. Data is isolated by exchange to prevent cross-contamination.
*   `data/binance/trades.db`
*   `data/mexc/trades.db`
*   `data/luno/trades.db`

---

## 🗺️ Milestone Plan (6-Week Roadmap)

### ✅ Milestone 1: Core Foundation (Week 1)
*   [x] Implement `BaseExchangeAdapter`, `MexcAdapter`, `BinanceAdapter`.
*   [x] Implement `LunoAdapter`.
*   [x] Implement Physical Database Separation.
*   [x] Implement `ExchangeHealthMonitor` (Priority 1 Enhancement).
*   [x] Establish Git Strategy (Main Branch Swap).

### 🚧 Milestone 2: Grid Bot Integration (Week 2 - Current)
*   [ ] **Port Grid Strategy**: Move logic from `engine.py` to `strategies/grid_strategy.py`.
*   [ ] **Enhance Strategy Base**: Ensure `BaseStrategyEnhanced` handles all safety checks.
*   [ ] **Testing**: Verify Grid Bot works on Binance (Paper Mode).
*   [ ] **Cleanup**: Remove legacy grid logic from `engine.py`.

### 📅 Milestone 3: Buy-the-Dip Migration (Week 3)
*   [ ] **Port Dip Strategy**: Move logic to `strategies/dip_strategy.py`.
*   [ ] **Integrate Confluence**: connect V2 Confluence Engine to new Strategy class.
*   [ ] **Testing**: Verify Dip Bot on multiple pairs.

### 📅 Milestone 4: Multi-Exchange Support (Week 4)
*   [ ] **Multi-Adapter Engine**: Update Engine to hold multiple adapters simultaneously.
*   [ ] **Routing Logic**: Strategy-to-Exchange routing (e.g., Grid on Binance, Dip on Luno).

### 📅 Milestone 5: Production Hardening (Week 5)
*   [ ] **Go/No-Go Validator**: Deployment pre-flight checks.
*   [ ] **Security Audit**: API key handling review.
*   [ ] **Drift Protection**: Capital erosion monitoring.

---

## 🔖 Versioning Strategy

We follow **Semantic Versioning** (MAJOR.MINOR.PATCH).

| Component | Current Version | Notes |
| :--- | :--- | :--- |
| **Adapter Layer** | `1.1.0` | Initial Release + Health Monitor |
| **Grid Bot** | `2.0.0` | **Pending** (Migration to V3) |
| **Dip Bot** | `1.5.0` | Legacy Version (Pre-Migration) |
| **Core Engine** | `3.0.0` | Adapter-Based Architecture |

---

## 📝 Change Log

### [2026-01-06] - V3.0.0 Architecture Shift
*   **Refactor**: Replaced `UnifiedExchange` with `ExchangeFactory` + Adapters.
*   **Feat**: Added `ExchangeHealthMonitor` for background latency tracking.
*   **Feat**: Added `AdapterConfig` for centralized configuration.
*   **Git**: Promoted `feature/adapter-refactor` to `main`. Archived legacy code to `legacy_v2025`.
*   **Docs**: Created Master Documentation.

---

## 🛡️ Governance & Rules
1.  **Kill Switch**: If latency > 2000ms, NO NEW ORDERS.
2.  **No "God Classes"**: Logic must be separated (Strategy vs Execution vs Data).
3.  **Strict Typing**: All new interfaces must use Python type hints.
