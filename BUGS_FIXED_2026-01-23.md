# 🐛 Bugs Fixed - 2026-01-23

Complete documentation of all bugs discovered and fixed during dashboard deployment.

---

## Bug #1: Hardcoded strategies_active Count

**Severity**: HIGH
**Impact**: Dashboard shows incorrect number of active bots (3 instead of 5)

### Root Cause
File: `enterprise/backend/api/bots.py:80`

```python
strategies_active=3,  # TODO: Parse from log or config
```

The bot status endpoint returned a **hardcoded value of 3** instead of querying the actual number of running bots from the database.

### Why It Happened
- Developer left a TODO comment
- Quick fix during initial development
- Never replaced with actual database query

### Symptoms
- Dashboard header shows "3 Active Bots" when 5 are running
- Bot status API returns incorrect `strategies_active` count
- Mismatch between bot logs (showing 5) and API response (showing 3)

### Fix Applied
Modified `enterprise/backend/api/bots.py:62-82` to query the `bot_status` table:

```python
# Count active strategies from bot database
strategies_count = 0
try:
    import sqlite3
    from utils.bot_reader import bot_reader
    conn = bot_reader._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bot_status WHERE status = 'RUNNING'")
    strategies_count = cursor.fetchone()[0]
    conn.close()
except Exception as e:
    print(f"Warning: Could not count strategies: {e}")
    strategies_count = 0

return BotStatus(
    is_running=True,
    pid=proc.pid,
    uptime_seconds=uptime,
    mode=mode,
    strategies_active=strategies_count,  # NOW DYNAMIC
    last_heartbeat=datetime.now()
)
```

### Verification
```bash
# Before fix
curl -s http://localhost:8000/api/bots/status -H "Authorization: Bearer $TOKEN"
# Returns: "strategies_active": 3

# After fix
curl -s http://localhost:8000/api/bots/status -H "Authorization: Bearer $TOKEN"
# Returns: "strategies_active": 5
```

---

## Bug #2: Portfolio Only Shows Bots with Trades

**Severity**: HIGH
**Impact**: Bots without trades are invisible on dashboard

### Root Cause
File: `enterprise/backend/utils/bot_reader.py:188-203` (line numbers may vary)

The `get_portfolio_summary()` method queries strategies from the `positions` table:

```python
# Strategy breakdown from positions
cursor.execute("""
    SELECT
        strategy,
        COUNT(*) as position_count,
        SUM(COALESCE(unrealized_pnl_usd, 0)) as strategy_pnl
    FROM positions
    GROUP BY strategy
""")
```

**Problem**: If a bot hasn't made any trades yet, it has NO entries in the `positions` table, so it doesn't appear in the portfolio summary.

### Why It Happened
- Original design assumption: all active bots will have at least one position
- Grid bots typically open positions quickly on startup
- Buy-the-Dip bots wait for specific market conditions (may take hours/days)
- Database schema separates bot configuration (`bot_status`) from trading data (`positions`)

### Symptoms
- Dashboard shows only 1 bot (Grid Bot ETH - the only one with a trade)
- Buy-Dip bots are running but invisible
- Portfolio strategies array missing 4 out of 5 bots
- Confusing UX: bot logs show 5 bots, dashboard shows 1

### Current Status
Portfolio API returns:
```json
{
    "strategies": [
        {
            "name": "Grid Bot ETH",
            "trades": 1,
            "pnl": 0.0
        }
    ]
}
```

Expected:
```json
{
    "strategies": [
        {"name": "Grid Bot BTC", "trades": 0, "pnl": 0.0},
        {"name": "Grid Bot ETH", "trades": 1, "pnl": 0.0},
        {"name": "Buy-Dip-5.2%", "trades": 0, "pnl": 0.0},
        {"name": "Buy-Dip-5.5%", "trades": 0, "pnl": 0.0},
        {"name": "Buy-Dip-8.0%", "trades": 0, "pnl": 0.0}
    ]
}
```

### Fix Required
Modify `get_portfolio_summary()` to:
1. Query ALL bots from `bot_status` table (source of truth for active bots)
2. LEFT JOIN with positions to get P&L data
3. Show bots with 0 trades/pnl if they have no positions yet

```python
# Strategy breakdown from bot_status (show ALL active bots)
cursor.execute("""
    SELECT
        bs.strategy,
        bs.wallet_balance,
        COALESCE(SUM(p.unrealized_pnl_usd), 0) as strategy_pnl,
        COUNT(p.id) as position_count
    FROM bot_status bs
    LEFT JOIN positions p ON bs.strategy = p.strategy
    WHERE bs.status = 'RUNNING'
    GROUP BY bs.strategy, bs.wallet_balance
""")
```

---

## Bug #3: Single Buy-the-Dip Bot Instead of 3 Variants

**Severity**: CRITICAL
**Impact**: Only 3 bots running instead of expected 5

### Root Cause
File: `run_bot.py:148-175`

The bot initialization code created ONE "Buy-the-Dip Strategy" bot instead of THREE separate A/B test variants.

```python
engine.add_bot({
    'name': 'Buy-the-Dip Strategy',  # Single bot
    'type': 'Buy-the-Dip',
    'take_profit_pct': 0.08,  # Fixed 8% profit target
    ...
})
```

### Why It Happened
- A/B test configuration was added to the file but not used
- `AB_TEST_ENABLED` and `AB_TEST_VARIANTS` variables existed but were orphaned
- Bot initialization logic never refactored to loop through variants
- Deployment script added config but didn't modify initialization

### Symptoms
- Bot logs show only 3 bots:
  - Grid Bot BTC
  - Grid Bot ETH
  - Buy-the-Dip Strategy (single)
- Expected 5 bots (2 Grid + 3 Buy-Dip variants)
- Dashboard shows 3 active bots
- No A/B testing happening despite config existing

### Fix Applied
File: `FIX_5_BOTS_CONFIG.sh`

Replaced single bot configuration with 3 separate bots:

```python
# Variant 1: Conservative (5.2% profit)
engine.add_bot({
    'name': 'Buy-Dip-5.2%',
    'type': 'Buy-the-Dip',
    'initial_balance': 333,
    'take_profit_pct': 0.052,
    ...
})

# Variant 2: Standard (5.5% profit)
engine.add_bot({
    'name': 'Buy-Dip-5.5%',
    'type': 'Buy-the-Dip',
    'initial_balance': 333,
    'take_profit_pct': 0.055,
    ...
})

# Variant 3: Aggressive (8.0% profit)
engine.add_bot({
    'name': 'Buy-Dip-8.0%',
    'type': 'Buy-the-Dip',
    'initial_balance': 334,
    'take_profit_pct': 0.080,
    ...
})
```

### Verification
```bash
grep "Bot added" ~/cryptobot_v3/logs/bot.log
# Before fix:
Bot added: Grid Bot BTC
Bot added: Grid Bot ETH
Bot added: Buy-the-Dip Strategy

# After fix:
Bot added: Grid Bot BTC
Bot added: Grid Bot ETH
Bot added: Buy-Dip-5.2%
Bot added: Buy-Dip-5.5%
Bot added: Buy-Dip-8.0%
```

---

## Bug #4: Dashboard API Crashing (500 Errors)

**Severity**: CRITICAL
**Impact**: Portfolio and performance endpoints completely broken

### Root Cause
File: `enterprise/backend/utils/bot_reader.py` (original version before fix)

API was querying non-existent `pnl` column in `trades` table:

```python
# WRONG - trades table has NO pnl column
cursor.execute("SELECT SUM(COALESCE(pnl, 0)) FROM trades")
```

### Database Schema Reality
```sql
-- trades table does NOT have pnl column
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    strategy VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10),
    price FLOAT,
    amount FLOAT,
    cost FLOAT,
    fee FLOAT
    -- NO pnl COLUMN!
);

-- positions table HAS unrealized_pnl_usd
CREATE TABLE positions (
    id VARCHAR(36) PRIMARY KEY,
    ...
    unrealized_pnl_usd FLOAT,  -- THIS exists
    unrealized_pnl_pct FLOAT,
    ...
);
```

### Why It Happened
- Misunderstanding of database schema
- Assumed `trades` table would have P&L calculation
- Actual design: P&L calculated at position level, not trade level
- No schema documentation referenced during API development

### Symptoms
```bash
curl http://localhost:8000/api/trades/portfolio
# Returns: 500 Internal Server Error

# Backend logs:
INFO: 161.142.150.117:4128 - "GET /api/trades/portfolio HTTP/1.1" 500
```

### Fix Applied
File: `FIX_DASHBOARD_API.sh`

Completely rewrote `bot_reader.py` to use `positions` table:

```python
# CORRECT - use positions table
cursor.execute("SELECT SUM(COALESCE(unrealized_pnl_usd, 0)) FROM positions")
total_pnl = cursor.fetchone()[0] or 0.0
```

### Verification
```bash
# After fix
curl -s http://localhost:8000/api/trades/portfolio -H "Authorization: Bearer $TOKEN"
# Returns: 200 OK with valid JSON
{
    "total_pnl": 0.0,
    "total_trades": 1,
    "win_rate": 0.0,
    ...
}
```

---

## Bug #5: Firewall Blocking Port 3000

**Severity**: MEDIUM
**Impact**: Dashboard completely inaccessible from browser

### Root Cause
VPS firewall (ufw) not configured to allow incoming connections on port 3000.

### Why It Happened
- Initial deployment focused on bot (no frontend)
- Backend port 8000 was opened
- Frontend deployment added later without updating firewall
- Default ufw policy: deny all incoming except explicitly allowed

### Symptoms
```
Browser error: 72.60.40.29 refused to connect
ERR_CONNECTION_REFUSED
```

### Services Status
```bash
# Frontend running correctly
ps aux | grep next
root  46514  next-server (port 3000)

# But firewall blocking connections
sudo ufw status | grep 3000
# (no output - port not allowed)
```

### Fix Applied
```bash
sudo ufw allow 3000/tcp
sudo ufw status
# Output:
3000/tcp    ALLOW    Anywhere
```

### Verification
```bash
# Before fix
curl http://72.60.40.29:3000
# Connection refused

# After fix
curl http://72.60.40.29:3000
# Returns HTML (Next.js page)
```

---

## Bug #6: Email Validation Failure

**Severity**: LOW
**Impact**: Admin login failing during initial setup

### Root Cause
File: `enterprise/backend/.env`

```bash
ADMIN_EMAIL=admin@cryptobot.local  # .local TLD rejected
```

Pydantic email validator rejects `.local` TLD as special-use/reserved name.

### Why It Happened
- Development convention: use `.local` for internal services
- Pydantic follows RFC standards strictly
- `.local` is mDNS/Bonjour reserved TLD (RFC 6762)
- FastAPI validation layer blocked it

### Symptoms
```
POST /api/auth/login/json
Error: "The part after the @-sign is a special-use or reserved name that cannot be used with email"
```

### Fix Applied
```bash
# Changed .env
ADMIN_EMAIL=admin@cryptobot.com
```

Restarted backend to recreate admin user with valid email.

### Verification
```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cryptobot.com","password":"change_me_immediately"}'
# Returns: {"access_token": "...", "token_type": "bearer"}
```

---

## Summary of All Fixes

| Bug # | Issue | Severity | File | Status |
|-------|-------|----------|------|--------|
| 1 | Hardcoded strategies_active=3 | HIGH | `api/bots.py:80` | ✅ FIXED |
| 2 | Portfolio missing bots without trades | HIGH | `utils/bot_reader.py:188` | 🔧 IN PROGRESS |
| 3 | Only 1 Buy-Dip bot instead of 3 | CRITICAL | `run_bot.py:148` | ✅ FIXED |
| 4 | API querying wrong table/column | CRITICAL | `utils/bot_reader.py` | ✅ FIXED |
| 5 | Firewall blocking port 3000 | MEDIUM | UFW config | ✅ FIXED |
| 6 | Email .local TLD rejected | LOW | `.env` | ✅ FIXED |

---

## Lessons Learned

### 1. **Avoid Hardcoded Values**
- Never use `TODO` comments with hardcoded values in production
- If you must hardcode during development, add a failing test or assertion
- Use database queries or configuration files for dynamic values

### 2. **Document Database Schema**
- Maintain up-to-date schema documentation
- Include column descriptions and relationships
- Reference schema when writing queries

### 3. **Test with Empty States**
- Don't assume data will always exist
- Test API endpoints with:
  - Empty database
  - Partial data (some bots with trades, some without)
  - Full data
- Handle NULL/missing data gracefully

### 4. **Configuration vs. Implementation**
- Adding `AB_TEST_ENABLED` config doesn't automatically enable A/B testing
- Configuration must be **consumed** by implementation code
- Deployment scripts should verify changes are actually used

### 5. **Database Design Considerations**
- Separate configuration tables (`bot_status`) from transactional tables (`trades`, `positions`)
- Use LEFT JOINS when displaying all configured items regardless of activity
- Don't rely on transactional tables as source of truth for active configurations

### 6. **Infrastructure Checklist**
- Firewall rules
- Port accessibility
- Service dependencies
- Authentication/authorization
- Environment configuration

---

## Files Modified

### Backend
- `enterprise/backend/api/bots.py` - Fixed strategies_active count
- `enterprise/backend/utils/bot_reader.py` - Rewritten to use positions table (pending final fix)
- `enterprise/backend/.env` - Changed email domain

### Bot Configuration
- `run_bot.py` - Split Buy-the-Dip into 3 variants

### Deployment Scripts
- `FIX_DASHBOARD_API.sh` - Rewrites bot_reader.py
- `FIX_5_BOTS_CONFIG.sh` - Reconfigures bot initialization
- `COMPLETE_FIX_DEPLOYMENT.sh` - Comprehensive fix deployment

### Infrastructure
- UFW firewall - Allowed port 3000

---

## Testing Checklist

After all fixes applied:

- [ ] API returns `strategies_active: 5`
- [ ] Portfolio shows all 5 bots
- [ ] Bot logs show 5 bots initialized
- [ ] Dashboard header shows "5 Active Bots"
- [ ] Dashboard displays 5 bot cards
- [ ] Bots without trades show $0.00 P&L
- [ ] Portfolio total shows $1,500
- [ ] No 500 errors in browser console
- [ ] Hard refresh clears any cached data

---

**Document Date**: 2026-01-23
**Total Bugs Fixed**: 6
**Status**: 5 fixed, 1 in progress (Bug #2 - portfolio endpoint)
