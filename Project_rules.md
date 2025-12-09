# Project Rules & Guidelines: Antigravity Crypto Automation System (ACAS)

**Project Name:** Lumina
**Codename:** Antigravity
**Version:** 2.1
**Source of Truth:** This document governs all development, product decisions, and AI-generated code.

---

## 1. Core Philosophy (The "North Star")

**Mission:** Build a secure, production-grade AI crypto trading platform that is safe and intuitive for non-technical users.
**The "Grandma Rule":** If a feature requires technical knowledge to configure, it is rejected. Complexity must be abstracted away.
**Litmus Test:** *"If your actual grandma lost $10,000 using this bot, could you sleep at night knowing you built in every reasonable safeguard?"*

---

## 2. Code Style & Standards (Python)

All contributors (including AI Agents) must strictly adhere to these standards to ensure stability.

### 2.1 Formatting & Syntax
* **PEP 8 Compliance:** Strictly follow PEP 8.
* **Type Hinting:** Mandatory for ALL function arguments and return values.
* **Imports:** Group standard library → third-party → local application. No wildcard imports.

### 2.2 Financial Logic (CRITICAL)
* **No Floating Point Math:** Never use python `float` for price or currency calculations.
* **Decimal Usage:** ALWAYS use `decimal.Decimal` for financial values.
* **Rounding:** Explicitly define rounding strategies (e.g., `ROUND_DOWN` for sell orders).

### 2.3 Execution Standards (New)
* **Slippage Tolerance:** Max 0.5% deviation from expected price.
* **Order Types:** Limit orders are default. Market orders only for emergencies/exits.
* **Fill-or-Kill:** Cancel orders unfilled after 120s.
* **Smart Routing:** Check order book depth before placing large orders.

### 2.4 Documentation & Naming
* **Docstrings:** Google Style. Must include `Args`, `Returns`, and `Raises`.
* **User-Facing Variables:** Map to simple UI terms (e.g., `risk_tolerance` not `sigma`).

### 2.5 Error Handling
* **No Silent Failures:** Every interruption is logged.
* **Contextual Logging:** Logs must explain the "Why" in human-readable format.

---

## 3. Product & Architecture Requirements

### 3.1 Security & Data
* **Zero-Trust Secrets:** API Keys are encrypted at rest and in transit.
* **No PII Logging:** Never log API keys, user passwords, or seed phrases.
* **Wallet Isolation:** Each coin has a distinct "Smart Wallet" abstraction.

### 3.2 User Experience (UX) Standards
* **Natural Language First:** Dashboard must explain actions in plain English.
* **Guided Setup:** Configuration must be wizard-style.
* **User Education:**
    * **Risk Quiz:** Mandatory risk assessment before trading.
    * **Loss Scenarios:** Simulate "What if market drops 30%?"
    * **Glossary:** Inline definitions for all financial terms.

### 3.3 Bot Logic & Safety
* **Kill Switch:** Master "Stop All" button at architecture level.
* **Dry-Run Default:** All new strategies default to "Paper Trading".
* **Risk Management (Expanded):**
    * **Position Sizing:** Max 2% (configurable 1-5%) of portfolio per trade.
    * **Daily Loss Limit:** Auto-pause all bots if portfolio drops X% in 24h.
    * **Correlation Check:** Prevent opening >3 correlated positions.
    * **Volatility Scaling:** Reduce position sizes by 50% if VIX > 90th percentile.

### 3.4 Operational Resilience (New)
* **Heartbeat Monitoring:** Ping exchange every 30s.
* **Stale Data Detection:** Flag and block trading if prices > 10s old.
* **Partial Fills:** If <50% filled after 60s → Cancel. If >50% → Allow completion.
* **Balance Reconciliation:** Verify local vs exchange balance every 5 minutes.

### 3.5 Strategy Lifecycle (New)
* **Validation Pipeline:**
    1. Backtest (3+ years data).
    2. Walk-forward analysis.
    3. Monte Carlo simulation (1000+ iterations).
    4. Paper Trading (30 days).
    5. Live Trading (10% capital, 7 days).
* **Diversity:** Min 3 uncorrelated strategies. No strategy > 40% capital.

### 3.6 System Health & Monitoring (New)
* **Metrics:** Orders/min, Avg latency, Error rate.
* **Alerting:** SMS/Email if portfolio drops > 5% in 1 hour.

---

## 4. Git Workflow & Version Control

### 4.1 Branching Strategy
* `main`: Stable, production-ready.
* `develop`: Integration branch.
* `feature/name`: New features.
* `fix/name`: Bug fixes.

### 4.2 Commit Messages
* Imperative mood, Semantic tagging (`[Feat]`, `[Fix]`, `[Sec]`).

### 4.3 Deployment Strategy (New)
* **Blue-Green:** Run old + new versions in parallel during updates.
* **Canary:** Deploy to small subset first (if applicable).
* **Automated Rollback:** Revert if error rate > 2%.

---

## 5. Instructions for AI Assistant (Google Antigravity Tool)

1.  **Prioritize Safety:** Flag high-risk requests. Suggest safer alternatives.
2.  **Grandma Rule:** Translate technical terms to layperson terms.
3.  **Validate Inputs:** Generate strict validation logic.
4.  **Test Generation:** Always generate `pytest` cases for financial logic.
5.  **Agent Constraints (New):**
    *   **Prohibited:** Cannot modify core wallet code or API key handling without explicit override.
    *   **Audit:** Track all AI-generated code changes.

---

## 6. Legal & Compliance (New)

*   **Tax Reporting:** Support export to IRS Form 8949 format.
*   **Audit Trail:** Immutable logs of all trades.
*   **Jurisdiction:** Check user location for restricted coins.
*   **Disclaimer:** Clear "Not Financial Advice" labeling.
