# Dashboard Architecture: PAPER vs LIVE Bots

## 🎯 Design Principles

1. **Isolation:** PAPER and LIVE data must be completely separated
2. **Clarity:** Visual indicators prevent confusion about trading mode
3. **Shared Intelligence:** Market analysis shared, execution separated
4. **Unified Monitoring:** Single dashboard shows both modes side-by-side

---

## 📊 Database Strategy

### Separate Databases by Mode & Exchange

```
data/
├── trades_binance_paper.db    # Binance testnet trades (fake money)
├── trades_binance_live.db     # Binance production trades (real money)
├── trades_mexc_live.db        # MEXC production trades (real money)
└── intelligence/              # Shared intelligence data
    ├── market_regime.db       # Market state (shared across all bots)
    ├── correlations.db        # Asset correlations (shared)
    ├── new_coins.db           # New coin detection (shared)
    └── fundamentals.db        # Fundamental analysis (shared)
```

**Key Separation:**
- ✅ **Trade Execution:** Completely isolated per mode/exchange
- ✅ **Capital Tracking:** Separate per mode/exchange
- ✅ **P&L Calculation:** Independent per mode/exchange
- ⚠️ **Intelligence:** Shared (uses real market data for all bots)

---

## 🧠 Intelligence Module Architecture

### Shared Components (Mode-Agnostic)

These analyze **real market data** and provide insights to all bots:

```python
class SharedIntelligence:
    """
    Intelligence modules that analyze real markets
    Recommendations apply to both PAPER and LIVE bots
    """

    # 1. Market Regime Detector
    regime_detector = RegimeDetector()
    # Input: Real BTC/USDT price data
    # Output: BULL/BEAR/SIDEWAYS + confidence
    # Used by: All bots (PAPER + LIVE)

    # 2. Correlation Manager
    correlation_manager = CorrelationManager()
    # Input: Real price data for all tracked assets
    # Output: Correlation matrix (diversification insights)
    # Used by: All bots to avoid over-concentration

    # 3. New Coin Detector
    new_coin_detector = NewCoinDetector()
    # Input: Exchange listings
    # Output: Newly listed coins with metadata
    # Used by: All bots for opportunity detection

    # 4. Fundamental Analyzer
    fundamental_analyzer = FundamentalAnalyzer()
    # Input: On-chain data, news, social sentiment
    # Output: Fundamental score (bullish/bearish)
    # Used by: All bots for veto decisions

    # 5. Veto Manager
    veto_manager = VetoManager()
    # Input: All intelligence signals
    # Output: GO/NO-GO for trades
    # Used by: All bots before executing
```

**Why Shared?**
- Markets are the same for everyone
- No point analyzing BTC trend separately for PAPER vs LIVE
- Insights apply equally to all trading modes
- Reduces computational overhead

### Mode-Specific Components

These respect mode boundaries:

```python
class ModeSpecificExecution:
    """
    Execution and capital management per mode
    NEVER mix PAPER and LIVE execution
    """

    # Separate per mode
    exchange_paper = UnifiedExchange('binance', mode='paper')
    exchange_live = UnifiedExchange('binance', mode='live')

    # Separate databases
    logger_paper = TradeLogger('data/trades_binance_paper.db')
    logger_live = TradeLogger('data/trades_binance_live.db')

    # Separate capital controllers
    capital_paper = CapitalController(logger_paper)
    capital_live = CapitalController(logger_live)

    # Separate notifiers (different prefixes)
    notifier_paper = LiveTradingNotifier(mode='paper')  # 📝 PAPER
    notifier_live = LiveTradingNotifier(mode='live')    # 🔴 LIVE
```

---

## 🎨 Dashboard Design

### Unified Dashboard with Mode Separation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🤖 CRYPTO TRADING DASHBOARD                       │
│                                                                       │
│  Mode Selector: [📝 PAPER] [🔴 LIVE] [👀 ALL]                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  📝 PAPER MODE (Binance Testnet - Fake Money)                       │
├─────────────────────────────────────────────────────────────────────┤
│  Capital: $140.00 allocated | $0.00 used | $140.00 available        │
│  Daily P&L: +$0.00 | Total P&L: +$0.00                              │
│                                                                       │
│  Active Bots:                                                        │
│  • Binance_Grid_BTC_Paper:    $80 | 0 trades | $0.00 P&L           │
│  • Binance_Grid_ETH_Paper:    $60 | 0 trades | $0.00 P&L           │
│                                                                       │
│  Recent Trades: (None)                                               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🔴 LIVE MODE (Binance Production - REAL MONEY)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Capital: $0.00 allocated | $0.00 used | $0.00 available            │
│  Daily P&L: $0.00 | Total P&L: $0.00                                │
│                                                                       │
│  Active Bots: (None)                                                 │
│                                                                       │
│  ⚠️ LIVE TRADING NOT STARTED - Using PAPER mode for testing         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🧠 SHARED INTELLIGENCE (Real Market Data)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Market Regime: BULL (Confidence: 73.5%)                            │
│  BTC Trend: Upward | ETH Trend: Upward                              │
│                                                                       │
│  Correlation Matrix:                                                 │
│  • BTC ↔ ETH: 0.85 (Highly Correlated)                             │
│  • BTC ↔ BNB: 0.72 (Correlated)                                    │
│                                                                       │
│  Fundamental Scores:                                                 │
│  • BTC: 78/100 (Bullish)                                            │
│  • ETH: 82/100 (Bullish)                                            │
│                                                                       │
│  New Coins Detected: (None in last 24h)                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ⚙️ SYSTEM HEALTH                                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Exchange Status: ✅ Connected (Latency: 45ms)                      │
│  Circuit Breaker: ✅ Normal (0 failures)                            │
│  Daily Loss Limit: ✅ OK ($0/$50 used)                              │
│  Last Update: 2026-01-06 05:45:32                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Implementation Architecture

### Dashboard Configuration

```python
class DashboardConfig:
    """
    Dashboard can monitor multiple modes simultaneously
    """

    MODES = {
        'paper': {
            'db_path': 'data/trades_binance_paper.db',
            'exchange': 'binance',
            'sandbox': True,
            'color': 'blue',
            'icon': '📝',
            'label': 'PAPER (Testnet)'
        },
        'live': {
            'db_path': 'data/trades_binance_live.db',
            'exchange': 'binance',
            'sandbox': False,
            'color': 'red',
            'icon': '🔴',
            'label': 'LIVE (Real Money)'
        }
    }

    # Shared intelligence (mode-agnostic)
    INTELLIGENCE_DB = 'data/intelligence/market_regime.db'
```

### Confluence Engine Integration

**The Confluence Engine provides holistic view across ALL bots:**

```python
class ConfluenceEngine:
    """
    Aggregates signals from multiple sources
    Provides unified trading signals to all bots
    """

    def __init__(self):
        # Shared intelligence modules
        self.regime_detector = RegimeDetector()
        self.correlation_manager = CorrelationManager()
        self.veto_manager = VetoManager()
        self.fundamental_analyzer = FundamentalAnalyzer()

        # Connect to all bot databases for trade history
        self.loggers = {
            'paper': TradeLogger('data/trades_binance_paper.db'),
            'live': TradeLogger('data/trades_binance_live.db'),
        }

    def get_confluence_signal(self, symbol, mode='paper'):
        """
        Generate trading signal considering:
        - Market regime (shared)
        - Correlations (shared)
        - Fundamentals (shared)
        - Historical performance (mode-specific)
        """

        # 1. Market Regime (SHARED)
        regime, confidence = self.regime_detector.detect_regime()

        # 2. Correlations (SHARED)
        correlation_risk = self.correlation_manager.check_concentration(symbol)

        # 3. Fundamentals (SHARED)
        fundamental_score = self.fundamental_analyzer.analyze(symbol)

        # 4. Historical Performance (MODE-SPECIFIC)
        logger = self.loggers[mode]
        win_rate = logger.get_win_rate(symbol)

        # 5. Veto Check (SHARED intelligence, mode-specific execution)
        veto_result = self.veto_manager.check_veto(symbol, mode)

        # Aggregate signals
        confluence_score = self._calculate_confluence(
            regime, correlation_risk, fundamental_score,
            win_rate, veto_result
        )

        return {
            'signal': 'BUY' if confluence_score > 70 else 'WAIT',
            'confidence': confluence_score,
            'components': {
                'regime': regime,
                'correlation': correlation_risk,
                'fundamentals': fundamental_score,
                'win_rate': win_rate,
                'veto': veto_result
            }
        }
```

**Key Point:** Confluence uses shared intelligence but respects mode boundaries for execution and historical data.

---

## 📱 Monitoring Strategy

### Option 1: Unified Dashboard (Recommended)

**One dashboard, multiple tabs:**

```
Dashboard URL: http://localhost:8501

Tabs:
├── Overview (All Modes)
├── 📝 PAPER Mode Details
├── 🔴 LIVE Mode Details
├── 🧠 Intelligence
└── ⚙️ System Health
```

**Advantages:**
- Single point of monitoring
- Easy comparison between modes
- Shared intelligence visible
- Context switching minimal

**Implementation:**
```python
# streamlit_dashboard.py
import streamlit as st

mode = st.sidebar.selectbox("Mode", ["All", "PAPER", "LIVE"])

if mode == "All":
    show_unified_view()
elif mode == "PAPER":
    show_paper_dashboard()
else:
    show_live_dashboard()
```

### Option 2: Separate Dashboards

**Run two instances:**
```bash
# PAPER dashboard on port 8501
streamlit run dashboard.py --server.port 8501 -- --mode paper

# LIVE dashboard on port 8502
streamlit run dashboard.py --server.port 8502 -- --mode live
```

**Advantages:**
- Complete isolation
- No accidental mode mixing
- Can run on different servers

**Disadvantages:**
- Need to monitor two URLs
- Harder to compare modes
- Duplicate intelligence display

**My Recommendation:** **Option 1 (Unified Dashboard)** with clear visual separation.

---

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REAL MARKET DATA                             │
│              (Binance, CoinGecko, On-chain, News)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SHARED INTELLIGENCE LAYER                           │
│  • Market Regime Detector                                        │
│  • Correlation Manager                                           │
│  • Fundamental Analyzer                                          │
│  • New Coin Detector                                             │
│  • Veto Manager                                                  │
└──────────────┬──────────────────────┬────────────────────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────┐   ┌──────────────────────┐
│   PAPER MODE BOTS    │   │   LIVE MODE BOTS     │
│   (Testnet)          │   │   (Production)       │
├──────────────────────┤   ├──────────────────────┤
│ • Grid BTC (Paper)   │   │ • Grid BTC (Live)    │
│ • Grid ETH (Paper)   │   │ • Grid ETH (Live)    │
│ • BuyDip BTC (Paper) │   │ • BuyDip BTC (Live)  │
└──────────┬───────────┘   └───────────┬──────────┘
           │                           │
           ▼                           ▼
┌──────────────────────┐   ┌──────────────────────┐
│ trades_binance_paper │   │ trades_binance_live  │
│        .db           │   │        .db           │
└──────────┬───────────┘   └───────────┬──────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
            ┌──────────────────────┐
            │   UNIFIED DASHBOARD   │
            │                       │
            │ • PAPER tab           │
            │ • LIVE tab            │
            │ • Intelligence tab    │
            └───────────────────────┘
```

---

## 🚀 Implementation Checklist

### Phase 1: Database Separation
- [x] PAPER database: `data/trades_binance_paper.db`
- [ ] LIVE database: `data/trades_binance_live.db` (when ready for live)
- [ ] Intelligence database: `data/intelligence/`

### Phase 2: Dashboard Updates
- [ ] Add mode selector to dashboard
- [ ] Create PAPER mode tab
- [ ] Create LIVE mode tab (placeholder)
- [ ] Create Intelligence tab
- [ ] Add visual mode indicators

### Phase 3: Confluence Integration
- [ ] Connect Confluence to both databases
- [ ] Mode-aware signal generation
- [ ] Historical performance per mode

### Phase 4: Testing
- [ ] Test PAPER mode monitoring
- [ ] Verify data isolation
- [ ] Test mode switching
- [ ] Validate intelligence sharing

---

## 💡 Key Takeaways

1. **Data Isolation:** PAPER and LIVE never mix execution data
2. **Intelligence Sharing:** Market analysis shared across all bots
3. **Unified Monitoring:** Single dashboard, multiple views
4. **Clear Indicators:** Visual separation prevents confusion
5. **Scalable:** Architecture supports multiple exchanges/modes

**Your Phase 3 Paper Testing can run alongside future LIVE bots on the same dashboard without any risk of confusion or data mixing.**

Ready to implement? 🚀
