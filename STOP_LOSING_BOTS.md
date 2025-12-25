# How to Stop Losing Bots on VPS

## Quick Command Reference

```bash
# SSH to your VPS
ssh [your-username]@[your-vps-ip]

# Navigate to project directory
cd /root/CryptoBot_Project

# Check all running processes
pm2 list

# Stop specific bot by name
pm2 stop "Hyper-Scalper Bot"
pm2 stop "Buy-the-Dip Strategy"

# OR delete them completely
pm2 delete "Hyper-Scalper Bot"
pm2 delete "Buy-the-Dip Strategy"

# Save the updated configuration
pm2 save

# Verify they're stopped
pm2 list
```

## Alternative: Stop by Process ID

If bot names don't match exactly:

```bash
# List all processes with IDs
pm2 list

# Stop by ID (replace 0 with actual ID)
pm2 stop 0
pm2 stop 1

# Delete by ID
pm2 delete 0
pm2 delete 1

# Save configuration
pm2 save
```

## Verify Bots Are Stopped

1. **Check PM2 status:**
   ```bash
   pm2 list
   # Stopped bots should show status: "stopped"
   ```

2. **Check dashboard:**
   - Navigate to dashboard in browser
   - Verify bot status shows "STOPPED" or "PAUSED"
   - Confirm P&L values are now accurate

3. **Check Telegram alerts:**
   - You should receive a notification that bots have stopped

## Bots to Stop (Based on Analysis)

### 🔴 Hyper-Scalper Bot
- **Current Loss:** -$3,144.48
- **Reason:** Dashboard was hiding the loss by showing $0
- **Trade Activity:** 116 trades (59 buys, 57 sells)
- **Problem:** Bought $47,200 worth, sold only $44,055

### 🔴 Buy-the-Dip Strategy  
- **Current Loss:** -$7,675.42
- **Reason:** Worse than dashboard showed (-$3,517)
- **Trade Activity:** Multiple trades with significant losses
- **Problems:**
  - Overtrading (11 trades on Dec 5 alone)
  - Catching falling knives (buying dips that keep dipping)
  - No proper stop-losses
  - Position sizing too large ($800 per trade)
  - Has $800 stuck in XRP (open position not sold)

## After Stopping the Bots

### 1. Review Open Positions
Check the dashboard for any open positions belonging to stopped bots:
- Go to "Open Positions" tab
- Look for positions from Hyper-Scalper or Buy-the-Dip
- Consider manually closing underwater positions via exchange

### 2. Close Positions (Optional)
If you want to liquidate positions:
- Log into MEXC exchange
- Manually sell any coins bought by stopped bots
- This will realize the losses but free up capital

### 3. Keep Running (Profitable Bots)
✅ **Grid Bot ETH** - Keep running (+$4,007.67 profit)
✅ **Grid Bot BTC** - Keep running (+$815.48 profit)  
✅ **SMA Trend Bot** - Keep running (+$2,336.32 profit)
✅ **Hidden Gem** - Keep running (+$720.05 profit)

## If You Want to Restart Buy-the-Dip Later

Before restarting, reconfigure it in `run_bot.py`:

```python
{
    'name': 'Buy-the-Dip Strategy',
    'type': 'Buy-the-Dip',
    'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT'],
    'amount': 200,  # REDUCED from $800 to $200
    'max_exposure_per_coin': 600,  # REDUCED from $2000 to $600
    'dip_threshold': 0.12,  # INCREASED from 8% to 12% (more selective)
    'take_profit_pct': 0.05,
    'stop_loss_enabled': True,  # ENABLE stop loss
    'stop_loss_pct': 0.05,  # 5% stop loss
    'initial_balance': 5000
}
```

## Troubleshooting

### Bot won't stop
```bash
# Force kill the process
pm2 kill

# Restart pm2
pm2 resurrect

# Or use system commands
pkill -f "Hyper-Scalper"
pkill -f "Buy-the-Dip"
```

### Can't find bot in pm2 list
```bash
# Check all running Python processes
ps aux | grep python

# Find and kill by PID
kill [PID]
```

### Dashboard still shows bot as running
- Wait 30 seconds and refresh
- Check if bot heartbeat timestamp is updating
- If stuck, restart dashboard:
  ```bash
  pm2 restart dashboard
  ```
