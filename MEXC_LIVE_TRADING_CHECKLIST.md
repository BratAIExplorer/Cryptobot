# 🚀 MEXC LIVE TRADING PRE-LAUNCH CHECKLIST

**CRITICAL:** This is your final checklist before enabling live trading with **REAL MONEY** on MEXC.

**Status:** Your MEXC account is now funded ✅
**Next Step:** Complete ALL items below before launching bots

---

## 📋 TABLE OF CONTENTS

1. [🔐 Security & API Configuration](#1-security--api-configuration)
2. [💰 Account & Funding Verification](#2-account--funding-verification)
3. [⚙️ Bot Configuration Review](#3-bot-configuration-review)
4. [🧪 System Health Checks](#4-system-health-checks)
5. [📱 Monitoring & Alerts Setup](#5-monitoring--alerts-setup)
6. [🛡️ Risk Management Validation](#6-risk-management-validation)
7. [🎯 Final Pre-Launch Validation](#7-final-pre-launch-validation)
8. [🚦 GO/NO-GO Decision](#8-gono-go-decision)

---

## 1. 🔐 Security & API Configuration

### API Key Setup
- [ ] **MEXC API keys created** with **SPOT TRADING ONLY** permissions
- [ ] **IP Whitelist configured** (do NOT allow all IPs)
- [ ] **Withdrawals DISABLED** on API keys (critical security measure)
- [ ] **API keys saved** in `.env` file (not `.env.template`)
- [ ] **.env file permissions** set correctly (`chmod 600 .env`)
- [ ] **API keys tested** with read-only call (balance check)

**Commands to verify:**
```bash
# Check .env file exists and has correct permissions
ls -la .env
# Should show: -rw------- (600 permissions)

# Test API connection (read-only)
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
import ccxt
mexc = ccxt.mexc({
    'apiKey': os.getenv('MEXC_API_KEY'),
    'secret': os.getenv('MEXC_SECRET_KEY'),
    'enableRateLimit': True
})
print('Testing MEXC API...')
balance = mexc.fetch_balance()
print(f\"✅ API Connected! USDT Balance: \${balance['USDT']['total']:.2f}\")
"
```

### Environment Configuration
- [ ] **TRADING_MODE=LIVE** set in `.env` or bot config
- [ ] **EXCHANGE=MEXC** confirmed in bot startup
- [ ] **Database separation:** Using `trades_mexc_live.db` (NOT paper DB)
- [ ] **Telegram credentials** configured for LIVE alerts (separate chat from paper)

**Create `.env` file now:**
```bash
cat > .env << 'EOF'
# MEXC LIVE TRADING CONFIGURATION
MEXC_API_KEY=your_actual_api_key_here
MEXC_SECRET_KEY=your_actual_secret_key_here

# Telegram Alerts (LIVE - use separate bot/chat from paper!)
TELEGRAM_BOT_TOKEN=your_live_bot_token_here
TELEGRAM_CHAT_ID=your_live_chat_id_here

# Trading Mode
TRADING_MODE=LIVE
EXCHANGE=MEXC

# CryptoPanic (optional but recommended)
CRYPTOPANIC_API_KEY=your_api_key_here
EOF

chmod 600 .env
```

---

## 2. 💰 Account & Funding Verification

### Balance Checks
- [ ] **Total USDT balance confirmed** on MEXC Spot Wallet
- [ ] **Balance > $1,500** minimum for 6-strategy portfolio
- [ ] **Reserved buffer:** Keep 20% uninvested ($300+ if $1500 funded)
- [ ] **No pending transfers** or locked funds
- [ ] **Correct wallet type:** Funds in SPOT wallet (not Futures/Margin)

**Check balance:**
```bash
python3 -c "
import ccxt, os
from dotenv import load_dotenv
load_dotenv()
mexc = ccxt.mexc({
    'apiKey': os.getenv('MEXC_API_KEY'),
    'secret': os.getenv('MEXC_SECRET_KEY')
})
bal = mexc.fetch_balance()
usdt = bal['USDT']['total']
print(f'💰 MEXC USDT Balance: \${usdt:,.2f}')
print(f'✅ Sufficient for live trading' if usdt >= 1500 else '❌ Need at least \$1,500')
"
```

### Capital Allocation Plan
Based on your funded amount, allocate capital conservatively:

**Recommended Allocation (for $1,500 - $3,000):**
- Buy-the-Dip: $500-800 ($25-40/coin)
- Grid Bot BTC: $200-300
- Grid Bot ETH: $200-300
- Hyper-Scalper: $200-400 ($50-100/coin)
- SMA Trend: $200-400 ($50-100/coin)
- Hidden Gem: $200-400 ($25-50/coin)
- **Reserve (20%):** Keep uninvested as buffer

- [ ] **Capital allocation** matches your actual balance
- [ ] **Per-coin position sizes** appropriate for balance
- [ ] **Reserve buffer** maintained (don't invest 100%)

---

## 3. ⚙️ Bot Configuration Review

### Strategy Parameters
- [ ] **Position sizes reduced** from paper trading (10x smaller to start)
- [ ] **Stop losses configured** for ALL strategies
- [ ] **Take profit targets** are realistic (5-15% range)
- [ ] **Max positions per strategy** limited appropriately
- [ ] **No test/debug symbols** in coin lists (remove any test pairs)

**Review run_bot_mexc.py:**
```bash
# Check current configuration
grep -A 5 "amount" run_bot_mexc.py | head -30

# Verify position sizes are SMALL for live launch
# Example: Buy-the-Dip should be $25-50/coin, not $500!
```

### Database Configuration
- [ ] **Live database path** set: `data/trades_mexc_live.db`
- [ ] **NOT using paper database** (verify path in bot code)
- [ ] **Database initialized** with correct schema
- [ ] **Backup strategy** in place for database

**Verify database setup:**
```bash
# Check which database the bot will use
grep -i "database\|db_path\|trades.*\.db" run_bot_mexc.py

# Create live database directory
mkdir -p data
```

### Symbol Verification
- [ ] **All symbols available on MEXC** (check exchange listing)
- [ ] **No delisted coins** in strategy configs
- [ ] **Sufficient liquidity** for all pairs (>$100k daily volume)
- [ ] **Correct symbol format:** BTC/USDT not BTCUSDT

**Test symbol availability:**
```bash
python3 -c "
import ccxt
mexc = ccxt.mexc()
mexc.load_markets()

# Check critical pairs
test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
for sym in test_symbols:
    if sym in mexc.markets:
        ticker = mexc.fetch_ticker(sym)
        vol = ticker.get('quoteVolume', 0)
        print(f'✅ {sym}: \${vol:,.0f} 24h volume')
    else:
        print(f'❌ {sym}: NOT AVAILABLE ON MEXC')
"
```

---

## 4. 🧪 System Health Checks

### Bot System Verification
- [ ] **Run `verify_bot.py`** - all checks pass
- [ ] **Python dependencies** installed (`pip install -r requirements.txt`)
- [ ] **Database schema** correct (all tables created)
- [ ] **File permissions** correct for data/logs directories
- [ ] **No errors** in recent logs

**Run verification:**
```bash
# Run comprehensive bot verification
python3 verify_bot.py

# Check Python packages
pip list | grep -E "ccxt|pandas|streamlit|tenacity"

# Test database connection
python3 -c "
from core.logger import TradeLogger
logger = TradeLogger(db_path='data/trades_mexc_live.db')
logger.verify_schema()
print('✅ Database schema verified')
"
```

### Exchange Connectivity
- [ ] **MEXC API responding** (test ticker fetch)
- [ ] **Rate limits understood** (100ms between requests)
- [ ] **Heartbeat mechanism** working (if using mexc exchange module)
- [ ] **No network errors** in test calls
- [ ] **Latency acceptable** (<2 seconds per API call)

**Test connectivity:**
```bash
python3 -c "
import ccxt, time
mexc = ccxt.mexc({'enableRateLimit': True})

print('Testing MEXC connectivity...')
start = time.time()
ticker = mexc.fetch_ticker('BTC/USDT')
latency = (time.time() - start) * 1000

print(f'✅ BTC/USDT: \${ticker[\"last\"]:,.2f}')
print(f'⏱️  Latency: {latency:.0f}ms')
print('✅ OK' if latency < 2000 else '⚠️ High latency!')
"
```

### Risk Module Checks
- [ ] **Circuit breaker** configured and tested
- [ ] **Max daily loss limit** set ($50-100 recommended)
- [ ] **Max position size** enforced per strategy
- [ ] **Cooldown periods** configured (prevent overtrading)
- [ ] **Emergency stop** mechanism tested

---

## 5. 📱 Monitoring & Alerts Setup

### Telegram Configuration
- [ ] **LIVE Telegram bot** created (separate from paper bot!)
- [ ] **LIVE chat/group** created (label clearly: "🔴 MEXC LIVE 🔴")
- [ ] **Test message sent** and received successfully
- [ ] **Alert format** includes "LIVE" indicator
- [ ] **All team members** added to live alerts group

**Test Telegram:**
```bash
# Test Telegram notification
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

message = '''
🔴 **LIVE TRADING TEST** 🔴

This is a test message from your MEXC live trading bot.

If you receive this, Telegram alerts are working!

⚠️ This is REAL MONEY trading mode.
'''

url = f'https://api.telegram.org/bot{token}/sendMessage'
requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'})
print('✅ Test alert sent! Check your Telegram.')
"
```

### Monitoring Schedule
- [ ] **First hour:** Check every 15 minutes
- [ ] **First 24h:** Check every 2-4 hours
- [ ] **First week:** Daily review at minimum
- [ ] **Dashboard access** verified (if using web UI)
- [ ] **Cron/scheduled checks** configured (optional but recommended)

**Create monitoring script:**
```bash
cat > monitor_live.sh << 'EOF'
#!/bin/bash
echo "=== MEXC LIVE BOT STATUS @ $(date) ==="

# 1. Check if bot is running
if pgrep -f "run_bot_mexc.py" > /dev/null; then
    echo "✅ Bot is running (PID: $(pgrep -f run_bot_mexc.py))"
else
    echo "❌ Bot is NOT running!"
fi

# 2. Check recent logs for errors
echo ""
echo "Recent errors (last 10 min):"
tail -100 logs/bot_$(date +%Y%m%d).log 2>/dev/null | grep -i error | tail -5

# 3. Database quick stats
echo ""
echo "Trade counts:"
sqlite3 data/trades_mexc_live.db "SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells
FROM trades;" 2>/dev/null || echo "Database not accessible"

echo ""
echo "=== End Status ==="
EOF

chmod +x monitor_live.sh
./monitor_live.sh  # Test it
```

---

## 6. 🛡️ Risk Management Validation

### Position Limits
- [ ] **Max daily loss:** $50-100 limit configured
- [ ] **Max open positions:** 10-15 total across all strategies
- [ ] **Max per-coin exposure:** $100-200 maximum
- [ ] **Max per-strategy capital:** No single strategy >30% of portfolio
- [ ] **Correlation limits:** Not >50% in correlated coins (BTC/ETH)

### Stop Loss Configuration
- [ ] **ALL strategies have stop losses** (no exceptions!)
- [ ] **Stop loss percentages:** 3-10% range (not >10%)
- [ ] **Hard stops enforced** (not just trailing)
- [ ] **Stop loss execution tested** in code
- [ ] **Emergency liquidation** plan documented

### Trading Hours (Optional but Recommended)
- [ ] **Consider limiting trading hours** (e.g., 6 AM - 10 PM UTC)
- [ ] **Weekend trading** decision made (pause or continue?)
- [ ] **High volatility blackout** periods identified
- [ ] **Manual override** capability available

---

## 7. 🎯 Final Pre-Launch Validation

### Paper Trading Performance Review
Before going live, verify paper trading was successful:

- [ ] **Paper trading ran >24 hours** successfully
- [ ] **Win rate >40%** across strategies
- [ ] **No circuit breaker triggers** in last 24h
- [ ] **No critical errors** in logs
- [ ] **Positive net P&L** in paper mode

**Check paper performance:**
```bash
# Review paper trading results
sqlite3 data/trades_v3_paper.db "
SELECT
    'Win Rate: ' || ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) || '%' as metric,
    'Total P&L: $' || ROUND(SUM(pnl), 2) as value
FROM positions
WHERE status='CLOSED' AND exit_time > datetime('now', '-24 hours');
"
```

**If paper trading shows:**
- ✅ Win rate >40% → Proceed to live
- ⚠️ Win rate 30-40% → Reduce position sizes by 50%
- ❌ Win rate <30% → DO NOT go live, fix strategies first

### Code Review Checklist
- [ ] **No hardcoded test values** (amount=999999, symbol='TEST/USDT')
- [ ] **No debug prints** that spam logs
- [ ] **Exception handling** present for API calls
- [ ] **Logging configured** properly (not DEBUG level in production)
- [ ] **No infinite loops** or uncaught exceptions

**Quick code audit:**
```bash
# Check for common issues
grep -n "amount.*99999\|symbol.*TEST\|mode.*paper" run_bot_mexc.py
grep -n "print(" run_bot_mexc.py | head -20  # Minimize debug prints
grep -n "try:\|except" run_bot_mexc.py | wc -l  # Should have exception handling
```

### Emergency Procedures Documented
- [ ] **How to stop bot** documented (Ctrl+C, kill command, STOP_SIGNAL file)
- [ ] **How to close all positions** on MEXC web UI
- [ ] **Emergency contact plan** (who to notify if issues)
- [ ] **Rollback procedure** documented (git, database backup)
- [ ] **MEXC support contact** info saved

**Emergency stop methods:**
```bash
# Method 1: STOP_SIGNAL file
touch STOP_SIGNAL

# Method 2: Kill process
pkill -f run_bot_mexc.py

# Method 3: Keyboard interrupt (if running in foreground)
# Press Ctrl+C
```

---

## 8. 🚦 GO/NO-GO Decision

### Final Checklist Summary

Review the categories below. **ALL must be GREEN to proceed.**

| Category | Status | Required Actions |
|----------|--------|------------------|
| Security & API | ⬜ | All API keys configured, IP whitelisted |
| Account Funding | ⬜ | Balance verified, capital allocated |
| Bot Configuration | ⬜ | Reduced position sizes, correct database |
| System Health | ⬜ | verify_bot.py passes, no errors |
| Monitoring Setup | ⬜ | Telegram working, monitoring scheduled |
| Risk Management | ⬜ | Stop losses, max loss limits configured |
| Paper Performance | ⬜ | >40% win rate in 24h paper trading |
| Emergency Procedures | ⬜ | Stop methods documented and tested |

### GO/NO-GO Decision Matrix

**✅ GREEN - GO LIVE:**
- All 8 categories checked ✅
- Paper trading win rate >40%
- No critical errors in last 24h
- Team ready to monitor first 24h closely

**⚠️ YELLOW - DELAY 24-48H:**
- 1-2 minor issues (can be fixed quickly)
- Paper win rate 35-40% (borderline)
- Reduce position sizes by 50% and proceed with caution

**❌ RED - DO NOT LAUNCH:**
- Any security issue (API keys, permissions)
- Balance insufficient (<$1,000)
- Paper trading failed (win rate <30%)
- Critical bugs or system errors
- Monitoring not working

---

## 🚀 LAUNCH PROCEDURE

If all checks pass, follow this exact sequence:

### Step 1: Final Backup
```bash
# Backup current database (if any)
cp data/trades_mexc_live.db data/trades_mexc_live_backup_$(date +%Y%m%d_%H%M%S).db 2>/dev/null || true

# Git commit current state
git add -A
git commit -m "Pre-launch checkpoint - MEXC live trading $(date)"
git push origin claude/bot-launch-checklist-SmLAH
```

### Step 2: Environment Verification
```bash
# Final environment check
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('=== FINAL ENVIRONMENT CHECK ===')
print(f'MEXC_API_KEY: {\"✅ Set\" if os.getenv(\"MEXC_API_KEY\") else \"❌ Missing\"}')
print(f'MEXC_SECRET_KEY: {\"✅ Set\" if os.getenv(\"MEXC_SECRET_KEY\") else \"❌ Missing\"}')
print(f'TELEGRAM_BOT_TOKEN: {\"✅ Set\" if os.getenv(\"TELEGRAM_BOT_TOKEN\") else \"❌ Missing\"}')
print(f'TRADING_MODE: {os.getenv(\"TRADING_MODE\", \"NOT SET\")}')
print('===============================')
"
```

### Step 3: Launch Bot
```bash
# Start with logging to file
nohup python3 run_bot_mexc.py > logs/live_bot_$(date +%Y%m%d).log 2>&1 &

# Save PID for monitoring
echo $! > bot.pid
echo "Bot started with PID: $(cat bot.pid)"
```

### Step 4: First Hour Monitoring
```bash
# Monitor logs in real-time
tail -f logs/live_bot_$(date +%Y%m%d).log

# In another terminal, run status checks every 15 min:
watch -n 900 './monitor_live.sh'
```

### Step 5: Verify First Trade
- [ ] **Wait for first trade signal**
- [ ] **Verify trade appears on MEXC UI**
- [ ] **Check Telegram alert received**
- [ ] **Verify database entry created**
- [ ] **Confirm position sizing correct**

---

## 📞 POST-LAUNCH MONITORING SCHEDULE

### Hour 0-1: CRITICAL
- Check every **5-10 minutes**
- Verify first API calls successful
- Ensure no immediate errors
- Confirm bot is running

### Hour 1-6: HIGH ALERT
- Check every **30 minutes**
- Monitor first trades
- Verify stop losses working
- Check balance updates

### Hour 6-24: ACTIVE
- Check every **2-4 hours**
- Review P&L
- Verify strategy performance
- Check for any errors

### Day 2-7: STANDARD
- Check **2-3 times per day**
- Daily P&L review
- Weekly performance summary
- Adjust position sizes if needed

---

## 🆘 EMERGENCY CONTACTS & RESOURCES

### If Something Goes Wrong:

1. **STOP THE BOT IMMEDIATELY**
   ```bash
   touch STOP_SIGNAL
   # or
   kill $(cat bot.pid)
   ```

2. **Close all open positions on MEXC:**
   - Login to MEXC web interface
   - Go to Spot Trading → Open Orders
   - Cancel all orders
   - Sell all altcoins back to USDT manually

3. **Check logs for errors:**
   ```bash
   tail -100 logs/live_bot_$(date +%Y%m%d).log | grep -i error
   ```

4. **Review recent trades:**
   ```bash
   sqlite3 data/trades_mexc_live.db "
   SELECT * FROM trades
   ORDER BY entry_time DESC
   LIMIT 10;
   "
   ```

### MEXC Support
- **Website:** https://www.mexc.com/support
- **Telegram:** @MEXCEnglish
- **API Issues:** support@mexc.com

### Bot Support
- Check logs first: `logs/live_bot_*.log`
- Review git history: `git log --oneline`
- Rollback if needed: `git checkout <previous-commit>`

---

## ✅ FINAL SIGN-OFF

**Before launching, have you:**
- [ ] Read this entire checklist?
- [ ] Completed ALL items in sections 1-7?
- [ ] Verified you can STOP the bot if needed?
- [ ] Set up monitoring for the first 24 hours?
- [ ] Reduced position sizes from paper trading?
- [ ] Prepared for potential losses?
- [ ] Only investing what you can afford to lose?

**Sign-off (mental commitment):**
- [ ] I understand this is REAL MONEY trading
- [ ] I have reviewed all risk management settings
- [ ] I am prepared to monitor closely for 24-48 hours
- [ ] I know how to stop the bot in an emergency
- [ ] I accept that losses may occur

**Final approval:** ⬜ **I AM READY TO GO LIVE**

---

## 📊 EXPECTED FIRST 24H PERFORMANCE

Based on paper trading and strategy configuration:

**Realistic Expectations:**
- **Trades executed:** 5-15 trades (varies by market volatility)
- **Win rate:** 35-50% (lower at first, improves with data)
- **P&L:** -$20 to +$50 (high variance initially)
- **Max drawdown:** -$30 to -$50 (acceptable range)

**Red Flags (Stop bot if you see):**
- Loss >$100 in first 24h
- Win rate <20% after 10+ trades
- Same coin bought/sold repeatedly (loop bug)
- API errors every minute
- Position sizes >$200/coin (config error)

---

## 🎯 SUCCESS METRICS (Week 1)

**Green (Scale up positions):**
- Win rate ≥45%
- Net profit >$50
- No circuit breakers triggered
- Avg trade P&L >$2

**Yellow (Continue monitoring):**
- Win rate 35-45%
- Net profit -$20 to +$50
- 1-2 circuit breaker triggers
- Avg trade P&L -$1 to +$2

**Red (Reduce size or stop):**
- Win rate <35%
- Net loss >$100
- >3 circuit breaker triggers
- Avg trade P&L <-$1

---

**GOOD LUCK! 🚀**

Remember: Start small, monitor closely, scale gradually.

**Never risk more than you can afford to lose.**
