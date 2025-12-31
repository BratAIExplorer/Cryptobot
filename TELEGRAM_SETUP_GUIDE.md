# 📱 Telegram Alerts Setup Guide

## ✅ Current Status

**Good News:** Telegram alerts are ALREADY FULLY IMPLEMENTED in your bot! 🎉

The system currently supports:
- ✅ Trade executions (BUY/SELL)
- ✅ Stop Loss hits (with specific alert)
- ✅ Take Profit hits (with specific alert)
- ✅ Trailing Stop hits (with specific alert)
- ✅ Large loss warnings (>$50)
- ✅ Circuit breaker triggers
- ✅ Max drawdown warnings
- ✅ No activity alerts
- ✅ Service restarts
- ✅ Daily performance summaries
- ✅ Profit milestones
- ✅ Confluence signals
- ✅ New coin listings
- ✅ Error alerts

**All you need to do is configure the environment variables!**

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts:
   - Choose a name: `My Crypto Trading Bot`
   - Choose a username: `mycryptobot_123_bot` (must end with `_bot`)
4. **BotFather will give you a TOKEN** - save this!
   - Example: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. The bot will reply with your **Chat ID**
   - Example: `987654321`

### Step 3: Configure Environment Variables

**On your VPS:**

```bash
# Edit .env file
nano .env

# Add these lines (replace with your actual values):
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# Save and exit (Ctrl+X, Y, Enter)
```

**Or export directly:**

```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
export TELEGRAM_CHAT_ID='987654321'
```

### Step 4: Test the Connection

```bash
cd /home/user/Cryptobot
python3 scripts/test_telegram.py
```

**Expected Output:**
```
============================================================
🔔 TELEGRAM DRY RUN TEST
============================================================
🔑 Token: 12345...xyz
🆔 Chat ID: 987654321

Attempting to send test message...
✅ SUCCESS! Message sent.
```

**You should receive a message in Telegram:**
```
🔔 Dry Run Test

If you see this, your Telegram alerts are working! 🚀
```

### Step 5: Restart the Bot

```bash
# If running as systemd service:
sudo systemctl restart crypto_bot_runner

# If running with PM2:
pm2 restart crypto_bot

# If running manually:
# Stop current bot (Ctrl+C)
python3 run_bot.py
```

**You should immediately receive a startup notification in Telegram!**

---

## 📊 What Alerts You'll Receive

### 🟢 **Trade Executions**

**Buy Alert:**
```
🟢 BUY BTC/USDT
Price: $45,230.50
Amount: 0.0221
Reason: Golden Cross detected
```

**Sell Alert (Generic):**
```
🔴 SELL ETH/USDT
Price: $3,150.00
Amount: 0.3175
Reason: Profit: $45.50 (+3.2%)
```

### 🛑 **Stop Loss Hit**

```
🛑 STOP LOSS HIT

Symbol: SOL/USDT
Strategy: SMA Trend Bot V2

Entry: $98.50
Exit: $93.57
Loss: $24.65 (-5.00%)

✅ Position closed - Capital preserved
```

### 🎯 **Take Profit Hit**

```
🎯 TAKE PROFIT HIT

Symbol: BTC/USDT
Strategy: Hidden Gem Monitor V2

Entry: $44,500.00
Exit: $51,175.00
Profit: $133.50 (+15.00%)

🎉 Winner! Target reached
```

### 📉 **Trailing Stop Hit**

```
📉 TRAILING STOP HIT

Symbol: ETH/USDT
Strategy: SMA Trend Bot V2

Entry: $3,000.00
Peak Profit: +12.50%
Exit: $3,285.00
Final Profit: $95.25 (+9.50%)

✅ Profits secured via trailing stop
```

### 💥 **Large Loss Alert**

```
💥 LARGE LOSS ALERT

Symbol: DOGE/USDT
Loss: $75.50 (7.5%)

Review trade details on dashboard.
```

### 🔴 **Circuit Breaker Triggered**

```
🔴 CIRCUIT BREAKER TRIGGERED (Bot: SMA Trend Bot V2)

⚠️ Bot has been paused due to 3 consecutive errors.
❌ Last Error: `MEXC API timeout`

⏰ Auto-recovery in 30 minutes.

Check logs: `pm2 logs crypto_bot`
```

### 📊 **Daily Summary (Automated)**

```
📊 DAILY SUMMARY

Date: 2024-01-15
Total P&L: $+248.75
Trades: 12
Win Rate: 75.0%

Best Strategy: SMA Trend Bot V2
P&L: $+150.25
```

### 🚀 **Bot Startup**

```
🚀 Bot Started 🚀

Mode: PAPER
Active Strategies:
- SMA Trend Bot V2 (5 symbols)
- Hidden Gem Monitor V2 (15 symbols)
- Hybrid v2.0 (10 symbols)
- Grid Bot - BTC (1 symbols)
- Grid Bot - ETH (1 symbols)
- Momentum Swing Bot (5 symbols)

✅ Systems Check: OK
```

---

## 🔧 Troubleshooting

### ❌ "Token not found" Error

**Solution:** Check your `.env` file has the correct token format:
```bash
cat .env | grep TELEGRAM
```

### ❌ "Unauthorized" Error

**Problem:** Bot token is invalid

**Solution:**
1. Go back to @BotFather
2. Send `/mybots`
3. Select your bot
4. Click "API Token" to regenerate

### ❌ "Chat not found" Error

**Problem:** Chat ID is incorrect

**Solution:**
1. Message your bot first (send any message like `/start`)
2. Get your Chat ID from @userinfobot again
3. Update the `.env` file

### ❌ Not Receiving Alerts

**Check:**
1. Bot is actually running: `pm2 status` or `systemctl status crypto_bot_runner`
2. Environment variables loaded: `echo $TELEGRAM_BOT_TOKEN`
3. Check bot logs for errors: `pm2 logs crypto_bot --lines 50`

---

## 🎛️ Customization

### Disable Certain Alerts

Edit `core/notifier.py` to comment out unwanted notifications:

```python
# Example: Disable startup notifications
def notify_startup(self, mode, active_bots):
    return  # Disabled
    # ... rest of code
```

### Change Alert Frequency

The bot has built-in throttling:
- **Startup alerts:** Max once per 4 hours
- **Performance summaries:** Every 4 hours
- **No activity warnings:** After 24 hours

To change, edit the `hours` parameter in `core/engine.py`:

```python
# Line 355 - Performance summaries
if self.notifier.can_send_throttled_msg("periodic_performance_summary", hours=4):
    # Change hours=4 to your preference

# Line 417 - No activity warnings
if hours_since_trade > 24:  # Change 24 to your preference
```

### Add Custom Alerts

Add new methods to `core/notifier.py`:

```python
def alert_custom_event(self, message):
    """Send custom alert"""
    msg = f"🔔 *CUSTOM ALERT*\n\n{message}"
    self.send_message(msg)
```

Then call from anywhere in the bot:
```python
self.notifier.alert_custom_event("My custom event happened!")
```

---

## 📝 Testing Checklist

After setup, verify these alerts work:

- [ ] Startup notification received when bot starts
- [ ] Trade execution alerts (wait for first trade or simulate)
- [ ] Daily summary (wait 4 hours or test manually)
- [ ] Stop loss alert (trigger by setting very tight SL in test mode)
- [ ] Take profit alert (trigger by setting low TP target)
- [ ] Error alert (simulate by causing an API error)

---

## 🎉 You're Done!

Your Telegram alerts are now active. You'll receive real-time notifications for:
- Every trade executed
- Every stop loss or take profit hit
- Critical errors and warnings
- Daily performance summaries
- And more!

**Pro Tip:** Create a dedicated Telegram group and add your bot to it. Invite your team members to monitor the bot together!

---

## 📚 Additional Resources

- **Test Telegram:** `python3 scripts/test_telegram.py`
- **Send Manual Report:** `python3 scripts/telegram_report.py`
- **Notifier Code:** `core/notifier.py` (lines 1-308)
- **Integration Code:** `core/engine.py` (search for "notifier")

---

**Need Help?** Check the logs:
```bash
pm2 logs crypto_bot --lines 100
# Look for "Telegram notifications enabled" message
```

**Still Having Issues?**
1. Verify environment variables: `env | grep TELEGRAM`
2. Test the bot token manually: https://api.telegram.org/bot<YOUR_TOKEN>/getMe
3. Check firewall allows outbound HTTPS (port 443)
