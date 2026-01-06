# MEXC API Key Fix Guide

## 🎯 GOOD NEWS: BTC/ETH Are Active on MEXC!

Your screenshots confirm BTC/USDT and ETH/USDT are **actively trading** on MEXC with massive volume:
- **BTC/USDT**: 1.22B USDT/24h volume
- **ETH/USDT**: 740M USDT/24h volume

## 🔍 The Real Problem: API Key Permissions

The error `"symbol not support api" (code 10007)` is **NOT** because markets are inactive.

It's because your API key likely has **"Read Only"** permission instead of **"Spot Trading"** permission.

### Why Paper Trading Worked But Live Trading Failed

| Action | Permission Needed | Status |
|--------|------------------|--------|
| Fetch prices (fetch_ticker) | Read Only | ✅ Works |
| Fetch balance | Read Only | ✅ Works |
| **Place orders (create_order)** | **Spot Trading** | ❌ **Missing** |

This explains why:
- ✅ Paper bot worked (only reads prices)
- ❌ Live bot failed (tries to place orders)

## 🔧 The Fix: Regenerate API Keys with Correct Permissions

### Step 1: Delete Current API Key

1. Go to: https://www.mexc.com/user/openapi
2. Find your current API key
3. Click "Delete"

### Step 2: Create NEW API Key with Trading Permission

Click "Create API Key" and configure:

```
✅ Read              ← REQUIRED for data access
✅ Spot Trading      ← REQUIRED for order placement
❌ Futures           ← NOT needed
❌ Withdraw          ← NOT needed (dangerous)
```

**IP Whitelist (Recommended):**
- Add your server IP for extra security
- Or leave blank for testing (less secure)

### Step 3: Save New API Credentials

You'll receive:
- **API Key**: `mx0vglX...` (long string)
- **Secret Key**: `8f7e3...` (long string)

**⚠️ CRITICAL: Copy the secret immediately - it's only shown once!**

### Step 4: Update .env File

```bash
# Run setup helper
./setup_api_keys.sh

# OR manually edit .env
nano .env
```

Update these lines:
```bash
MEXC_API_KEY=your_new_api_key_here
MEXC_SECRET=your_new_secret_here
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Load Environment Variables

```bash
# Export variables to current session
export $(cat .env | grep -v '^#' | xargs)

# Verify they're loaded
echo $MEXC_API_KEY
```

### Step 6: Run Diagnostic

```bash
python3 diagnose_mexc_api.py
```

**Expected output if fixed:**
```
✅ Account access works
✅ Can query orders
✅ ORDER CREATION WORKS!
🎉 SUCCESS! Your API keys have FULL TRADING permissions!
```

### Step 7: Launch Live Trading

Once diagnostic passes:

```bash
python3 run_bot_mexc_SAFE_LIVE.py
```

## 🚨 If Diagnostic Still Fails

### Error: "Account verification required"

**Solution:** Complete KYC verification
1. Go to MEXC → Account → Verification
2. Complete identity verification
3. Wait for approval (usually 5-30 minutes)
4. Try again

### Error: "IP not whitelisted"

**Solution:** Update IP whitelist
1. Go to MEXC → API Management
2. Click "Edit" on your API key
3. Add your server IP or remove IP restriction
4. Save and try again

### Error: "Insufficient balance"

**Good news!** This means API has permission but account needs funds.
- Check your USDT balance on MEXC
- Transfer funds if needed

## 📊 Quick Reference

| Issue | Cause | Fix |
|-------|-------|-----|
| Markets "inactive" | ❌ False alarm | Markets ARE active |
| "symbol not support api" | API key = Read Only | Recreate with Spot Trading |
| Paper trading works | Read permission OK | Need Spot Trading permission |
| Live trading fails | Missing Spot permission | Regenerate API key |

## ✅ Verification Checklist

Before going live, confirm:

- [ ] API key created with "Spot Trading" permission
- [ ] .env file updated with new keys
- [ ] Environment variables loaded (`echo $MEXC_API_KEY` shows key)
- [ ] Diagnostic script passes all tests
- [ ] Test order successfully created and canceled
- [ ] Account has sufficient USDT balance ($218+)
- [ ] Telegram alerts configured (optional but recommended)

## 🎯 Expected Timeline

- **Recreate API keys**: 2 minutes
- **Update .env**: 1 minute
- **Run diagnostic**: 1 minute
- **Launch live bot**: 30 seconds

**Total: ~5 minutes to fix and launch**

---

## 🚀 Bottom Line

**You DON'T need to:**
- ❌ Switch to Binance
- ❌ Use SOL/XRP instead of BTC/ETH
- ❌ Change your strategy

**You DO need to:**
- ✅ Regenerate API key with "Spot Trading" permission
- ✅ Update .env file
- ✅ Run diagnostic to confirm
- ✅ Launch your BTC/ETH grid bots as planned

**BTC/USDT and ETH/USDT work perfectly on MEXC - your original plan was correct!**
