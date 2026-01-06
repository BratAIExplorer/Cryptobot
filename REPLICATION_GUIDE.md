# 🤖 CryptoBot Project - Replication Guide

This document provides all the necessary details to replicate, configure, and run the CryptoBot project.

## 1. Prerequisites

Before starting, ensure you have the following installed:

*   **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
*   **Git**: [Download Here](https://git-scm.com/downloads)
*   **Node.js & npm** (Optional, for PM2 process management): [Download Here](https://nodejs.org/)

## 2. Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd CryptoBot_Project
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## 3. Configuration

The bot relies on environment variables for API keys and settings.

1.  **Create a `.env` file** in the project root.
2.  **Add the following configuration:**

    ```ini
    # --- Exchange Credentials (MEXC) ---
    MEXC_API_KEY=your_mexc_api_key_here
    MEXC_SECRET_KEY=your_mexc_secret_key_here

    # --- Telegram Notifications (Optional but Recommended) ---
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_telegram_chat_id

    # --- Other Exchanges (Optional) ---
    # BINANCE_API_KEY=...
    # BINANCE_SECRET_KEY=...
    ```

## 4. Running the Bot

### A. Quick Start (Refined Parameters)
To run the latest version of the bot with the "Christmas Edition" refined parameters (Grid, Trend, Buy-the-Dip):

```bash
python run_bot.py
```

*   **Default Mode:** `paper` (Safe, simulated trading).
*   **To Go Live:** Edit `run_bot.py` and change `TRADING_MODE = 'live'`. **Warning: Real money will be used.**

### B. Dashboard (Streamlit)
To view the performance dashboard:

```bash
streamlit run intelligence/dashboard_intelligence.py
```
*   Access via browser at `http://localhost:8501`.

## 5. Project Structure

*   `run_bot.py`: Main entry point. Defines strategy allocations and starts the engine.
*   `core/`: Core trading engine, risk management, and exchange interface.
*   `strategies/`: Strategy logic (Grid, SMA, etc.).
*   `data/`: Database files (`.db`) and logs.
*   `Project_rules.md`: Detailed architecture and coding standards.

## 6. Troubleshooting

*   **Missing Dependencies:** Run `pip install -r requirements.txt` again.
*   **API Errors:** Check your `.env` file and ensure keys are correct and have "Spot Trading" permissions.
*   **Database Locked:** Ensure no other instance is running (check Task Manager).

---
*Generated for Antigravity Authentication & Replication*
