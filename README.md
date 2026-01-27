# 🤖 Crypto Bot - Buy-the-Dip Portfolio

## Overview
This is a sophisticated algorithmic trading bot designed for "Buy-the-Dip" strategies. It manages a diverse portfolio of cryptocurrencies, automatically buying during market dips and holding positions indefinitely until profit targets are met ("Never Sell on Loss").

## Key Features
*   **Unified BTD Portfolio**: Operates 4 distinct "Buy-the-Dip" strategies across **12 major coins** (BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, LINK, AVAX, TRX).
*   **Diverse Strategy Tiers**:
    *   **Main BTD (3%)**: Captures small market corrections.
    *   **Conservative (5.2%)**: Buys on slightly deeper pullbacks.
    *   **Moderate (5.5%)**: Adds to positions during mid-sized dips.
    *   **Aggressive (8.0%)**: Capitalizes on significant market crashes.
*   **No Loss Selling**: Auto-cleanup logic is **disabled** for BTD strategies. Positions are held until the profit target (e.g., +8%) is reached, regardless of time.
*   **Accurate PnL Reporting**: Includes an advanced reporting tool (`check_pnl_v3.py`) that calculates **Realized Net Profit** by subtracting exchange fees (0.1%).
*   **Risk Management**: Dynamically monitors total portfolio health and prevents over-exposure.

## Deployment Guide (VPS)

### 1. Update Code
Pull the latest changes from the repository:
```bash
cd ~/cryptobot_v3
git pull
```

### 2. Restart Bot
Apply any configuration or code changes:
```bash
sudo systemctl restart cryptobot
```

### 3. Check Status
Verify the bot is running and see the total capital allocation:
```bash
tail -f logs/bot_engine.log
```

## Reporting

To check your portfolio performance and open positions:

```bash
python3 check_pnl_v3.py
```

This report will show:
*   **Realized PnL**: Actual profit banked (net of fees).
*   **Unrealized PnL**: Paper value of open positions.
*   **Open Positions**: List of current holdings and their individual performance.

## Strategy Configuration (Current)
*   **Total Capital**: $11,500
*   **BTD Capital**: $10,000 ($2,500 x 4 Strategies)
*   **Grid/Other Bots**: $1,500
*   **Fee Rate**: 0.1% (Factored into PnL)
