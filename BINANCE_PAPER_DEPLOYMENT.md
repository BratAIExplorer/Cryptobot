# Binance Paper Trading Bot - Deployment Guide

## ✅ Phase 3 Complete: Code Adaptation

The Binance paper trading bot has been successfully created by systematically converting the tested MEXC bot while preserving all safety features.

---

## 📋 What Was Changed

### Source File
- **From:** `run_bot_mexc_SAFE_LIVE.py` (tested MEXC bot)
- **To:** `run_bot_binance_SAFE_PAPER.py` (new Binance testnet bot)

### Systematic Conversions

| Component | MEXC (Old) | Binance (New) |
|-----------|------------|---------------|
| **Exchange** | `EXCHANGE = 'MEXC'` | `EXCHANGE = 'binance'` |
| **Trading Mode** | `TRADING_MODE = 'live'` | `TRADING_MODE = 'paper'` |
| **Sandbox** | Not used | `SANDBOX_MODE = True` |
| **Database** | `trades_mexc_live.db` | `trades_binance_paper.db` |
| **Environment** | `.env` | `.env.binance.paper` |
| **API Keys** | `MEXC_API_KEY`, `MEXC_SECRET` | `BINANCE_API_KEY`, `BINANCE_SECRET` |
| **BTC Bot Name** | `MEXC_Grid_BTC_Live` | `Binance_Grid_BTC_Paper` |
| **ETH Bot Name** | `MEXC_Grid_ETH_Live` | `Binance_Grid_ETH_Paper` |
| **Notifications** | 🔴 LIVE | 📝 PAPER |

### Preserved Safety Features ✅

All tested MEXC features were preserved:
- ✅ Capital Controller with strict per-bot limits
- ✅ Daily loss limit ($50)
- ✅ LiveTradingNotifier with mode-aware alerts
- ✅ Emergency stop signal (STOP_SIGNAL file)
- ✅ Pre-launch environment verification
- ✅ 10-second abort window
- ✅ Grid Bot configuration (same parameters)
- ✅ Capital recycling logic

### New Binance-Specific Features

1. **Sandbox Mode Enablement**
   ```python
   SANDBOX_MODE = True  # Use Binance testnet

   # In verify_environment():
   binance.set_sandbox_mode(True)

   # In main():
   if SANDBOX_MODE and hasattr(engine.exchange, 'set_sandbox_mode'):
       engine.exchange.set_sandbox_mode(True)
   ```

2. **Testnet Environment Loading**
   ```python
   load_dotenv('.env.binance.paper')
   ```

3. **Mode-Aware Notifications**
   ```python
   notifier = LiveTradingNotifier(
       token=telegram_config['token'],
       chat_id=telegram_config['chat_id'],
       mode='paper'  # Adds 📝 PAPER prefix to all alerts
   )
   ```

---

## 🚀 Deployment Steps

### Step 1: Verify .env.binance.paper Configuration

Ensure your `.env.binance.paper` file exists and contains:

```bash
# Binance TESTNET API Keys (from testnet.binance.vision)
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET=your_testnet_secret_here

# Telegram (same as MEXC for consistency)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Trading mode
TRADING_MODE=paper
```

**CRITICAL:** These must be TESTNET API keys from https://testnet.binance.vision/, NOT live Binance keys!

### Step 2: Pre-Launch Verification

Run the Binance testnet verification script:

```bash
cd /home/user/Cryptobot
python3 verify_binance_paper.py
```

**Expected Output:**
```
✅ Paper API Key: eWG8WCLNoH...rJkq
✅ Connected to Binance Testnet (Paper Trading)
✅ Can read testnet balance
✅ BTC/USDT: Active
✅ ETH/USDT: Active
✅ Testnet order works
🎉 TESTNET ORDER WORKS!
✅ BINANCE PAPER API VERIFICATION COMPLETE!
```

### Step 3: Launch Paper Trading Bot

```bash
cd /home/user/Cryptobot
python3 run_bot_binance_SAFE_PAPER.py
```

**You will see:**
1. Pre-launch environment verification (API check, markets check, Telegram test)
2. 10-second abort window (Ctrl+C to cancel)
3. Grid bot initialization (BTC $80 + ETH $60)
4. Continuous monitoring loop

### Step 4: Monitor Paper Trading

**Check Bot Status:**
```bash
# View real-time logs
tail -f logs/live_*.log

# Check database
sqlite3 data/trades_binance_paper.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# Check if bot is running
ps aux | grep run_bot_binance

# View bot PID
cat bot.pid
```

**Check Telegram:**
- You should receive a startup notification: "📝 PAPER BOT - Pre-launch test successful!"
- All trading alerts will have "📝 PAPER" prefix
- Messages will include "(Testnet - fake money)"

### Step 5: Emergency Stop (If Needed)

**Method 1:** Create stop signal file
```bash
touch STOP_SIGNAL
```

**Method 2:** Graceful shutdown
```bash
# Press Ctrl+C in the terminal running the bot
```

**Method 3:** Kill by PID
```bash
kill $(cat bot.pid)
```

---

## 🎯 Success Criteria

Paper trading test should run for **2-4 hours** successfully:

### ✅ Must Pass:
- [ ] Bot starts without errors
- [ ] Binance testnet connection successful
- [ ] Grid orders calculated correctly
- [ ] Telegram notifications working with 📝 PAPER prefix
- [ ] Capital limits enforced
- [ ] No real money used (testnet only)
- [ ] Database records trades correctly
- [ ] Emergency stop works

### 📊 Expected Behavior:
- Grid levels calculated around current BTC/ETH prices
- Orders placed on testnet (fake money)
- Price monitoring every 60 seconds
- Telegram alerts for bot launch and any fills
- Capital allocation: BTC $80, ETH $60, Reserve $78.08

---

## 🔍 Troubleshooting

### Error: "Invalid Api-Key ID" (-2008)
**Cause:** Using live Binance API key instead of testnet key
**Fix:** Generate new API key at https://testnet.binance.vision/

### Error: "Insufficient Funds"
**Cause:** Testnet account empty
**Fix:** Visit https://testnet.binance.vision/ and use the faucet to get free testnet USDT

### Error: "BTC/USDT not active"
**Cause:** Not connected to testnet properly
**Fix:** Verify `set_sandbox_mode(True)` is being called (check logs)

### Error: "Cannot read balance"
**Cause:** API key permissions issue
**Fix:** Ensure testnet API key has "Spot Trading" enabled

---

## 📈 Next Steps After Successful Paper Test

### Phase 4: Small Live Test ($30)
1. Create `.env.binance.live` with LIVE Binance API keys
2. Copy `run_bot_binance_SAFE_PAPER.py` → `run_bot_binance_SAFE_SMALL.py`
3. Change to `TRADING_MODE = 'live'`, `SANDBOX_MODE = False`
4. Reduce allocations: BTC $15, ETH $15
5. Run for 24 hours

### Phase 5: Full Deployment ($140)
1. Transfer remaining funds from MEXC to Binance
2. Update allocations to full amounts (BTC $80, ETH $60)
3. Deploy with 24/7 monitoring
4. Gradual transition from MEXC to Binance

---

## 🔐 Safety Reminders

### Paper Trading (Current Phase)
- ✅ Uses Binance TESTNET
- ✅ Fake money only
- ✅ Zero financial risk
- ✅ Safe to test all features
- ✅ Can test emergency stops

### Live Trading (Future Phases)
- ⚠️ Uses real money
- ⚠️ Requires LIVE API keys
- ⚠️ Financial risk involved
- ⚠️ Start with small amounts
- ⚠️ Monitor continuously

---

## 📝 File Summary

### New Files Created
- `run_bot_binance_SAFE_PAPER.py` - Binance paper trading bot (343 lines)

### Configuration Files Needed
- `.env.binance.paper` - Testnet API keys and config

### Related Documentation
- `MEXC_TO_BINANCE_MIGRATION.md` - Full migration plan
- `verify_binance_paper.py` - Testnet verification script
- `verify_binance_api.py` - Live API verification (Phase 4)

---

## ✅ Completion Checklist

Before launching:
- [ ] `.env.binance.paper` configured with testnet keys
- [ ] `verify_binance_paper.py` passed all tests
- [ ] Telegram bot token configured
- [ ] Understand emergency stop procedures
- [ ] Know it's using FAKE MONEY on testnet

During paper test:
- [ ] Monitor logs for errors
- [ ] Check Telegram for 📝 PAPER alerts
- [ ] Verify grid calculations are correct
- [ ] Test emergency stop once
- [ ] Run for minimum 2 hours

After successful paper test:
- [ ] Review trade logs
- [ ] Verify capital limits worked
- [ ] Check no unexpected behavior
- [ ] Document any issues found
- [ ] Get ready for Phase 4 (small live test)

---

## 🎉 Ready to Launch!

Your Binance paper trading bot is ready for testing. This is a risk-free testnet environment where you can validate all functionality before committing real funds.

**Launch command:**
```bash
python3 run_bot_binance_SAFE_PAPER.py
```

Good luck! 🚀📝
