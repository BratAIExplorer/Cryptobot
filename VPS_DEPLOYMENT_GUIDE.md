# VPS Deployment - Position Updater Fix

## Commands to Run on VPS

```bash
cd ~/cryptobot_v3

# Backup current state
cp core/logger.py core/logger.py.backup_$(date +%Y%m%d_%H%M%S)

# Pull changes
git pull origin claude/test-dip-bot-profit-lhCxz

# Test the updater method
python3 test_position_updater.py

# If test passes, restart bot
pkill -f run_bot.py
nohup python3 run_bot.py > logs/bot.log 2>&1 &

# Monitor for position updates
tail -f logs/bot.log | grep -E "POSITION UPDATE|current_price"
```

## Expected Output

After bot starts, you should see (every 3 minutes):
```
[POSITION UPDATE] Refreshed prices for 5 open positions
```

## Verification

Check if positions are being updated:
```bash
sqlite3 data/multi/trades_paper.db "
SELECT 
    symbol,
    ROUND(entry_price,2) as entry,
    ROUND(current_price,2) as current,
    datetime(updated_at) as last_update
FROM positions 
WHERE status='OPEN' 
LIMIT 3;"
```

The `last_update` should be recent (within last 3 minutes).

## Rollback (If Needed)

```bash
pkill -f run_bot.py
git checkout HEAD~1
cp core/logger.py.backup_* core/logger.py
nohup python3 run_bot.py > logs/bot.log 2>&1 &
```
