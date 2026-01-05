# 💰 Capital Recycling & Launch Roadmap

## ❓ YOUR QUESTION: How Do Bots Reuse Funds After Selling?

**Short Answer:** The `CapitalController` automatically tracks and releases capital when positions are closed (sold), making it available for new trades.

---

## 🔄 CAPITAL RECYCLING MECHANISM

### How It Works

```
INITIAL STATE:
- Bot allocated: $80
- Available: $80
- In use: $0

AFTER BUY (BTC at $93,700):
- Bot allocated: $80
- Available: $0
- In use: $80 (open position)

AFTER SELL (BTC at $94,800):
- Bot allocated: $80
- Available: $80 (✅ capital released!)
- In use: $0
- Profit: +$1,100 (added to available capital)
```

### Implementation in Code

In `core/capital_controller.py`:

```python
def record_trade(self, bot_name, trade_amount, side):
    if side == 'BUY':
        # Lock capital
        self.bot_spent[bot_name] += trade_amount

    elif side == 'SELL':
        # Release capital (automatically available for re-use)
        self.bot_spent[bot_name] -= trade_amount  # ✅ FREED!
```

**This happens automatically on every sell!**

---

## ✅ CAPITAL RECYCLING FEATURES

### 1. Automatic Release on Sell
```python
# When bot sells BTC:
# 1. Position closed in database
# 2. Capital controller updated (SELL recorded)
# 3. Capital immediately available for next trade
# 4. No manual intervention needed
```

### 2. Real-Time Tracking
```python
# Capital controller syncs with database
capital_controller.enforce_sync_with_database()

# This ensures accuracy even after bot restart
# Reads actual open positions from database
# Updates bot_spent accordingly
```

### 3. Grid Bot Capital Efficiency
Grid bots are **especially efficient** at capital recycling:

```
Grid Example ($80 allocated for BTC):
- Buy at $93,000 ($40 used) → Available: $40
- Buy at $92,500 ($40 used) → Available: $0
- Sell at $93,500 ($40 freed) → Available: $40 ✅
- Buy at $92,000 ($40 used) → Available: $0
- Sell at $93,000 ($40 freed) → Available: $40 ✅
```

**Result:** Same $80 generates 5+ trades/day through recycling!

---

## 🧪 HOW TO TEST CAPITAL RECYCLING

### Test Script

Create `test_capital_recycling.py`:

```python
#!/usr/bin/env python3
"""
Test Capital Recycling Mechanism
Simulates buy/sell cycle to verify capital release
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.capital_controller import CapitalController
from core.logger import TradeLogger

def test_recycling():
    logger = TradeLogger(db_path='data/test_capital.db')
    controller = CapitalController(logger)

    # Setup
    controller.set_bot_allocation('Test_Grid_BTC', 100)

    print("=" * 60)
    print("CAPITAL RECYCLING TEST")
    print("=" * 60)

    # Initial state
    print(f"\n1. Initial State:")
    print(f"   Allocated: ${controller.bot_allocations['Test_Grid_BTC']:.2f}")
    print(f"   Available: ${controller.get_available_capital('Test_Grid_BTC'):.2f}")

    # Simulate BUY
    allowed, reason = controller.check_trade_allowed('Test_Grid_BTC', 50, 'BTC/USDT')
    print(f"\n2. Check BUY $50 allowed: {allowed}")

    if allowed:
        controller.record_trade('Test_Grid_BTC', 50, 'BUY')
        print(f"   ✅ BUY recorded")
        print(f"   Available after buy: ${controller.get_available_capital('Test_Grid_BTC'):.2f}")

    # Try another BUY
    allowed, reason = controller.check_trade_allowed('Test_Grid_BTC', 50, 'BTC/USDT')
    print(f"\n3. Check another BUY $50 allowed: {allowed}")

    if allowed:
        controller.record_trade('Test_Grid_BTC', 50, 'BUY')
        print(f"   ✅ Second BUY recorded")
        print(f"   Available after 2nd buy: ${controller.get_available_capital('Test_Grid_BTC'):.2f}")

    # Try third BUY (should fail - no capital)
    allowed, reason = controller.check_trade_allowed('Test_Grid_BTC', 50, 'BTC/USDT')
    print(f"\n4. Check third BUY $50 allowed: {allowed}")
    if not allowed:
        print(f"   ❌ Blocked: {reason}")

    # Simulate SELL (release capital)
    print(f"\n5. SELL first position ($50):")
    controller.record_trade('Test_Grid_BTC', 50, 'SELL')
    print(f"   ✅ SELL recorded")
    print(f"   Available after sell: ${controller.get_available_capital('Test_Grid_BTC'):.2f}")

    # Try BUY again (should work now)
    allowed, reason = controller.check_trade_allowed('Test_Grid_BTC', 50, 'BTC/USDT')
    print(f"\n6. Check BUY $50 after sell: {allowed}")
    if allowed:
        print(f"   ✅ Capital recycling works!")

    print("\n" + "=" * 60)
    print("✅ CAPITAL RECYCLING TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_recycling()
```

**Run this before going live:**
```bash
python3 test_capital_recycling.py
```

**Expected output:**
```
1. Initial State:
   Allocated: $100.00
   Available: $100.00

2. Check BUY $50 allowed: True
   ✅ BUY recorded
   Available after buy: $50.00

3. Check another BUY $50 allowed: True
   ✅ Second BUY recorded
   Available after 2nd buy: $0.00

4. Check third BUY $50 allowed: False
   ❌ Blocked: Exceeds allocation

5. SELL first position ($50):
   ✅ SELL recorded
   Available after sell: $50.00

6. Check BUY $50 after sell: True
   ✅ Capital recycling works!
```

---

## 🚀 YOUR NEXT STEPS (COMPLETE LAUNCH ROADMAP)

### PHASE 0: PREPARATION (Do this on VPS)

#### Step 1: Pull Latest Code
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE
git pull origin claude/bot-launch-checklist-SmLAH
```

#### Step 2: Test Capital Recycling
```bash
# Run the test script (will be created next)
python3 test_capital_recycling.py

# Should show capital releases properly
```

#### Step 3: Test Telegram Alerts
```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

from core.notifier_live import LiveTradingNotifier

# Test LIVE mode notifier
notifier = LiveTradingNotifier(
    token=os.getenv('TELEGRAM_BOT_TOKEN'),
    chat_id=os.getenv('TELEGRAM_CHAT_ID'),
    mode='live'
)

# Send test alerts
notifier.send_message("Testing LIVE notifier")
notifier.notify_trade('BTC/USDT', 'BUY', 93700, 0.001, 'Test')

print("✅ Check your Telegram for LIVE prefix")
EOF
```

#### Step 4: Test Dashboard
```bash
# Install streamlit if not already
pip install streamlit

# Launch dashboard (separate terminal)
streamlit run dashboard_mexc_live.py --server.port 8501

# Access: http://your-vps-ip:8501
# Or tunnel: ssh -L 8501:localhost:8501 root@srv1010193
```

---

### PHASE 1: DRY-RUN TEST (5-10 minutes)

Before going live with real money, do a quick dry-run:

```bash
# 1. Modify run_bot_mexc_SAFE_LIVE.py temporarily
# Change line 30:
TRADING_MODE = 'paper'  # Test run first!

# 2. Run for 5 minutes
python3 run_bot_mexc_SAFE_LIVE.py

# 3. Verify:
# - Telegram alerts show "🔴 LIVE" prefix (even in paper mode)
# - Capital controller logs show tracking
# - Dashboard loads with data
# - No errors in console

# 4. Stop with Ctrl+C

# 5. Revert to LIVE mode
TRADING_MODE = 'live'
```

---

### PHASE 2: LIVE LAUNCH (THE REAL DEAL)

#### Pre-Launch Checklist
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot_LIVE

# ✅ 1. Environment configured
cat .env | grep -E "MEXC|TELEGRAM"

# ✅ 2. Balance verified
python3 -c "import ccxt,os; from dotenv import load_dotenv; load_dotenv(); m=ccxt.mexc({'apiKey':os.getenv('MEXC_API_KEY'),'secret':os.getenv('MEXC_SECRET')}); print(f'Balance: ${m.fetch_balance()[\"USDT\"][\"total\"]:.2f}')"

# ✅ 3. Telegram working
# (should have received test messages)

# ✅ 4. Dashboard accessible
# http://your-vps-ip:8501

# ✅ 5. Capital recycling tested
# (test script passed)

# ✅ 6. You're mentally prepared
echo "I understand this is REAL MONEY trading"
```

#### Launch Command
```bash
# Create logs directory
mkdir -p logs

# Launch bot
nohup python3 run_bot_mexc_SAFE_LIVE.py > logs/live_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Save PID
echo $! > bot.pid
echo "Bot PID: $(cat bot.pid)"

# Monitor live
tail -f logs/live_*.log
```

---

### PHASE 3: FIRST HOUR MONITORING (CRITICAL!)

#### Minute 0-15: Startup Verification
```bash
# Check every 2-3 minutes:

# 1. Bot still running?
ps aux | grep run_bot_mexc_SAFE_LIVE

# 2. Any errors?
tail -50 logs/live_*.log | grep -i error

# 3. Telegram startup received?
# Should see: "🔴 LIVE Bot Started"

# 4. Dashboard loading?
# http://your-vps-ip:8501
```

#### Minute 15-60: First Trades
```bash
# Check every 10-15 minutes:

# 1. Run status monitor
./monitor_mexc_live.sh

# 2. Check dashboard for trades
# Should see 1-3 grid orders placed

# 3. Verify Telegram alerts
# Each trade should send "🔴 LIVE BUY/SELL"

# 4. Capital tracking
tail -100 logs/live_*.log | grep "Capital Control"
```

**Expected behavior (first hour):**
- ✅ 2-4 grid orders placed (BTC + ETH)
- ✅ Telegram alerts with 🔴 LIVE prefix
- ✅ Dashboard shows open positions
- ✅ No errors in logs
- ✅ Capital controller tracks properly

---

### PHASE 4: FIRST 24 HOURS (Active Monitoring)

#### Check every 2-4 hours:

```bash
# Quick status
./monitor_mexc_live.sh

# Expected progress:
# - Hour 6: 5-10 trades
# - Hour 12: 10-20 trades
# - Hour 24: 15-30 trades
# - P&L: -$5 to +$15 (volatile at first)
```

#### Red Flags (STOP BOT if you see):
```bash
# 1. Same coin bought 5+ times without selling
grep "BUY BTC" logs/live_*.log | tail -20

# 2. Loss > $30 in 24h
sqlite3 data/trades_mexc_live.db "
SELECT SUM(unrealized_pnl_usd) FROM positions
WHERE status='CLOSED' AND exit_time > datetime('now', '-24 hours');
"

# 3. Capital exceeded (should never happen with controls)
tail -100 logs/live_*.log | grep "CAPITAL LIMIT BREACH"

# 4. Circuit breaker triggered
tail -100 logs/live_*.log | grep "CIRCUIT BREAKER"
```

#### Emergency Stop:
```bash
# If ANY red flag:
touch STOP_SIGNAL
# or
kill $(cat bot.pid)

# Then investigate before restarting
```

---

### PHASE 5: WEEK 1 REVIEW (Day 7)

#### Performance Analysis
```bash
# Generate week 1 report
sqlite3 data/trades_mexc_live.db << 'EOF'
SELECT
    'Total Trades' as metric, COUNT(*) as value FROM trades
UNION ALL
SELECT 'Win Rate %',
    ROUND(100.0 * SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM positions WHERE status='CLOSED'
UNION ALL
SELECT 'Total P&L $', ROUND(SUM(unrealized_pnl_usd), 2)
FROM positions WHERE status='CLOSED'
UNION ALL
SELECT 'Best Day $', MAX(daily_pnl) FROM (
    SELECT DATE(exit_time) as date, SUM(unrealized_pnl_usd) as daily_pnl
    FROM positions WHERE status='CLOSED'
    GROUP BY DATE(exit_time)
)
UNION ALL
SELECT 'Worst Day $', MIN(daily_pnl) FROM (
    SELECT DATE(exit_time) as date, SUM(unrealized_pnl_usd) as daily_pnl
    FROM positions WHERE status='CLOSED'
    GROUP BY DATE(exit_time)
);
EOF
```

#### GO/NO-GO Decision for Phase 2

**✅ GREEN - Expand to Phase 2:**
- Total P&L: +$15 to +$50
- Win Rate: >40%
- No circuit breakers
- Max daily loss: <$20
- **Action:** Add Buy-the-Dip strategy ($50 allocation)

**⚠️ YELLOW - Continue Phase 1:**
- Total P&L: -$10 to +$15
- Win Rate: 35-40%
- 1-2 circuit breakers
- Max daily loss: $20-30
- **Action:** Continue with grid bots only for another week

**❌ RED - Reduce or Stop:**
- Total P&L: <-$30
- Win Rate: <35%
- >3 circuit breakers
- Max daily loss: >$30
- **Action:** Reduce position sizes 50% or stop and debug

---

### PHASE 6: EXPANSION (Week 2+)

#### If Week 1 Successful:

**Option A: Add Buy-the-Dip (Keep $218 USDT)**
```python
# Modify run_bot_mexc_SAFE_LIVE.py
ALLOCATIONS = {
    'MEXC_Grid_BTC_Live': 70,   # Reduce from $80
    'MEXC_Grid_ETH_Live': 50,   # Reduce from $60
    'MEXC_Buy_Dip_Live': 40,    # NEW! (2 coins at $20 each)
}
# Total: $160, Reserve: $58
```

**Option B: Convert XRP → Scale Portfolio**
```python
# Sell 479 XRP on MEXC → ~$500
# New balance: ~$718 USDT

ALLOCATIONS = {
    'MEXC_Grid_BTC_Live': 250,
    'MEXC_Grid_ETH_Live': 200,
    'MEXC_Buy_Dip_Live': 150,
    'MEXC_SMA_Trend_Live': 100,
}
# Total: $700, Reserve: $18
```

---

## 📊 CAPITAL EFFICIENCY METRICS

### What to Track

```bash
# 1. Capital Utilization
# How much of allocated capital is actively deployed?
# Target: 60-80% (grid bots cycle frequently)

# 2. Capital Velocity
# How many trades per $100 allocated per day?
# Target: 2-4 trades/$100/day

# 3. Return on Allocated Capital (ROAC)
# Weekly profit / allocated capital
# Target: 5-10% weekly

# Example for Week 1:
# Allocated: $140
# Profit: $20
# ROAC: 20/140 = 14.3% ✅ Excellent!
```

---

## 🎯 SUCCESS CRITERIA SUMMARY

### Technical Success:
- ✅ Capital recycling works (test passed)
- ✅ Telegram LIVE alerts functioning
- ✅ Dashboard accessible and updating
- ✅ Capital controls enforced
- ✅ No bot crashes for 24h

### Financial Success (Week 1):
- ✅ Total profit: >$15
- ✅ Win rate: >40%
- ✅ Max daily loss: <$20
- ✅ Max drawdown: <15%

### Operational Success:
- ✅ You can monitor remotely
- ✅ Emergency stop works when tested
- ✅ You understand how to read dashboard
- ✅ You're comfortable with live trading

---

## 🆘 SUPPORT RESOURCES

### If Something Goes Wrong:

**1. Bot not recycling capital:**
```bash
# Force sync with database
python3 << 'EOF'
from core.capital_controller import CapitalController
from core.logger import TradeLogger

logger = TradeLogger(db_path='data/trades_mexc_live.db')
controller = CapitalController(logger)

# Set allocations
controller.set_bot_allocation('MEXC_Grid_BTC_Live', 80)
controller.set_bot_allocation('MEXC_Grid_ETH_Live', 60)

# Force sync from database
controller.enforce_sync_with_database()

# Check status
controller.print_summary()
EOF
```

**2. Telegram alerts not working:**
```bash
# Re-test connection
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = f'https://api.telegram.org/bot{os.getenv(\"TELEGRAM_BOT_TOKEN\")}/sendMessage'
requests.post(url, json={'chat_id': os.getenv('TELEGRAM_CHAT_ID'), 'text': 'Test'})
"
```

**3. Dashboard not loading:**
```bash
# Check streamlit is running
ps aux | grep streamlit

# Restart dashboard
pkill -f streamlit
streamlit run dashboard_mexc_live.py --server.port 8501 &
```

**4. Capital tracking incorrect:**
```bash
# Reset and sync
# Manually query database to verify open positions match capital tracking
sqlite3 data/trades_mexc_live.db "
SELECT bot_id, SUM(position_size_usd) as capital_used
FROM positions WHERE status='OPEN' GROUP BY bot_id;
"
```

---

## ✅ FINAL PRE-LAUNCH CONFIRMATION

Before you run `python3 run_bot_mexc_SAFE_LIVE.py`, confirm:

- [x] I understand capital recycling (capital released on SELL)
- [x] I tested capital recycling script (passed)
- [x] I tested Telegram LIVE alerts (received with 🔴 prefix)
- [x] I can access dashboard (http://vps-ip:8501)
- [x] I know how to stop bot (touch STOP_SIGNAL)
- [x] I'm prepared to monitor for 24 hours
- [x] I accept potential -$20 to +$30 variance in first week
- [x] I have the monitoring script ready (./monitor_mexc_live.sh)

**When ALL checked → You're ready to launch!**

---

**NEXT:** Create the capital recycling test script and run it to verify everything works.
