# Week 1: Architecture Refactor Plan

## Goal Description
Implement critical architectural improvements recommended by the Senior Architect to prevent cross-exchange order errors, ensure data integrity, and add safety kill switches. This is a "Week 1" Blocking Task before any live deployment.

## User Review Required
> [!IMPORTANT]
> **Blocking Change**: This refactor will temporarily break the bot until all components are updated to use the new `BaseExchangeAdapter`.
> **Database Migration**: Current databases will be moved to `data/binance/` and `data/mexc/`. Old `trades.db` in root will be archived.

## Proposed Changes

### Core Architecture: Adapter Pattern
Refactor the brittle `UnifiedExchange` into a proper Interface + Adapter pattern.

#### [NEW] [base_adapter.py](file:///c:/CryptoBot_Project/core/interfaces/base_adapter.py)
- Define `BaseExchangeAdapter` abstract base class.
- Enforce methods: `create_order`, `get_balance`, `fetch_ohlcv`, `shutdown`.
- Enforce attributes: `kill_switch_active` (bool).

#### [NEW] [binance_adapter.py](file:///c:/CryptoBot_Project/core/exchanges/binance_adapter.py)
- Implementation of `BaseExchangeAdapter` for Binance.
- Encapsulate `ccxt.binance` logic.
- Implement per-exchange Kill Switch.

#### [NEW] [mexc_adapter.py](file:///c:/CryptoBot_Project/core/exchanges/mexc_adapter.py)
- Port logic from `core/exchange_mexc.py` to this new adapter.
- Implement per-exchange Kill Switch.

#### [NEW] [luno_adapter.py](file:///c:/CryptoBot_Project/core/exchanges/luno_adapter.py)
- Wrap Luno logic.

#### [MODIFY] [engine.py](file:///c:/CryptoBot_Project/core/engine.py)
- Update `TradingEngine` to instantiate specific adapters based on configuration.
- Remove dependence on `UnifiedExchange`.
- Implement `ExchangeFactory` pattern to select adapter.

### Safety: Kill Switches
#### [MODIFY] [core/engine.py](file:///c:/CryptoBot_Project/core/engine.py)
- Add `check_exchange_health()` method calling the adapter's health check.
- If health check fails (latency > 2s), trigger `adapter.shutdown()` and stop trading for that exchange.

### Data: Physical Separation
#### [NEW] `data/binance/`, `data/mexc/`, `data/luno/`
- Create directories.

#### [MODIFY] [logger.py](file:///c:/CryptoBot_Project/core/logger.py)
- Update `TradeLogger` to accept a `db_path` that defaults to the correct exchange folder.
- `get_db_path(exchange_name) -> path` helper.

## Verification Plan

### Automated Tests
1.  **Unit Tests for Adapters**: Create `tests/test_adapters.py` to verify:
    *   `MexcAdapter` creates proper order payload.
    *   `MexcAdapter.shutdown` stops subsequent orders.
    *   `ExchangeFactory` returns correct class.
    *   *Command*: `pytest tests/test_adapters.py`
2.  **Integration Test**: Update `tests/test_execution.py` to use `MexcAdapter` (mocked) instead of `UnifiedExchange`.
    *   *Command*: `pytest tests/test_execution.py`

### Manual Verification
1.  **Database Check**: Run script to verify DBs created in new folders.
    *   *Command*: `python scripts/verify_db_structure.py` (to be created)
2.  **Dry Run**: Run `python run_bot.py --mode paper` and verify logs show "Using MexcAdapter" and write to `data/mexc/trades.db`.
