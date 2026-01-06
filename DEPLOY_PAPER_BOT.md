# 🚀 Deploy Binance Paper Trading Bot - Step by Step Guide

## ✅ Pre-Deployment Checklist

### 1. Pull Latest Code
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
git pull origin claude/bot-launch-checklist-SmLAH
```

**What's new:**
- ✅ Continuous monitoring loop (bot stays running)
- ✅ Sandbox mode fix (connects to testnet)
- ✅ Notifier super() fix (Telegram alerts work)
- ✅ Strategic planning docs (market analysis, dashboard architecture)

### 2. Verify Environment Configuration
```bash
cat .env.binance.paper | grep -v SECRET
```

**Should show:**
```
BINANCE_API_KEY=eWG8WCL... (your testnet key)
BINANCE_SECRET=*** (hidden)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TRADING_MODE=paper
```

### 3. Run Pre-Launch Verification
```bash
python3 verify_binance_paper.py
```

**Expected output:**
```
✅ Paper API Key: eWG8WCLNoH...rJkq
✅ Binance Testnet Connected: $10,000.00 USDT (fake money)
✅ BTC/USDT: Active
✅ ETH/USDT: Active
✅ Testnet order works
🎉 TESTNET ORDER WORKS!
```

---

## 🎬 Launch the Bot

### Start in Screen Session (Recommended)
```bash
# Create a new screen session named "binance-paper"
screen -S binance-paper

# Launch the bot
python3 run_bot_binance_SAFE_PAPER.py

# Detach from screen: Ctrl+A, then D
# Reattach later: screen -r binance-paper
```

### Or Run in Background with nohup
```bash
nohup python3 run_bot_binance_SAFE_PAPER.py > logs/binance_paper_bot.log 2>&1 &
echo $! > bot.pid
```

---

## 📊 Expected Startup Sequence

You should see this sequence:

### 1. Initial Configuration
```
================================================================================
📝 BINANCE PAPER TRADING BOT - PHASE 3 📝
================================================================================
✅ TESTNET MODE: Using fake money on Binance testnet!
Exchange: binance
Mode: PAPER
Sandbox: True
Database: data/trades_binance_paper.db
Balance: $218.08 USDT (target)
Tradeable: $141.75 (65%)
Reserve: $76.33 (35%)
```

### 2. Pre-Launch Verification
```
================================================================================
🔍 PRE-LAUNCH ENVIRONMENT VERIFICATION
================================================================================
✅ BINANCE_API_KEY: **********rJkq
✅ BINANCE_SECRET: **********shAV
✅ TELEGRAM_BOT_TOKEN: **********W4Wk
✅ TELEGRAM_CHAT_ID: **********6792

🔗 Testing Binance Testnet API connection...
✅ Binance Testnet Connected: $10,000.00 USDT (fake money)
✅ BTC/USDT: Active
✅ ETH/USDT: Active

📱 Testing Telegram...
✅ Telegram test message sent

================================================================================
✅ ALL CHECKS PASSED - READY FOR PAPER TRADING
================================================================================
```

### 3. 10-Second Abort Window
```
⏸️  FINAL SAFETY CHECK:
   - Environment verified ✅
   - Capital allocation set ✅
   - Telegram alerts configured ✅
   - Emergency stop ready ✅

⚠️  Press Ctrl+C within 10 seconds to ABORT...
   Otherwise, PAPER trading will begin!

   Starting in 10...
   Starting in 9...
   ...
```

### 4. Bot Initialization
```
🚀 LAUNCHING PAPER TRADING NOW (Testnet)...
[DB] Initialized V3 Database at data/trades_binance_paper.db
[Capital Control] Daily loss limit: $50.00
[Capital Control] Binance_Grid_BTC_Paper: $80.00 allocated
[Capital Control] Binance_Grid_ETH_Paper: $60.00 allocated
INFO:core.exchange_unified:🔧 Binance sandbox mode enabled (testnet)
INFO:core.exchange_unified:✅ Connected to BINANCE in PAPER mode
```

### 5. Capital Allocation Summary
```
================================================================================
💰 PHASE 1 CAPITAL ALLOCATION
================================================================================

1️⃣  Grid Bot BTC: $80
2️⃣  Grid Bot ETH: $60

============================================================
💰 CAPITAL ALLOCATION STATUS
============================================================
Total Portfolio: $140.00
Currently Used:  $0.00 (0.0%)
Available:       $140.00
Daily P&L:       $+0.00 (Limit: -$50.00)

Per-Bot Allocation:
  Binance_Grid_BTC_Paper    | $     0 / $    80 |   0.0% | Available: $    80
  Binance_Grid_ETH_Paper    | $     0 / $    60 |   0.0% | Available: $    60
============================================================

📋 Bot PID: 12345 (saved to bot.pid)
```

### 6. Continuous Monitoring Loop (NEW!)
```
🚀 PAPER TRADING ACTIVE (Testnet) - Monitoring for signals...
================================================================================

Engine started in paper mode
🌡️ Warming up Market Regime Detector...
✅ Market Regime Initialized: BULL (Confidence: 73.5%)
🔗 Building correlation matrix for portfolio diversification...
✅ Correlation Matrix Built: 2 pairs analyzed
[STARTUP] Updating Binance_Grid_BTC_Paper: Trades=0, PnL=$0.0, Balance=$0.0
[STARTUP] Updating Binance_Grid_ETH_Paper: Trades=0, PnL=$0.0, Balance=$0.0

💫 Starting continuous monitoring loop...
   Press Ctrl+C to stop gracefully

============================================================
📊 Cycle 1 - 2026-01-06 06:00:00
============================================================
[Trading logic executes...]
⏸️  Waiting 60 seconds until next cycle...

============================================================
📊 Cycle 2 - 2026-01-06 06:01:00
============================================================
[Trading logic executes...]
⏸️  Waiting 60 seconds until next cycle...
```

**This continuous loop is the key indicator that the fix worked!**

---

## 🔍 Monitoring the Bot

### Check if Bot is Running
```bash
# Check process
ps aux | grep run_bot_binance_SAFE_PAPER

# Check PID file
cat bot.pid

# View recent logs
tail -f logs/live_*.log
```

### Monitor Trading Activity
```bash
# View database
sqlite3 data/trades_binance_paper.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# Check bot status
sqlite3 data/trades_binance_paper.db "SELECT * FROM bot_status;"

# Monitor capital
sqlite3 data/trades_binance_paper.db "SELECT * FROM capital_tracking ORDER BY timestamp DESC LIMIT 5;"
```

### Telegram Notifications

You should receive these messages:

**1. Pre-launch Test:**
```
📝 PAPER BOT - Pre-launch test successful! Launching in 10 seconds...

(Testnet - fake money)
```

**2. Bot Startup:**
```
📝 PAPER
🚀 Bot Started 🚀

Mode: PAPER
Total Allocation: $140.00

Active Strategies:
- Binance_Grid_BTC_Paper: $80
- Binance_Grid_ETH_Paper: $60

✅ Systems Check: OK

(Testnet - fake money)
```

**3. Bot Launch Alerts:**
```
📝 PAPER
🤖 Bot Activated

Name: Binance_Grid_BTC_Paper
Symbol: BTC/USDT
Allocation: $80.00

(Testnet - fake money)
```

**4. Trade Alerts (when trades happen):**
```
📝 PAPER
🟢 BUY BTC/USDT
Price: $93,732.11
Amount: 0.0008
Value: $74.99
Reason: Grid level 2 fill

(Testnet - fake money)
```

---

## 🛑 Stopping the Bot

### Method 1: Graceful Shutdown (Ctrl+C)
```bash
# If running in foreground, press Ctrl+C
# If in screen session:
screen -r binance-paper
# Then Ctrl+C
```

### Method 2: Stop Signal File
```bash
touch STOP_SIGNAL
# Bot will detect and shutdown gracefully
```

### Method 3: Kill by PID
```bash
kill $(cat bot.pid)
```

**All methods trigger graceful shutdown showing:**
```
⚠️  Interrupted by user. Shutting down gracefully...

================================================================================
✅ BINANCE PAPER BOT STOPPED
================================================================================

============================================================
💰 CAPITAL ALLOCATION STATUS
============================================================
[Final summary displayed]

📊 Review results:
   python analyze_trades.py --db data/trades_binance_paper.db
   sqlite3 data/trades_binance_paper.db 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;'
```

---

## 🚨 Troubleshooting

### Bot Starts Then Immediately Stops

**Before Fix:**
```
Engine started in paper mode
✅ Market Regime Initialized
✅ Correlation Matrix Built

================================================================================
✅ BINANCE PAPER BOT STOPPED  ← Immediate exit!
================================================================================
```

**After Fix (Expected):**
```
Engine started in paper mode
✅ Market Regime Initialized
✅ Correlation Matrix Built

💫 Starting continuous monitoring loop...  ← Should see this!

============================================================
📊 Cycle 1 - 2026-01-06 06:00:00  ← And this!
============================================================
```

**If still stopping immediately:**
- Pull latest code: `git pull origin claude/bot-launch-checklist-SmLAH`
- Check you have `core/engine.py` with monitoring loop (lines 255-283)

### Connection Errors

**Error: "Invalid Api-Key ID" (-2008)**
```bash
# Check you're using testnet keys
grep BINANCE_API_KEY .env.binance.paper
# Should be testnet key, NOT live Binance key
```

**Error: "Sandbox mode not enabled"**
```bash
# Verify code has sandbox fix
grep "set_sandbox_mode" core/exchange_unified.py
# Should show lines 65-67 with sandbox mode check
```

### Telegram Not Working

**Check configuration:**
```bash
# Test Telegram manually
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<YOUR_CHAT_ID>", "text": "Test from bash"}'
```

**If bot runs but no Telegram:**
- Bot continues without Telegram (non-critical)
- Check logs: `tail -f logs/live_*.log | grep Telegram`

---

## ✅ Success Criteria

After 2-4 hours, bot should show:

### 1. Continuous Operation
```bash
# Bot process running
ps aux | grep run_bot_binance_SAFE_PAPER
# Should show running process

# Multiple cycles executed
tail -100 logs/live_*.log | grep "Cycle"
# Should show Cycle 1, 2, 3... 120+
```

### 2. No Critical Errors
```bash
# Check for errors
grep ERROR logs/live_*.log | tail -20
# Minor warnings OK, no fatal errors
```

### 3. Database Updated
```bash
sqlite3 data/trades_binance_paper.db "SELECT COUNT(*) FROM bot_status;"
# Should show bot status records
```

### 4. Telegram Active
- Startup messages received
- Bot launch alerts received
- No error notifications

---

## 📈 After 24 Hours Success

If bot runs successfully for 24 hours:

### Phase 3A: Add More Strategies

**Option 1: Add Buy the Dip**
```bash
# Edit run_bot_binance_SAFE_PAPER.py
# Change allocations to include BuyDip strategy
```

**Option 2: Add BNB Grid**
```bash
# Run market analysis first
python3 check_binance_testnet_markets.py

# Then add BNB/USDT to allocations
```

### Phase 3B: Dashboard Integration

**Update dashboard to show PAPER mode:**
```bash
# Run dashboard
streamlit run dashboard.py --server.port 8501
```

**Add mode selector:**
- Implement tab system (PAPER / LIVE / Intelligence)
- Display bot status from trades_binance_paper.db
- Show shared intelligence (regime, correlations)

---

## 🎯 Next Milestones

### Milestone 1: 24 Hours Stable (Phase 3 Complete)
- ✅ Bot runs continuously
- ✅ No critical errors
- ✅ Telegram alerts working
- ✅ Capital tracking correct

### Milestone 2: Strategy Expansion (Phase 3A)
- Add Buy the Dip strategy
- Add BNB Grid bot
- Compare strategy performance

### Milestone 3: Dashboard Integration (Phase 3B)
- Unified dashboard with mode tabs
- PAPER mode visualization
- Intelligence module display

### Milestone 4: Small Live Test (Phase 4)
- Transfer $30 to Binance
- Run alongside PAPER bot
- Monitor both on unified dashboard

---

## 📞 Getting Help

**If stuck:**
1. Share the exact error message
2. Show recent logs: `tail -50 logs/live_*.log`
3. Check bot status: `ps aux | grep run_bot_binance`
4. Verify environment: `python3 verify_binance_paper.py`

**Common issues all have fixes documented above!**

---

## 🚀 Ready to Launch!

```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
git pull origin claude/bot-launch-checklist-SmLAH
python3 verify_binance_paper.py
screen -S binance-paper
python3 run_bot_binance_SAFE_PAPER.py
# Ctrl+A, D to detach
```

**Let it run! The bot will monitor continuously and you can check progress anytime.** 📊
