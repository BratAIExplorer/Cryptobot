# Implementation Plan - Confluence Score "Brain" Upgrade
> [!IMPORTANT]
> This upgrade changes the `Buy-the-Dip` from a naive "price drop" buyer to a sophisticated "sentiment-aware" investor.
> It requires the auto-running `NewsFilter` to be active.

# 1. Goal
Integrate the `ConfluenceEngine` into the main trading loop with a **Veto System**.
*   **Before:** Bot buys any coin that drops -5%.
*   **After:** Bot Checks 3 Veto Rules. If ANY are true -> **SKIP BUY**.

# 2. The Three Veto Rules (Validated)
1.  **BTC Crash Rule:** If BTC is down > 5% in 24h -> **VETO ALL ALTS**.
    *   *Why?* Historical data proves Alts have a beta > 1. When BTC sneezes, Alts catch a cold. We stand aside.
2.  **News Sentiment Rule:** If Critical News (SEC, Hack, Insolvency) is detected -> **VETO**.
    *   *Source:* CryptoPanic API (Top 5 highly voted news).
3.  **Falling Knife Rule:** If Price < SMA200 AND RSI > 30 (Not yet oversold enough) -> **VETO**.
    *   *Why?* Don't buy a downtrend until it's statistically "oversold".

# 3. New Components

### A. `core/brain.py` (The Veto Logic)
*   **Class:** `TradingBrain`
*   **Methods:**
    *   `check_veto(symbol, price_data)` -> Returns `(True/False, reason)`
    *   `get_news_sentiment()` -> Cached sentiment from API.
    *   `set_manual_override(symbol, status)` -> Allow user to FORCE BUY or FORCE BLOCK.

### B. `user_override.json` (User Request)
*   A simple JSON file where you can manually whitelist/blacklist coins.
    ```json
    {
      "FORCE_ALLOW": ["XRP", "DOGE"],
      "FORCE_BLOCK": ["LUNA", "FTT"]
    }
    ```

# 4. Alert System (User Request)
*   We will add a new Notification type: `ALERT_VETO`.
*   **Message:** "⚠️ VETO: Skipped buying XRP (-5% dip) because BTC is down -6%."

# 5. Implementation Steps
1.  Create `core/brain.py` with Veto Logic.
2.  Update `core/engine.py` to call `brain.check_veto()` before placing any Dip Buy.
3.  Create helper script `manage_overrides.py` to easily edit the JSON file.

# 6. Safety Validation
*   **Fallback:** If News API fails, we assume "Neutral" but still enforce the BTC Crash Rule (hard data).
