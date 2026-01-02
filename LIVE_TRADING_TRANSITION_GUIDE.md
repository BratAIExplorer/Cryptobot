# 🚀 Live Trading Transition Guide

**⚠️ CRITICAL:** This guide covers transitioning from paper trading to live trading with real money. Follow ALL safety steps.

---

## 📋 Table of Contents

1. [Pre-Live Checklist](#pre-live-checklist)
2. [Paper vs Live Separation](#paper-vs-live-separation)
3. [Telegram Alert Configuration](#telegram-alert-configuration)
4. [Live Trading Safety Mechanisms](#live-trading-safety-mechanisms)
5. [Monitoring Dashboard](#monitoring-dashboard)
6. [Emergency Procedures](#emergency-procedures)

---

## 1. Pre-Live Checklist

### ✅ Performance Requirements (24-Hour Minimum)

Before going live, verify your paper trading bot meets these criteria:

```bash
# Run this on VPS to check readiness
cd /Antigravity/antigravity/scratch/crypto_trading_bot

echo "=== LIVE TRADING READINESS CHECK ==="

# Requirement 1: Win Rate > 60%
echo "1. WIN RATE CHECK (Must be > 60%):"
sqlite3 data/trades_v3_paper.db "SELECT
    strategy,
    COUNT(*) as total_trades,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
    ROUND(SUM(pnl), 2) as total_pnl
FROM positions
WHERE status='CLOSED' AND exit_time > datetime('now', '-24 hours')
GROUP BY strategy
HAVING COUNT(*) >= 5;"

# Requirement 2: No Circuit Breaker Triggers
echo ""
echo "2. CIRCUIT BREAKER CHECK (Must be 0):"
sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) as triggers_24h FROM circuit_breaker WHERE triggered_at > datetime('now', '-24 hours');"

# Requirement 3: Error Count < 10
echo ""
echo "3. ERROR COUNT CHECK (Must be < 10):"
grep -c "Error processing" logs/bot_systemd.log 2>/dev/null | tail -1000 | wc -l

# Requirement 4: At Least 10 Successful Trades
echo ""
echo "4. TRADE VOLUME CHECK (Must be >= 10):"
sqlite3 data/trades_v3_paper.db "SELECT COUNT(*) as trades_24h FROM trades WHERE timestamp > datetime('now', '-24 hours');"

# Requirement 5: Positive Net P&L
echo ""
echo "5. PROFITABILITY CHECK (Must be > 0):"
sqlite3 data/trades_v3_paper.db "SELECT ROUND(SUM(pnl), 2) as net_pnl_24h FROM positions WHERE status='CLOSED' AND exit_time > datetime('now', '-24 hours');"
```

**GO/NO-GO Decision:**
- ✅ **GO LIVE** if ALL 5 checks pass
- ❌ **STAY PAPER** if ANY check fails - continue monitoring for another 24-48 hours

---

## 2. Paper vs Live Separation

### 🗄️ Separate Databases

**Critical:** Live and paper trading MUST use separate databases to avoid confusion.

#### Option A: Run Two Separate Bot Instances (Recommended)

```
/Antigravity/antigravity/scratch/
├── crypto_trading_bot/          (Paper Trading - Port 8000)
│   ├── data/trades_v3_paper.db
│   ├── .env                     (MEXC_API_KEY not set)
│   └── run_bot.py
│
└── crypto_trading_bot_LIVE/     (Live Trading - Port 8001)
    ├── data/trades_v3_live.db
    ├── .env                     (MEXC_API_KEY set)
    └── run_bot.py
```

**Setup Commands:**

```bash
# 1. Clone paper bot to live bot directory
cd /Antigravity/antigravity/scratch
cp -r crypto_trading_bot crypto_trading_bot_LIVE

# 2. Configure live bot
cd crypto_trading_bot_LIVE

# 3. Create separate .env for live trading
cat > .env << 'EOF'
# LIVE TRADING ENVIRONMENT

# Telegram - SEPARATE CHAT for live alerts
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_LIVE_chat_id_here  # Different from paper!

# Exchange API Keys (LIVE TRADING)
MEXC_API_KEY=your_live_api_key
MEXC_SECRET=your_live_secret

# CryptoPanic API
CRYPTOPANIC_API_KEY=your_api_key

# Trading Mode Flag
TRADING_MODE=LIVE
EOF

# 4. Modify run_bot.py to use live database
sed -i "s/trades_v3_paper.db/trades_v3_live.db/g" run_bot.py

# 5. Update portfolio allocation for live trading (SMALLER positions)
nano config/portfolio_config.json  # Reduce amounts by 10x for safety
```

#### Option B: Single Bot with Mode Toggle (Not Recommended)

If you must use a single instance, add mode detection:

```python
# In core/logger.py
import os

TRADING_MODE = os.getenv('TRADING_MODE', 'PAPER')
DB_NAME = f'trades_v3_{TRADING_MODE.lower()}.db'
```

---

### 💰 Position Sizing for Live Trading

**CRITICAL SAFETY RULE:** Start with 10% of paper trading amounts

```json
// config/portfolio_config.json (LIVE)
{
  "Grid Bot BTC": {
    "symbol": "BTC/USDT",
    "allocation": 300,        // Was $3000 in paper
    "grid_levels": 20,
    "atr_multiplier": 2.0
  },
  "Grid Bot ETH": {
    "symbol": "ETH/USDT",
    "allocation": 300,        // Was $3000 in paper
    "grid_levels": 20,
    "atr_multiplier": 2.5
  },
  "Buy-the-Dip Strategy": {
    "allocation": 200,        // Was $2000 in paper
    "amount_per_trade": 50    // Was $500 in paper
  },
  "SMA Trend Bot V2": {
    "allocation": 250,        // Was $2500 in paper
    "amount_per_trade": 50
  }
}
```

**Total Live Capital:** $1,050 (vs $10,500 in paper)

After 1 week of successful live trading, you can gradually increase to 20%, 50%, then 100%.

---

## 3. Telegram Alert Configuration

### 📱 Separate Telegram Channels

**Setup:**

1. **Create Two Telegram Bots:**
   - `@BotFather` → `/newbot` → "Crypto Bot PAPER"
   - `@BotFather` → `/newbot` → "Crypto Bot LIVE" ⚠️

2. **Create Two Telegram Groups:**
   - "Crypto Bot - Paper Trading Alerts"
   - "🔴 Crypto Bot - LIVE TRADING 🔴" (use red flag emoji for visibility)

3. **Get Chat IDs:**
   ```bash
   # Add bot to each group, then get chat IDs:
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```

4. **Configure .env Files:**

   **Paper Bot (.env):**
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz  # Paper bot token
   TELEGRAM_CHAT_ID=-1001234567890                         # Paper group chat ID
   ```

   **Live Bot (.env):**
   ```bash
   TELEGRAM_BOT_TOKEN=987654321:ZYXwvuTSRqponMLKjihGFEdcba  # LIVE bot token
   TELEGRAM_CHAT_ID=-1009876543210                         # LIVE group chat ID
   ```

### 🎨 Enhanced Live Alerts

Modify `core/notifier.py` for live trading to add visual distinction:

```python
# Add to core/notifier.py
import os

TRADING_MODE = os.getenv('TRADING_MODE', 'PAPER')

def _get_alert_prefix(self):
    """Add visual prefix for live vs paper alerts"""
    if TRADING_MODE == 'LIVE':
        return "🔴 **LIVE** 🔴\n"
    else:
        return "📝 PAPER\n"

def notify_trade(self, trade_info):
    """Send trade notification with mode prefix"""
    prefix = self._get_alert_prefix()

    message = f"{prefix}"
    message += f"{'🟢 BUY' if trade_info['side'] == 'BUY' else '🔴 SELL'}\n"
    message += f"**{trade_info['symbol']}** @ ${trade_info['price']:.2f}\n"
    message += f"Amount: {trade_info['amount']:.4f}\n"
    message += f"Strategy: {trade_info['strategy']}\n"

    if TRADING_MODE == 'LIVE':
        message += f"\n⚠️ **REAL MONEY TRADE**"

    self.send_telegram_message(message)
```

---

## 4. Live Trading Safety Mechanisms

### 🛡️ Max Daily Loss Limit

Add to `core/risk_module.py`:

```python
class LiveTradingSafety:
    """Safety mechanisms for live trading"""

    def __init__(self, max_daily_loss_pct=2.0, max_daily_loss_usd=50):
        self.max_daily_loss_pct = max_daily_loss_pct  # 2% of total capital
        self.max_daily_loss_usd = max_daily_loss_usd  # $50 absolute max
        self.logger = TradeLogger()

    def check_daily_loss_limit(self):
        """Stop trading if daily loss exceeds limits"""
        query = """
        SELECT SUM(pnl) as daily_pnl
        FROM positions
        WHERE status='CLOSED'
        AND exit_time > datetime('now', '-24 hours')
        """

        result = self.logger.db.execute(query).fetchone()
        daily_pnl = result[0] if result else 0

        if daily_pnl < -self.max_daily_loss_usd:
            self._trigger_emergency_stop(
                f"Daily loss limit exceeded: ${daily_pnl:.2f}"
            )
            return False

        return True

    def _trigger_emergency_stop(self, reason):
        """Emergency stop all trading"""
        # Close all open positions
        # Pause all strategies
        # Send urgent Telegram alert
        # Write to circuit breaker
        pass
```

### ⚙️ Live Trading Configuration

Create `config/live_config.json`:

```json
{
  "safety_limits": {
    "max_daily_loss_usd": 50,
    "max_daily_loss_pct": 2.0,
    "max_position_size_usd": 100,
    "max_open_positions": 5,
    "require_manual_approval": false,
    "trading_hours": {
      "enabled": true,
      "start_hour": 6,
      "end_hour": 22,
      "timezone": "UTC"
    }
  },
  "monitoring": {
    "alert_on_every_trade": true,
    "daily_summary_time": "23:00",
    "weekly_report_day": "Sunday"
  },
  "api_limits": {
    "max_requests_per_minute": 50,
    "rate_limit_buffer": 0.8
  }
}
```

---

## 5. Monitoring Dashboard

### 📊 Real-Time Monitoring Commands

**Live Bot Status (Run every 15 minutes):**

```bash
#!/bin/bash
# save as: monitor_live_bot.sh

cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

echo "=== 🔴 LIVE BOT STATUS @ $(date) ==="
echo ""

# 1. Current Open Positions
echo "1. OPEN POSITIONS:"
sqlite3 data/trades_v3_live.db "SELECT
    strategy, symbol, buy_price, amount,
    ROUND((SELECT price FROM (SELECT price FROM trades WHERE symbol=p.symbol ORDER BY timestamp DESC LIMIT 1)) - buy_price, 2) as unrealized_pnl
FROM positions p
WHERE status='OPEN';"

echo ""

# 2. Today's P&L
echo "2. TODAY'S P&L:"
sqlite3 data/trades_v3_live.db "SELECT
    ROUND(SUM(pnl), 2) as todays_pnl,
    COUNT(*) as trades_today
FROM positions
WHERE status='CLOSED' AND exit_time > datetime('now', 'start of day');"

echo ""

# 3. Process Health
echo "3. PROCESS STATUS:"
systemctl status cryptobot_live --no-pager | head -12

echo ""

# 4. Recent Errors (Last 10 minutes)
echo "4. RECENT ERRORS:"
journalctl -u cryptobot_live --since "10 minutes ago" | grep -i error | tail -5

echo ""

# 5. Circuit Breaker
echo "5. CIRCUIT BREAKER:"
sqlite3 data/trades_v3_live.db "SELECT * FROM circuit_breaker WHERE id=1;"
```

Make it executable and add to cron:
```bash
chmod +x monitor_live_bot.sh

# Add to crontab (run every 15 minutes)
crontab -e
*/15 * * * * /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/monitor_live_bot.sh >> /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/monitor.log 2>&1
```

### 📈 Daily Performance Report

Create `scripts/daily_report.sh`:

```bash
#!/bin/bash
# Sends daily summary to Telegram

cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

REPORT=$(sqlite3 data/trades_v3_live.db << 'EOF'
SELECT
'📊 **DAILY LIVE BOT REPORT** 📊
Date: ' || date('now') || '

💰 **P&L Summary:**
Today: $' || ROUND(SUM(CASE WHEN exit_time > datetime(''now'', ''start of day'') THEN pnl ELSE 0 END), 2) || '
This Week: $' || ROUND(SUM(CASE WHEN exit_time > datetime(''now'', ''-7 days'') THEN pnl ELSE 0 END), 2) || '
This Month: $' || ROUND(SUM(CASE WHEN exit_time > datetime(''now'', ''start of month'') THEN pnl ELSE 0 END), 2) || '

📈 **Trade Stats:**
Trades Today: ' || COUNT(CASE WHEN exit_time > datetime(''now'', ''start of day'') THEN 1 END) || '
Win Rate: ' || ROUND(100.0 * SUM(CASE WHEN pnl > 0 AND exit_time > datetime(''now'', ''start of day'') THEN 1 ELSE 0 END) / COUNT(CASE WHEN exit_time > datetime(''now'', ''start of day'') THEN 1 END), 1) || '%

🎯 **Best Trade Today:**
' || (SELECT strategy || ' ' || symbol || ': $' || ROUND(pnl, 2) FROM positions WHERE exit_time > datetime('now', 'start of day') ORDER BY pnl DESC LIMIT 1) || '

⚠️ **Worst Trade Today:**
' || (SELECT strategy || ' ' || symbol || ': $' || ROUND(pnl, 2) FROM positions WHERE exit_time > datetime('now', 'start of day') ORDER BY pnl ASC LIMIT 1)
FROM positions WHERE status='CLOSED';
EOF
)

# Send to Telegram
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     -d "chat_id=${TELEGRAM_CHAT_ID}" \
     -d "text=${REPORT}" \
     -d "parse_mode=Markdown"
```

Add to crontab:
```bash
# Daily report at 11:00 PM
0 23 * * * /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/scripts/daily_report.sh
```

---

## 6. Emergency Procedures

### 🚨 Emergency Stop (Circuit Breaker)

**When to use:**
- Daily loss exceeds -$50
- Bot behaving erratically
- Market crash/black swan event
- Exchange API issues

**How to stop:**

```bash
# Method 1: Pause via Circuit Breaker (bot keeps running but stops trading)
sqlite3 /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/data/trades_v3_live.db \
"UPDATE circuit_breaker SET is_paused=1, consecutive_errors=99, reason='MANUAL EMERGENCY STOP';"

# Method 2: Stop bot completely
systemctl stop cryptobot_live

# Method 3: Close all positions manually (via exchange web interface)
# Log into MEXC → Spot Trading → Close All Positions
```

### 📞 Emergency Contact Checklist

1. **Check Telegram alerts** - all recent notifications
2. **Review open positions** - consider manual closure
3. **Check exchange balance** - verify no unauthorized activity
4. **Review logs** - identify root cause
5. **Update safety limits** - if limits were insufficient

---

## 7. Systemd Service for Live Bot

Create `/etc/systemd/system/cryptobot_live.service`:

```ini
[Unit]
Description=Crypto Trading Bot (LIVE TRADING - REAL MONEY)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE
ExecStart=/usr/bin/python3 -u /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/run_bot.py

# Kill all processes on stop
KillMode=control-group
TimeoutStopSec=10

# Auto-restart on failure
Restart=on-failure
RestartSec=30

# Environment
EnvironmentFile=/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/.env

# Logging
StandardOutput=append:/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/bot_live.log
StandardError=append:/Antigravity/antigravity/scratch/crypto_trading_bot_LIVE/logs/bot_live_error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cryptobot_live
sudo systemctl start cryptobot_live
```

---

## ✅ Final Pre-Launch Checklist

Before starting live trading:

- [ ] Paper trading shows 24+ hours of profitable performance
- [ ] Win rate > 60% across all strategies
- [ ] No circuit breaker triggers in last 24 hours
- [ ] Separate Telegram bot and chat for live alerts configured
- [ ] Separate database (trades_v3_live.db) created
- [ ] Position sizes reduced to 10% of paper amounts
- [ ] Max daily loss limit set ($50 or 2% of capital)
- [ ] Exchange API keys added to .env (with IP whitelist)
- [ ] Systemd service created and tested
- [ ] Monitoring cron jobs configured
- [ ] Emergency stop procedure tested
- [ ] All team members notified of go-live time
- [ ] Exchange account has sufficient balance + buffer

**Final Sign-Off:** Only proceed when ALL boxes are checked ✅

---

## 📌 Quick Reference

| Task | Paper Bot | Live Bot |
|------|-----------|----------|
| Directory | `/Antigravity/.../crypto_trading_bot` | `/Antigravity/.../crypto_trading_bot_LIVE` |
| Database | `trades_v3_paper.db` | `trades_v3_live.db` |
| Systemd Service | `cryptobot.service` | `cryptobot_live.service` |
| Telegram Chat | Paper Trading Alerts | 🔴 LIVE TRADING 🔴 |
| Position Size | $100-500 per trade | $10-50 per trade (10%) |
| Max Daily Loss | No limit | $50 hard stop |
| Logs | `logs/bot_systemd.log` | `logs/bot_live.log` |

---

**Remember: Start small, monitor closely, scale gradually. Never risk more than you can afford to lose.** 🛡️
