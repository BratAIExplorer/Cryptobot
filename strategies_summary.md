# 🤖 Crypto Trading Bot: Strategy Optimization Summary (Phase 3.1)
*As of Dec 23, 2025*

This document outlines the optimized logic, new conditions, and expected behavior for the bot fleet following the Phase 2 overhaul.

---

## 🚀 Detailed Portfolio Configuration (Phase 2)

| Bot Strategy | 💰 Allocation | 🪙 Operating Coins | ⚙️ Key Conditions & Rules |
| :--- | :--- | :--- | :--- |
| **🛍️ Buy-The-Dip**<br>*(The Value Investor)* | **$800 per Coin**<br>($16,000 max) | **20 Coins:**<br>BTC, ETH, SOL, BNB, XRP, DOGE,<br>ADA, TRX, AVAX, SHIB, DOT, LINK,<br>BCH, NEAR, LTC, UNI, PEPE, APT,<br>ICP, ETC | **Entry:** Confluence Score ≥ 50<br>(RSI + Trend + Vol + News)<br>**Exit:** +5% / +7% / +10% (Tiered)<br>**Stop Loss:** ❌ DISABLED (Infinite Hold)<br>**Alerts:** Days 100, 125, 150, 200 |
| **⚡ Hyper-Scalper**<br>*(Cash Flow)* | **🛑 DEACTIVATED** | BTC, ETH, SOL, XRP | **Status:** OFF per Senior Trader review (Negative PnL after Fees).<br>Left in code for future optimization. |
| **📈 SMA Trend**<br>*(Wealth Builder)* | **$800 per Coin**<br>($4,000 max) | **5 Coins:**<br>DOGE, XRP, DOT, ATOM, ADA | **Entry:** SMA 20 > SMA 50 (Daily)<br>**Confirm:** Price > SMA 200<br>**Exit:** Death Cross (SMA 20 < 50)<br>**Timeframe:** Daily Candles |
| **🤖 Grid Bots**<br>*(Sideways Income)* | **$1,000 BTC**<br>**$1,000 ETH** | **BTC/USDT** ($50/grid)<br>**ETH/USDT** ($30/grid) | **BTC Range:** $88k - $108k (20 Grids)<br>**ETH Range:** $2,800 - $3,500 (30 Grids)<br>**Logic:** Buy Low / Sell High within range |
| **💎 Hidden Gem**<br>*(Paper Scout)* | **$100 per Coin**<br>(Scanning) | **Top 50 Riskier Alts:**<br>UNI, MANA, SAND, AAVE, etc. | **Logic:** Dip Buying on Volatile Assets<br>**Risk:** Minimal (Paper Trading Mode) |

---

## 🚀 Strategy Optimization Matrix (Logic Changes)

| Strategy | ⚙️ New Logic vs Old Logic | 🎯 Expected Behavior | ⚠️ User Action Required |
| :--- | :--- | :--- | :--- |
| **🛍️ Buy-The-Dip** | **New:** Confluence (Tech+Trend+Vol) + Infinite Hold<br>**Old:** Blind 5% Drop + Stop Loss | • **Fewer Trades:** No buying during crashes.<br>• **Bag Holding:** Intended. Do not panic.<br>• **Higher Win Rate:** High conviction entries. | • **Monitor Alerts:** Check dashboard on 100-day alerts.<br>• **Toggle:** Enable `stop_loss_enabled` in config if needed. |
| **⚡ Hyper-Scalper** | **New:** Volume Filter (>1.3x) + Time Limit<br>**Old:** RSI only (caught noise) | • **Silence:** No trades in low volume.<br>• **Quality:** Fewer fake-outs.<br>• **Better R/R:** 1:3.5 ratio. | • **BNB Balance:** Keep topped up for gas fees. |
| **📈 SMA Trend Bot** | **New:** Daily Timeframe + Death Cross Exit<br>**Old:** 1H chart + 24h Time Limit | • **Rare Trades:** Silent for weeks.<br>• **Big Wins:** Catches full trends.<br>• **No Forced Exit:** Holds for months. | • **Patience:** Do NOT think it's broken if silent. |

---

## 📋 Comprehensive Strategy Details

### 1. 🛍️ Buy-the-Dip (Value Investor)
**Status:** 🟢 **Optimized (Phase 2)**
*   **Philosophy:** "Buy quality assets when they are oversold, hold until they recover."
*   **Old Logic:** Buy any 5% drop -> result: Bought falling knives.
*   **New Logic:** Buy 5% drop **ONLY IF** Long-term Trend is Up AND Volume is High.
*   **The "Infinite Hold" Rule:** We accept that some dips turn into bear markets. We do not sell at a loss. We wait.

### 2. ⚡ Hyper-Scalper (Cash Flow)
**Status:** 🔴 **DEACTIVATED**
*   **Reasoning:** High-frequency scalping incurred excessive fees on MEXC, resulting in negative net PnL during backtests.
*   **Action:** Logic remains in `engine.py` but is commented out in `run_bot.py`.

### 3. 📈 SMA Trend Bot (Wealth Builder)
**Status:** 🟢 **Optimized (Phase 2)**
*   **Philosophy:** "The trend is your friend. Ride it until it bends."
*   **Old Logic:** 1-Hour charts -> result: Whipsawed by daily noise.
*   **New Logic:** **Daily Charts**. We look for multi-week moves.
*   **Safety:** Death Cross exit protects from market crashes (e.g., May 2021).

---

## 📝 User Action Plan

1.  **Stop Loss Configuration:**
    *   Currently, Buy-The-Dip has **NO STOP LOSS**.
    *   To enable it: Open `run_bot.py`, find `Buy-the-Dip Strategy`, set `'stop_loss_enabled': True`.

2.  **Monitoring:**
    *   **Daily:** Check Dashboard for "Confluence Score" logs.
    *   **Weekly:** Check "Age Alerts" for old positions.

3.  **Deployment:**
    *   Run `deploy.sh` (or `git pull` on VPS) to activate these changes.
    *   Restart the bot: `python run_bot.py`.
