# 🤖 Crypto Trading Bot: Strategy Summary & Recommendations
*As of Dec 9, 2025*

This document outlines the current logic, performance status, and expert recommendations for the active trading strategies.

---

## 1. 🤖 Hyper-Scalper Bot (The Cash Flow Output)
**Objective:** High-frequency trading to capture small, quick price movements.
**Status:** 🟢 **Active** | **Optimized Dec 9**

### ⚙️ Logic & Conditions
*   **Buy Condition:** RSI (3-period) < **30** (Oversold).
*   **Sell Condition (Win):** Profit > **3.5%** (Aggressive Target).
*   **Sell Condition (Loss):** Loss > **1.0%** (Tight Stop Loss).
*   **Time Limit:** Force exit after 30 minutes (keep capital moving).

### 📊 Performance
*   **Win Rate:** **54%** (Decent for scalping).
*   **Issue:** Previously losing more on bad trades (-$8.50) than gaining on good ones (+$4.88).
*   **Fix Applied:** Adjusted R/R ratio to 1:3.5 (Risk $1 to make $3.5).

### 🔮 Recommendations
*   **Monitor Win Rate:** The new tighter Stop Loss (1%) might lower the win rate. If it drops below 40%, we may need to loosen it slightly to 1.5%.
*   **Fee Awareness:** Ensure BNB balance is topped up, as this bot trades frequently.

---

## 2. 🛍️ Buy-the-Dip Strategy (The Value Investor)
**Objective:** Accumulate blue-chip assets at significant discounts.
**Status:** 🟠 **Holding Bags** | Active

### ⚙️ Logic & Conditions
*   **Buy Condition:** Price drops **4-15%** from the 24-hour high.
*   **Exit Strategy:** Tiered Sell (50% @ +5%, 25% @ +7%, 25% @ +10%).
*   **Stop Loss:** 30% (Wide berth for volatility).
*   **Time Limit:** 120 Days (Long-term hold).

### 📊 Performance
*   **Portfolio Coverage:** **80%** (16/20 coins bought).
*   **Missed Opportunities:** Has NOT yet bought **BTC, ETH, BNB, TRX** (likely because they haven't dipped enough).
*   **Current State:** Holding 16 positions mostly from Dec 2-5 drop.

### 🔮 Recommendations
*   **Trend Filter (Point 3):** To prevent catching "falling knives," we should only buy dips if the **Daily Trend** is still UP (e.g., Price > 200 SMA).
*   **Pause:** Temporarily pause new buys on "weak" coins until existing inventory clears.

---

## 3. 🤖 SMA Trend Bot (The Swing Trader)
**Objective:** Catch sustained market trends for large gains.
**Status:** 🟢 **Active**

### ⚙️ Logic & Conditions
*   **Buy Condition:** SMA 20 crosses *above* SMA 50 ("Golden Cross").
*   **Sell Condition:** SMA 20 crosses *below* SMA 50 OR Stop Loss/Take Profit.
*   **Take Profit:** 3% / **Stop Loss:** 5%.

### 📊 Performance
*   **Activity:** Low (1 active position).
*   **Context:** This is **good**. The market has been choppy/down. A trend bot *should* be inactive in these conditions.

### 🔮 Recommendations
*   **Patience:** Do not "force" this bot to trade. It is your safety valve. When the bull market returns, this bot will print money.

---

## 4. 🤖 Grid Bots (Side-ways Income)
**Objective:** Profit from market indecision (volatility without trend).
**Status:** 🟢 **Active (New)**

### ⚙️ Logic & Conditions
*   **BTC Grid:** Range $88k - $108k (20 Levels).
*   **ETH Grid:** Range $2,800 - $3,500 (30 Levels).
*   **Logic:** Buy Low, Sell High within these fixed ranges.

### 📊 Performance
*   **Early Results:** 3 Active positions. Small, consistent profits expected.

### 🔮 Recommendations
*   **Range Maintenance:** If BTC breaks $108k or drops below $88k, the grid must be reset/reconfigured.

---

## 5. 💎 Hidden Gem Monitor (The Scout)
**Objective:** "Paper Trade" risky altcoins to find the next 100x gem.
**Status:** 🟢 **Active**

### ⚙️ Logic & Conditions
*   **Strategy:** Buy-the-Dip logic on riskier assets (UNI, MANA, SAND, etc.).
*   **Risk:** Minimal ($100 allocation per trade).

### 📊 Performance
*   **Insight:** Currently holding UNI and MANA. Useful for sensing "Altseason" before it starts.

---

## 🚀 Summary of Next Steps
1.  **Deploy:** Push the new `run_bot.py` to VPS.
2.  **Verify:** Watch the Hyper-Scalper for 24 hours to ensure the new 3.5% target is hit.
3.  **Upgrade:** Begin work on **Confluence Engine** (Point 3) to give the bots a "Brain" to decide *when* to use which strategy.
