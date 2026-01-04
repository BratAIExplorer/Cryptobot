# How to Share Grid Bot Diagnostics for Analysis

## Quick Steps

### Step 1: SSH to Your VPS
```bash
ssh user@72.60.40.29
```

### Step 2: Navigate to Bot Directory
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
```

### Step 3: Copy Diagnostic Script to VPS

**Option A: Download from GitHub repo**
```bash
# If this repo is cloned on VPS
cp /path/to/Cryptobot/scripts/collect_grid_bot_diagnostics.sh .
```

**Option B: Create the script manually**
```bash
# Copy the script content from:
# scripts/collect_grid_bot_diagnostics.sh

nano collect_grid_bot_diagnostics.sh
# Paste the script content
# Save with Ctrl+X, Y, Enter

chmod +x collect_grid_bot_diagnostics.sh
```

### Step 4: Run the Diagnostic Script
```bash
bash collect_grid_bot_diagnostics.sh > grid_bot_report.txt
```

This will create a file `grid_bot_report.txt` with all diagnostic information.

### Step 5: View the Report
```bash
cat grid_bot_report.txt
```

### Step 6: Share with Me

**Option A: Copy and paste the entire output**
- Just copy the contents of `grid_bot_report.txt`
- Paste it in your next message

**Option B: Share key sections**
If the full report is too long, share these critical sections:

```bash
# Just the summary
grep -A 20 "SECTION 13: DIAGNOSTIC SUMMARY" grid_bot_report.txt

# Plus Section 4 (trades last 24h)
grep -A 15 "SECTION 4: GRID BOT TRADES (LAST 24 HOURS)" grid_bot_report.txt

# Plus Section 3 (bot status)
grep -A 10 "SECTION 3: REGISTERED BOTS" grid_bot_report.txt
```

---

## What I'll Analyze

Once you share the output, I will analyze:

### 1. **Trading Activity Status**
- ✅ Is Grid Bot actively trading?
- ⏰ When was the last trade?
- 📊 Trade frequency (vs expected 10-50 trades/day)

### 2. **Configuration Issues**
- 🎯 Is price within grid range?
  - BTC Grid: $88,000 - $108,000
  - ETH Grid: $2,800 - $3,600
- ⚙️ Are grid bots properly registered?
- 🔧 Configuration errors in run_bot.py?

### 3. **Performance Analysis**
- 💰 P&L vs expected (+$50-$150/day for BTC)
- 🎯 Win rate (should be 85-95%)
- 📈 Trade profitability
- ⚖️ Open positions status

### 4. **Error Detection**
- 🔴 Circuit breaker triggered?
- ❌ Recent errors in logs?
- 🛑 Service stopped unexpectedly?
- 🔌 Exchange API issues?

### 5. **Specific Recommendations**
Based on the diagnostics, I'll provide:
- ✅ Specific fixes for identified issues
- 🎯 Grid range adjustments if needed
- ⚙️ Configuration changes
- 🔄 Restart procedures
- 📊 Performance optimization tips

---

## Alternative: Quick Manual Check

If you can't run the full script, you can manually run these key queries:

### Check 1: Last Trade Time
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot

sqlite3 data/trades_v3_paper.db \
  "SELECT MAX(timestamp) as last_trade FROM trades WHERE strategy LIKE '%Grid%';"
```

**Share this output with me.**

### Check 2: Trades in Last 24 Hours
```bash
sqlite3 data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    COUNT(*) as trades_24h,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    MAX(timestamp) as last_trade
FROM trades
WHERE strategy LIKE '%Grid%'
  AND timestamp > datetime('now', '-24 hours')
GROUP BY strategy;
EOF
```

**Share this output with me.**

### Check 3: Bot Status
```bash
sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    status,
    total_trades,
    ROUND(total_pnl, 2) as pnl,
    last_heartbeat
FROM bot_status
WHERE strategy LIKE '%Grid%';
EOF
```

**Share this output with me.**

### Check 4: Current Prices (for grid range check)
```bash
sqlite3 data/trades_v3_paper.db << 'EOF'
SELECT
    symbol,
    ROUND(price, 2) as last_price,
    timestamp as price_time
FROM trades
WHERE symbol IN ('BTC/USDT', 'ETH/USDT')
  AND timestamp = (
      SELECT MAX(timestamp)
      FROM trades t2
      WHERE t2.symbol = trades.symbol
  );
EOF
```

**Share this output with me.**

---

## What Results Look Like

### ✅ Healthy Grid Bot Example:
```
Last Grid Bot Trade: 2026-01-03 14:23:45
Hours Since Last Trade: 1 hours
✅ Recent trading activity (within last 6 hours)

--- Quick Stats ---
Total Grid Bot Trades (All Time): 387
Grid Bot Trades (Last 24h): 34
Registered Grid Bots: 2
Open Positions: 3
```

### ⚠️ Problem Grid Bot Example:
```
Last Grid Bot Trade: 2026-01-02 02:15:33
Hours Since Last Trade: 36 hours
⚠️  WARNING: No Grid Bot trades in 36 hours!

--- Quick Stats ---
Total Grid Bot Trades (All Time): 12
Grid Bot Trades (Last 24h): 0
Registered Grid Bots: 0  ← PROBLEM!
Open Positions: 0
```

---

## Common Issues I Can Help With

### Issue 1: Zero Trades
**Symptoms:**
- Trades (Last 24h): 0
- Last trade: > 12 hours ago

**I'll check:**
- Is price outside grid range?
- Is bot service running?
- Configuration errors?
- Market volatility too low?

### Issue 2: No Bots Registered
**Symptoms:**
- Registered Grid Bots: 0
- Bot status table empty

**I'll check:**
- run_bot.py configuration
- Service startup errors
- Database connectivity

### Issue 3: Poor Performance
**Symptoms:**
- P&L negative or low
- Win rate < 70%
- Trades but losing money

**I'll check:**
- Grid level spacing
- Fee impact
- Grid range vs current price
- Market conditions

### Issue 4: Stopped Trading
**Symptoms:**
- Was trading, now stopped
- Last trade hours/days ago

**I'll check:**
- Circuit breaker triggered?
- Service crashed?
- Database locked?
- Exchange API issues?

---

## Ready to Analyze!

Once you run the diagnostic script and share the output, I'll provide:

1. **Root Cause Analysis** - What exactly is wrong
2. **Impact Assessment** - How serious is the issue
3. **Step-by-Step Fix** - Exact commands to run
4. **Verification Steps** - How to confirm it's fixed
5. **Prevention Tips** - How to avoid it in future

Just paste the output and I'll take care of the rest! 🔍
