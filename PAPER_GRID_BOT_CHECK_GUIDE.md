# Paper Trading Grid Bot Performance Check

**Purpose:** Check Grid Bot performance in Paper Trading mode on your VPS

---

## Quick Check Commands (Run on VPS)

### 1. Check Paper Bot Service Status
```bash
sudo systemctl status cryptobot
# or
sudo systemctl status cryptobot_paper
```

### 2. Check Grid Bot Trades (Last 24 Hours)
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot

sqlite3 data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    ROUND(SUM(cost), 2) as total_volume,
    MAX(timestamp) as last_trade
FROM trades
WHERE strategy LIKE '%Grid%'
  AND timestamp > datetime('now', '-24 hours')
GROUP BY strategy;
EOF
```

### 3. Check Grid Bot Status
```bash
sqlite3 data/trades_v3_paper.db << 'EOF'
SELECT
    strategy,
    status,
    total_trades,
    ROUND(total_pnl, 2) as total_pnl,
    ROUND(wallet_balance, 2) as balance,
    last_heartbeat
FROM bot_status
WHERE strategy LIKE '%Grid%';
EOF
```

### 4. Check Last 10 Grid Bot Trades
```bash
sqlite3 -header -column data/trades_v3_paper.db << 'EOF'
SELECT
    datetime(timestamp) as time,
    strategy,
    symbol,
    side,
    ROUND(price, 2) as price,
    ROUND(cost, 2) as cost
FROM trades
WHERE strategy LIKE '%Grid%'
ORDER BY timestamp DESC
LIMIT 10;
EOF
```

### 5. Run Comprehensive Analysis Script
```bash
# Copy the script to VPS
cd /Antigravity/antigravity/scratch/crypto_trading_bot

# Run the analysis
python3 /path/to/analyze_paper_grid_bot.py
```

---

## What to Look For

### ✅ Healthy Grid Bot (Expected)
```
Total Trades (24h): 10-50 trades
Last Trade: < 2 hours ago
Status: RUNNING
P&L: Positive small profits accumulating
```

### ⚠️ Warning Signs
```
Total Trades (24h): 0-2 trades
Last Trade: > 12 hours ago
Status: STOPPED or ERROR
P&L: Large negative values
```

### ❌ Critical Issues
```
Total Trades (24h): 0
Last Trade: N/A or > 24 hours ago
Status: Not found in bot_status
Database: Empty or missing
```

---

## Common Issues & Solutions

### Issue 1: Zero Trades in Last 24 Hours

**Possible Causes:**
1. Price is outside grid range (lower_limit to upper_limit)
2. Market is too stable (not enough volatility)
3. Grid Bot not running
4. Exchange API issues

**Solutions:**
```bash
# Check if bot is running
ps aux | grep run_bot.py

# Check grid configuration vs current price
# For BTC Grid Bot:
# - Lower Limit: $88,000
# - Upper Limit: $108,000
# - Current BTC price should be between these values

# Check logs for errors
tail -n 100 logs/bot_systemd.log | grep -i "grid\|error"
```

### Issue 2: Grid Bot Shows as "STOPPED"

**Solutions:**
```bash
# Restart the paper trading bot
sudo systemctl restart cryptobot

# Check startup logs
journalctl -u cryptobot -n 50 --no-pager
```

### Issue 3: No Grid Bot in bot_status Table

**This means Grid Bot never registered**

**Solutions:**
```bash
# Check run_bot.py configuration
cat run_bot.py | grep -A 20 "Grid Bot"

# Verify engine.add_bot() calls exist
grep -n "engine.add_bot" run_bot.py

# Restart bot to re-register
sudo systemctl restart cryptobot
```

---

## Understanding Grid Bot Trading Patterns

### Normal Behavior

**High Volatility (5-10% daily movement):**
- Trades: 20-50 per day
- Each trade: Small profit (0.5-2%)
- Pattern: BUY low, SELL high within grid

**Low Volatility (< 2% daily movement):**
- Trades: 2-10 per day
- Fewer opportunities
- Grid Bot waits for price to cross levels

### Abnormal Behavior

**Zero Trades for 12+ Hours:**
```
Likely Cause: Price outside grid range

Example:
Grid Range: $88,000 - $108,000
Current BTC Price: $110,000 ← TOO HIGH!

Solution: Adjust grid range or wait for price to return
```

**Excessive Losses:**
```
Grid Bots should have 80-95% win rate

If win rate < 60%:
- Check grid_levels configuration
- Verify ATR multiplier settings
- Review fee calculations
```

---

## Performance Benchmarks

### Grid Bot BTC (Expected Performance)

**Configuration (from run_bot.py):**
- Initial Balance: $3,000
- Grid Levels: 20
- Range: $88,000 - $108,000
- Amount per level: $150

**Expected Results (Paper Trading):**
- Daily Trades: 15-40
- Daily P&L: +$50 to +$150
- Win Rate: 85-95%
- Average Trade: +$2 to +$5

### Grid Bot ETH (Expected Performance)

**Configuration:**
- Initial Balance: $3,000
- Grid Levels: 30
- Range: $2,800 - $3,600
- Amount per level: $100

**Expected Results:**
- Daily Trades: 20-60
- Daily P&L: +$40 to +$120
- Win Rate: 85-95%
- Average Trade: +$1.50 to +$3

---

## Automated Monitoring

### Set Up Daily Report

```bash
# Create cron job for daily Grid Bot report
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * cd /Antigravity/antigravity/scratch/crypto_trading_bot && sqlite3 data/trades_v3_paper.db "SELECT strategy, COUNT(*) as trades_24h, ROUND(SUM(cost), 2) as volume FROM trades WHERE strategy LIKE '%Grid%' AND timestamp > datetime('now', '-24 hours') GROUP BY strategy;" | mail -s "Grid Bot Daily Report" your@email.com
```

### Set Up Telegram Alerts

If Telegram notifications are configured, you should receive:

**Trade Notifications:**
```
✅ BUY Grid Bot BTC
📊 BTC/USDT
💰 $150.00 @ $95,234.56
🎯 Grid: Level 12/20
```

**Performance Alerts:**
```
📊 Grid Bot BTC - 24h Summary
✅ Trades: 32
💰 P&L: +$87.45
📈 Win Rate: 91%
```

---

## Files & Tools

### Analysis Script
Location: `/home/user/Cryptobot/scripts/analyze_paper_grid_bot.py`

**Copy to VPS:**
```bash
# From your local machine
scp /home/user/Cryptobot/scripts/analyze_paper_grid_bot.py \
    user@72.60.40.29:/Antigravity/antigravity/scratch/crypto_trading_bot/

# On VPS
cd /Antigravity/antigravity/scratch/crypto_trading_bot
python3 analyze_paper_grid_bot.py
```

### Existing Analysis Script
Your repo already has: `scripts/analyze_24h_performance.sh`

**Run it:**
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
bash /path/to/scripts/analyze_24h_performance.sh
```

---

## Next Steps

1. **SSH to VPS:**
   ```bash
   ssh user@72.60.40.29
   ```

2. **Run Quick Check:**
   ```bash
   cd /Antigravity/antigravity/scratch/crypto_trading_bot

   # Check last trade time
   sqlite3 data/trades_v3_paper.db \
     "SELECT MAX(timestamp) as last_trade FROM trades WHERE strategy LIKE '%Grid%';"
   ```

3. **If Last Trade > 12 Hours Ago:**
   - Check price is within grid range
   - Check bot service is running
   - Review logs for errors
   - Consider restarting bot

4. **If Grid Bot is Trading Normally:**
   - Monitor P&L accumulation
   - Verify trades are profitable
   - Check win rate > 80%
   - Scale up if performing well

---

**Created:** January 3, 2026
**Purpose:** Diagnose Paper Trading Grid Bot performance after user reported zero trades in LIVE mode
