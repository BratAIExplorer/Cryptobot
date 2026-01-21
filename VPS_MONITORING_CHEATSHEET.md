# 🕵️‍♂️ VPS Monitoring Cheat Sheet

Run these commands on your VPS terminal (`root@srv...`) to check bot health and performance.

## 🚀 Process Management

**Check if bot is running:**
```bash
ps aux | grep run_bot.py
```

**Restart Bot (Apply new code):**
```bash
pkill -f run_bot.py
# Wait a few seconds...
nohup python3 run_bot.py > logs/bot.log 2>&1 &
```

**Stop Bot:**
```bash
pkill -f run_bot.py
```

---

## 📜 Log Monitoring

**Watch live logs (Follow mode):**
```bash
tail -f logs/bot.log
```
*(Press `Ctrl+C` to exit)*

**Check for Errors:**
```bash
grep -i "error\|exception\|traceback" logs/bot.log | tail -n 20
```

**Verify Position Updates (New Feature):**
```bash
grep "POSITION UPDATE" logs/bot.log | tail -n 20
```

**Check Buy/Sell Signals:**
```bash
grep -E "BUY|SELL|Signal" logs/bot.log | tail -n 20
```

---

## 📊 Database / Performance Queries
*(Copy and paste these directly into the terminal)*

**1. Check OPEN Positions (Live Status):**
See what the bot is currently holding and its real-time P&L.
```bash
sqlite3 data/multi/trades_paper.db "
.mode column
.headers on
SELECT 
    symbol,
    strategy,
    ROUND(entry_price, 2) as entry,
    ROUND(current_price, 2) as current,
    ROUND(unrealized_pnl_pct, 2) || '%' as pnl_pct,
    ROUND(unrealized_pnl_usd, 2) as pnl_usd,
    datetime(updated_at) as last_update
FROM positions 
WHERE status='OPEN'
ORDER BY updated_at DESC;
"
```

**2. Check CLOSED Positions (Profit History):**
See your realized gains/losses.
```bash
sqlite3 data/multi/trades_paper.db "
.mode column
.headers on
SELECT 
    symbol,
    strategy,
    ROUND(entry_price, 2) as buy_at,
    ROUND(exit_price, 2) as sold_at,
    ROUND(unrealized_pnl_pct, 2) || '%' as profit_pct,
    ROUND(unrealized_pnl_usd, 2) as profit_usd,
    datetime(exit_date) as closed_at
FROM positions 
WHERE status='CLOSED'
ORDER BY exit_date DESC
LIMIT 10;
"
```

**3. Performance Summary:**
Total Win/Loss stats.
```bash
sqlite3 data/multi/trades_paper.db "
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN unrealized_pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN unrealized_pnl_usd <= 0 THEN 1 ELSE 0 END) as losses,
    ROUND(SUM(unrealized_pnl_usd), 2) as total_pnl_usd
FROM positions 
WHERE status='CLOSED';
"
```

---

## 🛠️ Update & Maintenance

**Pull latest code from GitHub:**
```bash
cd ~/cryptobot_v3
git pull
```

**Check Disk Usage (Prevent log overflow):**
```bash
df -h
du -sh logs/
```
