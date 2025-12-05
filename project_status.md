> Status: **Optimized & Enhanced (Grid Bot Added)**
> Last Updated: 2025-12-05

## 1. Project Overview & Objectives
**Purpose:**
To build a robust, automated crypto trading system capable of executing multiple strategies simultaneously on a VPS, with real-time monitoring via a web dashboard.

**End Goal:**
A "set-and-forget" passive income generator that:
- Runs 24/7 with 99.9% uptime.
- Protects capital via strict risk management (Circuit Breakers, Max Drawdown).
- Provides clear visibility into performance via a Streamlit dashboard.
- Notifies the user of critical events via Telegram.

**Key Requirements:**
- **Multi-Strategy Support:** Scalping, Trend Following, Dip Buying, **Grid Trading**.
- **Safety First:** Stop-losses, exposure limits, and crash recovery.
- **Transparency:** Full logging of every trade and decision.

---

## 2. Issues Identified & Fixes Implemented
### Recent Optimizations (Dec 5)
- **Expert Review Implementation:**
    - **Hyper-Scalper:** Relaxed RSI from 15 to **30** to increase trade frequency. Increased Profit Target to **1.2%** to safely cover fees.
    - **Infrastructure:** Fixed a critical bug in `logger.py` where Circuit Breaker methods were missing.
    - **Process Management:** Created PM2 configuration (`ecosystem.config.js`) for robust 24/7 operation.

### Previous Fixes
- **Circuit Breaker:** Added to pause trading after 10 consecutive errors.
- **Dashboard Sync:** Fixed P&L calculation discrepancies.
- **Streamlit Warnings:** Resolved deprecation warnings for `use_container_width`.
- **Split-Brain DB:** Resolved dual-database issue.

---

## 3. Prevention Measures & "Extra Mile"
To ensure the bot functions as expected moving forward:

**Implemented Safety Nets:**
- **Circuit Breaker:** Auto-pauses on errors, auto-recovers after 30 mins. **(Verified & Fixed)**
- **Watchdog:** Alerts if there are many buys with 0 sells (hoarding check).
- **Max Drawdown Protection:** Pauses trading if equity drops below a set threshold.
- **PM2 Process Manager:** Ensures the bot auto-restarts on crashes or server reboots.

---

## 4. Bot Strategies, Conditions & Parameters
The system currently supports the following active strategies:

### A. Hyper-Scalper Bot (Optimized)
*High-frequency trading aiming for small, quick profits.*
- **Buy Condition:** RSI (3-period) < **30** (Relaxed from 15).
- **Sell Condition:**
    - **Profit:** > 1.2% AND Position Age > 30 mins.
    - **Take Profit:** Fixed 1.2%.
    - **Stop Loss:** Fixed 2%.
- **Role:** Cash flow generator. High volume, low margin.

### B. Grid Bot (NEW!)
*Profits from sideways market volatility (buy low, sell high).*
- **Strategy:** `GridStrategyV2` (Stateful).
- **BTC Config:** Range +/- 10%, 20 Grids.
- **ETH Config:** Range +/- 10%, 30 Grids.
- **Role:** Consistent income in non-trending markets.

### C. Buy-the-Dip Strategy
*Accumulates blue-chip coins during market drops.*
- **Buy Condition:** Price drops **4-15%** from the 24-hour high.
- **Sell Condition:** Tiered Exits (50% @ +5%, 25% @ +7%, 25% @ +10%).
- **Role:** Long-term accumulation and swing trading.

### D. SMA Trend Bot
*Follows established market trends.*
- **Buy Condition:** SMA 20 crosses *above* SMA 50 (Golden Cross).
- **Sell Condition:** Trend reversal or standard TP/SL.
- **Role:** Capturing larger moves in trending markets.

### E. Hidden Gem Monitor (NEW!)
*Paper trading top 20 altcoins to find opportunities.*
- **Coins:** ADA, DOT, LINK, MATIC, UNI, etc.
- **Role:** Market research and data gathering.

---

## 5. Performance to Date
*As of Dec 5, 2025*

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Total Trades** | ~140 | Mostly Hyper-Scalper activity. |
| **Net P&L** | Flat / Slightly Negative | Impacted by 48h downtime and unrealized losses in "Dip" positions. |
| **Win Rate** | N/A | Insufficient closed trades to calculate reliable win rate yet. |
| **Uptime** | **Healthy** | Downtime resolved. Bot is running and trading. |

**Current Holdings:**
- **Bag:** XRP, UNI, BTC, NEAR, PEPE (from Buy-the-Dip).
- **Status:** Waiting for market recovery to hit sell targets.

---

## 6. Expert Recommendations & Next Steps

### A. Immediate Actions
> [!IMPORTANT]
> **Deploy Updates:** Push the new `run_bot.py`, `logger.py`, and `strategies/` to the VPS.
> **Install PM2:** Run `npm install pm2 -g` on the VPS to enable the new process manager.

### B. Monitoring
> [!TIP]
> **Watch the Grid:** Monitor the new Grid Bots for the first 48 hours. Ensure they are placing orders correctly within the defined ranges.
> **Scalper Volume:** Expect a significant increase in trade volume with the new RSI 30 setting. Ensure you have enough BNB for fees.
