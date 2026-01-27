# CryptoBot V3 - Issues & Solutions Log

## Date: 2026-01-25

---

## Issue #1: Only 3 of 9 Bots Initializing

### Symptoms
- Dashboard showed only 3 bots (Grid BTC, Grid ETH, Buy-the-Dip Strategy)
- Bot status table had stale heartbeats for 6 bots
- Startup log showed: `Bot added: Grid Bot BTC`, `Bot added: Grid Bot ETH`, `Bot added: Buy-the-Dip Strategy` (only 3)

### Root Cause
The bot process (PID 262836) was started BEFORE the updated `run_bot.py` was deployed. The running process had the old 3-bot configuration in memory.

### Solution
```bash
# 1. Stop all bot processes
sudo systemctl stop cryptobot
pkill -9 python3

# 2. Clear old logs
rm ~/cryptobot_v3/logs/bot_engine.log

# 3. Start fresh
sudo systemctl start cryptobot

# 4. Verify all 9 bots loaded
cat ~/cryptobot_v3/logs/bot_engine.log | grep 'Bot added'
```

### Result
All 9 bots now initialize: Grid BTC, Grid ETH, Buy-the-Dip Strategy, SMA Trend Bot, DCA Bot, Buy-Dip-5.2%, Buy-Dip-5.5%, Buy-Dip-8.0%, Volatility Hunter

---

## Issue #2: Dashboard Login Failed - Connection Refused to Port 8000

### Symptoms
- Login page loads at `http://72.60.40.29:3000/login`
- Error in browser console: `ERR_CONNECTION_REFUSED` to `:8000/api/auth/login`
- Frontend works, but API calls fail

### Root Cause
Backend API (FastAPI/Uvicorn) not running on port 8000.

### Solution
```bash
# Check if backend is running
lsof -i:8000

# Start backend manually
cd ~/cryptobot_v3/enterprise/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# Verify
lsof -i:8000
```

---

## Issue #3: Backend Fails to Start - PostgreSQL Authentication Error

### Symptoms
- Backend log shows: `FATAL: password authentication failed for user "postgres"`
- `Application startup failed. Exiting.`

### Root Cause
The `.env` file had `DATABASE_URL=postgresql://postgres:postgres@localhost/cryptobot_enterprise` but the PostgreSQL password was different.

### Solution
Update the password to match (or change the database password):

```bash
# Option A: Update .env to match existing password
sed -i 's|postgresql://postgres:postgres@|postgresql://postgres:Cryptobot_999@|' ~/cryptobot_v3/enterprise/backend/.env

# Option B: Change PostgreSQL password (if running in Docker)
docker exec kyro_postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'Cryptobot_999';"
```

---

## Issue #4: PostgreSQL Native Service Won't Start

### Symptoms
- `sudo pg_ctlcluster 16 main start` fails
- Error: `could not create any TCP/IP sockets`
- Port 5432 already in use

### Root Cause
A Docker container (`kyro_postgres`) is already running PostgreSQL on port 5432.

### Solution
**Don't start the native PostgreSQL - use the Docker container instead.**

```bash
# Check what's using port 5432
lsof -i:5432
# Output: docker-pr 280591... TCP *:postgresql (LISTEN)

# Verify Docker container is healthy
docker ps | grep postgres
# Output: kyro_postgres ... Up ... (healthy)

# Use Docker PostgreSQL, not native
# The .env should point to localhost:5432 which routes to Docker
```

---

## Issue #5: SSH Command Escaping in PowerShell

### Symptoms
- Commands with quotes fail: `unexpected EOF while looking for matching '"'`
- Complex SQL commands break

### Root Cause
PowerShell has different quote escaping rules than bash.

### Solution
Use single quotes for the outer SSH command and escape inner quotes properly:

```powershell
# Instead of:
ssh root@vps "docker exec db psql -c \"ALTER USER ...\""

# Use:
ssh root@vps 'docker exec db psql -c "ALTER USER postgres PASSWORD '"'"'Cryptobot_999'"'"';"'
```

---

## Issue #6: Frontend Service Not Running

### Symptoms
- `http://72.60.40.29:3000` not accessible
- `lsof -i:3000` returns empty

### Root Cause
No systemd service exists for the frontend. It was started manually and has since stopped.

### Solution
```bash
# Start frontend manually
cd ~/cryptobot_v3/enterprise/frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &

# Verify
lsof -i:3000
```

---

## Quick Health Check Commands

```bash
# Check all services
lsof -i:3000  # Frontend (Next.js)
lsof -i:8000  # Backend (FastAPI)
lsof -i:5432  # PostgreSQL
ps aux | grep run_bot | grep -v grep  # Trading bots

# Check bot count in database
sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db 'SELECT COUNT(*) FROM bot_status;'

# Check bot heartbeats
sqlite3 ~/cryptobot_v3/data/multi/trades_paper.db 'SELECT strategy, status, last_heartbeat FROM bot_status ORDER BY last_heartbeat DESC;'

# Restart everything
sudo systemctl restart cryptobot
cd ~/cryptobot_v3/enterprise/backend && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
cd ~/cryptobot_v3/enterprise/frontend && nohup npm run dev > /tmp/frontend.log 2>&1 &
```

---

---

## Issue #7: Grid Bot Force-Closed at Loss after 24h

### Symptoms
- Grid bots showing realized losses of ~1.4%
- Trade analysis shows trades closing exactly 24 hours after opening.
- Grid bots are mean-reversion strategies that should wait for a bounce, but they were being killed early.

### Root Cause
The engine's "Auto-Cleanup" feature was force-closing stagnant positions after 24 hours (default) to free up capital. Grid bots were not exempt from this policy, causing them to sell at a loss if the price hadn't recovered within a day.

### Solution
Modified `core/engine.py` to add `Grid` bots to the "Indefinite Hold" list (max_hold = 0), allowing them to wait for their profit targets regardless of time.

---

## Issue #8: Buy-the-Dip Strategy Not Trading (Confluence 0)

### Symptoms
- "Buy-the-Dip" strategy shows no trades despite active dips.
- Log message: `Confluence V2 Reject: Score X/100 (Threshold 0)` or successful filter but no execution.
- Small trades ($1.50) were being calculated but rejected by Binance due to $10 minimum.

### Root Cause
Even with `min_confluence` at 0, the engine was scaling trade sizes based on conviction. A low score was resulting in a 10% scaling ($15 -> $1.50). Binance rejects any order below ~$10-15.

### Solution
1. Modified `core/engine.py` to force **100% trade size** when `min_confluence` is set to 0 or less (Data Collection Mode).
2. Increased `amount` for Buy-the-Dip in `run_bot.py` from **$15 to $30** to ensure even scaled trades (if used) comfortably meet exchange minimums.

---

## Summary of Active Configuration

| Component | Port | Process | Status |
|-----------|------|---------|--------|
| Frontend (Next.js) | 3000 | npm run dev | Manual start required |
| Backend (FastAPI) | 8000 | uvicorn main:app | Manual start required |
| PostgreSQL | 5432 | Docker: kyro_postgres | Auto-managed by Docker |
| Trading Bots | N/A | cryptobot.service | Systemd managed |

### Login Credentials
- **Dashboard URL**: http://72.60.40.29:3000/login
- **Default Admin**: admin / change_me_immediately
- **Database Password**: Cryptobot_999
- **Database Path (V3)**: `~/cryptobot_v3/data/multi/trades_paper.db`

---

## Issue #9: Exposure Limits Bypassed in Data Collection Mode

### Symptoms
- Bots exceeded their `max_exposure_per_coin` limits.
- A single coin could consume most of a bot's budget if it kept dipping.
- Logs showed: `📊 [DATA COLLECTION] Bypassing exposure limit for {symbol}...`

### Root Cause
In `core/engine.py`, there was a logic block specifically designed to **bypass** the exposure check if `is_data_collection` was True (which happens when `min_confluence <= 0`). This was intended for research but was dangerous for a scaled portfolio.

### Solution
**Removed the bypass logic entirely.**
The engine now strictly enforces `max_exposure_per_coin` for ALL bots, regardless of their mode or confluence settings.

- **File**: `core/engine.py` (lines ~1181)
- **Fix**: Removed `if is_data_collection:` check before the specific limit enforcement block.
