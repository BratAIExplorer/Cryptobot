# Cryptobot - Living Document & Task Tracker
**Last Updated:** 2026-01-11 12:10 UTC
**Current Branch:** `claude/check-dashboard-status-VNa0U`
**VPS Server:** srv1010193 (runsc) - IP: 21.0.0.28

---

## 🚀 CURRENT TASKS (In Progress)

| Task | Status | Priority | Started | Notes |
|------|--------|----------|---------|-------|
| Dashboard Health Check | ✅ COMPLETE | HIGH | 2026-01-11 | All dashboards checked, main dashboard running |
| Install Dependencies | ✅ COMPLETE | CRITICAL | 2026-01-11 | All pip packages installed successfully |
| Create Environment Config | ✅ COMPLETE | HIGH | 2026-01-11 | `.env` created with defaults |
| Restore Databases | ✅ COMPLETE | HIGH | 2026-01-11 | 72MB backup restored |
| Start Trading Dashboard | ✅ COMPLETE | HIGH | 2026-01-11 | Running on port 8501 |
| Document Status | ✅ COMPLETE | MEDIUM | 2026-01-11 | Created DASHBOARD_STATUS_REPORT.md |
| Create Living Document | 🔵 IN PROGRESS | MEDIUM | 2026-01-11 | This document |

---

## 📋 BACKLOG (Pending Tasks)

### 🔴 HIGH Priority

| Task | Description | Depends On | Estimate |
|------|-------------|------------|----------|
| Configure Production Credentials | Add real Telegram/API keys to `.env` | None | 15 min |
| Start Intelligence Dashboard | Launch on port 8502 | Dependencies installed ✅ | 5 min |
| Start Luno Monitor | Launch Flask app on port 5000 | Dependencies installed ✅ | 10 min |
| Set up Process Manager (PM2) | Auto-restart dashboards on crash | Dashboard running ✅ | 30 min |
| Configure Firewall Rules | Open ports 8501, 8502, 5000 | Dashboards running | 20 min |

### 🟡 MEDIUM Priority

| Task | Description | Depends On | Estimate |
|------|-------------|------------|----------|
| Create Intelligence Database | Initialize `intelligence.db` schema | None | 20 min |
| Set up SSL/HTTPS | Configure nginx reverse proxy | Firewall configured | 1-2 hrs |
| Create Systemd Services | Auto-start on reboot | Process manager | 45 min |
| Test Paper Trading Mode | Verify mode switching works | Dashboard running ✅ | 30 min |
| Test Live Trading Mode | Verify with test credentials | API keys configured | 1 hr |
| Dashboard Integration Testing | Test all 3 dashboards together | All dashboards running | 1 hr |

### 🟢 LOW Priority

| Task | Description | Depends On | Estimate |
|------|-------------|------------|----------|
| Implement Unified Dashboard v4 | Consolidate 3 dashboards into one | All dashboards tested | 2-3 days |
| Add Mobile Responsive Design | Make dashboard mobile-friendly | Dashboard v4 | 1-2 days |
| Set up Monitoring/Alerting | Uptime monitoring, error alerts | Production config | 1 day |
| Performance Optimization | Optimize database queries, caching | All features tested | 2-3 days |
| Documentation Update | Update all docs with new features | Features complete | 1 day |

---

## 📂 KEY PATHS & FILES

### 🖥️ **VPS ENVIRONMENT**
```
Server:           srv1010193 (hostname: runsc)
IP Address:       21.0.0.28
User:             root
Python:           /usr/local/bin/python3 (v3.11.14)
Project Root:     /home/user/Cryptobot ⭐ IMPORTANT: This is YOUR working directory
```

### 📁 **CRITICAL DIRECTORIES**

```
/home/user/Cryptobot/          # ⭐ PROJECT ROOT - Always cd here first!
├── dashboard/                  # Trading bot dashboard (Streamlit)
│   ├── app.py                 # Main dashboard application ⭐
│   ├── beginner_helpers.py    # Non-technical user translations
│   ├── components.py          # UI components
│   └── UI_IMPROVEMENTS.md     # Design documentation
│
├── intelligence/               # Intelligence & scoring system
│   ├── dashboard_intelligence.py  # Intelligence dashboard ⭐
│   ├── config.py              # Feature flags & thresholds
│   ├── master_decision.py     # Decision engine
│   ├── regulatory_scorer.py   # Fundamental analysis
│   └── asset_classifier.py    # Asset type routing
│
├── luno-monitor/              # Portfolio monitoring (Flask)
│   ├── src/
│   │   ├── dashboard.py       # Flask app ⭐
│   │   └── templates/         # HTML templates
│   ├── main.py                # Flask entry point ⭐
│   └── config.py              # Luno-specific config
│
├── core/                      # Trading bot core logic
│   ├── exchange.py            # Exchange interface (CCXT wrapper)
│   ├── strategies/            # Trading strategies
│   │   ├── grid_bot.py       # Grid trading strategy
│   │   └── dca_bot.py        # DCA strategy
│   ├── logger.py              # Trade logging
│   └── db_manager.py          # Database operations
│
├── data/                      # Data storage
│   ├── trades_v3.db          # ⭐ Main trading database (72MB)
│   ├── trades_paper.db       # ⭐ Paper trading database (72MB)
│   ├── known_symbols_mexc.json
│   └── coin_age_cache.json
│
├── docs/                      # Documentation
│   ├── LIVING_DOCUMENT.md    # ⭐ THIS FILE - Always check here first!
│   ├── DASHBOARD_STATUS_REPORT.md  # Latest dashboard status
│   ├── AI_HANDOVER.md        # AI context for continuity
│   ├── PRODUCT_STRATEGY_2026.md    # Product roadmap
│   └── VPS_DEPLOYMENT_GUIDE_V3.md  # Deployment instructions
│
├── .env                       # ⭐ Environment variables (secrets)
├── .env.template              # Template for .env
├── requirements.txt           # ⭐ Python dependencies
├── dashboard.log              # Dashboard runtime logs
└── README.md                  # Project overview
```

### 🗄️ **DATABASE FILES**

| Database | Path | Size | Purpose | Status |
|----------|------|------|---------|--------|
| **Main Trading DB** | `data/trades_v3.db` | 72MB | Live/paper trades, positions, P&L | ✅ Active |
| **Paper Trading DB** | `data/trades_paper.db` | 72MB | Paper mode trades | ✅ Active |
| **Intelligence DB** | `intelligence.db` | N/A | Asset scores, decisions | ❌ Missing (needs creation) |

### ⚙️ **CONFIGURATION FILES**

| File | Path | Purpose | Status |
|------|------|---------|--------|
| **Environment Config** | `.env` | Secrets, API keys, passwords | ✅ Created |
| **Dependencies** | `requirements.txt` | Python packages | ✅ Installed |
| **Intelligence Config** | `intelligence/config.py` | Feature flags, thresholds | ✅ Exists |
| **Luno Config** | `luno-monitor/config.py` | Luno API settings | ✅ Exists |

### 📝 **LOG FILES**

```
/home/user/Cryptobot/dashboard.log           # Main dashboard logs
/home/user/Cryptobot/logs/trading.log        # Trading bot logs (if exists)
/home/user/Cryptobot/luno-monitor/logs/      # Luno monitor logs (if exists)
```

---

## 🌐 DASHBOARD ACCESS INFO

### **Trading Bot Dashboard** (Streamlit)
- **URL:** http://21.0.0.28:8501
- **Status:** ✅ RUNNING (PID: 9979)
- **Port:** 8501
- **Password:** `admin123`
- **Start Command:**
  ```bash
  cd /home/user/Cryptobot
  python3 -m streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
  ```

### **Intelligence Dashboard** (Streamlit)
- **URL:** http://21.0.0.28:8502
- **Status:** ❌ NOT RUNNING
- **Port:** 8502
- **Start Command:**
  ```bash
  cd /home/user/Cryptobot
  python3 -m streamlit run intelligence/dashboard_intelligence.py --server.port 8502 --server.address 0.0.0.0
  ```

### **Luno Monitor** (Flask)
- **URL:** http://21.0.0.28:5000
- **Status:** ❌ NOT RUNNING
- **Port:** 5000
- **Start Command:**
  ```bash
  cd /home/user/Cryptobot/luno-monitor
  python main.py
  ```

---

## 🔧 QUICK REFERENCE COMMANDS

### **Navigation (ALWAYS START HERE)**
```bash
# ⭐ MOST IMPORTANT: Always cd to project root first
cd /home/user/Cryptobot

# Verify you're in the right place
pwd
# Should output: /home/user/Cryptobot
```

### **Dashboard Management**
```bash
# Check if dashboards are running
ps aux | grep streamlit | grep -v grep
ps aux | grep flask | grep -v grep

# View dashboard logs
tail -f /home/user/Cryptobot/dashboard.log

# Stop all dashboards
pkill -f streamlit
pkill -f flask

# Start main dashboard
cd /home/user/Cryptobot
nohup python3 -m streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

# Start intelligence dashboard
cd /home/user/Cryptobot
nohup python3 -m streamlit run intelligence/dashboard_intelligence.py --server.port 8502 --server.address 0.0.0.0 > intelligence.log 2>&1 &

# Start Luno monitor
cd /home/user/Cryptobot/luno-monitor
nohup python main.py > luno.log 2>&1 &
```

### **System Checks**
```bash
# Check Python version
python3 --version  # Should be 3.11.14

# Verify dependencies installed
python3 -c "import streamlit; print('Streamlit OK')"
python3 -c "import ccxt; print('CCXT OK')"
python3 -c "import pandas; print('Pandas OK')"

# Check port usage
ss -tulpn | grep 8501
ss -tulpn | grep 8502
ss -tulpn | grep 5000

# Check disk space
df -h

# Check memory usage
free -h
```

### **Database Management**
```bash
# Check database files
ls -lh /home/user/Cryptobot/data/*.db

# Access database (SQLite CLI)
sqlite3 /home/user/Cryptobot/data/trades_v3.db

# Common SQL queries (inside sqlite3)
.tables                          # List all tables
SELECT COUNT(*) FROM trades;     # Count trades
.exit                            # Exit sqlite3
```

### **Git Operations**
```bash
cd /home/user/Cryptobot

# Check status
git status

# Current branch
git branch

# Pull latest changes
git pull origin claude/check-dashboard-status-VNa0U

# View recent commits
git log --oneline -10

# View changes
git diff
```

### **Log Monitoring**
```bash
# Real-time dashboard logs
tail -f /home/user/Cryptobot/dashboard.log

# Real-time intelligence logs (if running)
tail -f /home/user/Cryptobot/intelligence.log

# View last 50 lines
tail -50 /home/user/Cryptobot/dashboard.log

# Search logs for errors
grep -i error /home/user/Cryptobot/dashboard.log
```

---

## 🔐 ENVIRONMENT VARIABLES (.env)

### **Current Configuration**
```bash
# View current .env (without sensitive data)
cat /home/user/Cryptobot/.env | grep -v "TOKEN\|SECRET\|KEY" | grep -v "^#"

# Edit .env file
nano /home/user/Cryptobot/.env
```

### **Required for Full Functionality**
```
TELEGRAM_BOT_TOKEN=          # Get from @BotFather
TELEGRAM_CHAT_ID=            # Get from @userinfobot
CRYPTOPANIC_API_KEY=         # Get from cryptopanic.com/developers/api/
DASHBOARD_PASSWORD=admin123  # ✅ Already set
MEXC_API_KEY=               # For live trading (optional)
MEXC_SECRET=                # For live trading (optional)
```

---

## 📊 SYSTEM ARCHITECTURE

### **Technology Stack**
- **Backend:** Python 3.11.14
- **Web Frameworks:** Streamlit (dashboards), Flask (Luno monitor)
- **Database:** SQLite3
- **Exchange API:** CCXT (unified crypto exchange library)
- **Charting:** Plotly
- **Data Processing:** Pandas, NumPy

### **Dashboard Ecosystem**
```
┌─────────────────────────────────────────────────────────┐
│                     VPS Server                          │
│                  21.0.0.28:8501/8502/5000              │
└─────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
    ┌───────▼────┐  ┌─────▼──────┐  ┌───▼────────┐
    │  Trading   │  │Intelligence│  │   Luno     │
    │ Dashboard  │  │ Dashboard  │  │  Monitor   │
    │ (Streamlit)│  │ (Streamlit)│  │  (Flask)   │
    │   :8501    │  │   :8502    │  │   :5000    │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │                │
    ┌─────▼───────────────▼────────────────▼─────┐
    │         Database Layer (SQLite)            │
    │  trades_v3.db | trades_paper.db           │
    │         intelligence.db (missing)          │
    └────────────────────────────────────────────┘
                           │
    ┌──────────────────────▼─────────────────────┐
    │         Exchange APIs (CCXT)               │
    │    MEXC | Binance | Luno (via API)        │
    └────────────────────────────────────────────┘
```

---

## 🐛 KNOWN ISSUES & WORKAROUNDS

### Issue 1: "File does not exist: dashboard/app.py"
**Cause:** Not in correct directory
**Solution:**
```bash
cd /home/user/Cryptobot
# Then try command again
```

### Issue 2: "Port 8501 is already in use"
**Cause:** Previous dashboard still running
**Solution:**
```bash
pkill -f streamlit
sleep 2
# Then restart dashboard
```

### Issue 3: "ModuleNotFoundError: No module named 'streamlit'"
**Cause:** Dependencies not installed
**Solution:**
```bash
cd /home/user/Cryptobot
pip3 install -r requirements.txt
```

### Issue 4: Intelligence dashboard shows no data
**Cause:** `intelligence.db` doesn't exist
**Solution:** Run intelligence system once to create DB (TODO: add instructions)

---

## 📈 PROGRESS TRACKING

### Completed Sessions
1. **2026-01-11:** Dashboard health check and startup
   - ✅ Installed all dependencies
   - ✅ Created `.env` configuration
   - ✅ Restored databases from backup
   - ✅ Started main dashboard on port 8501
   - ✅ Created comprehensive documentation

### Current Session Goals
- [x] Verify dashboard is operational
- [x] Document all paths and commands
- [ ] Start intelligence dashboard
- [ ] Configure production credentials
- [ ] Set up process manager

---

## 🎯 SUCCESS METRICS

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Main Dashboard Uptime | >99% | Running | ✅ |
| Intelligence Dashboard | Running | Not started | ❌ |
| Luno Monitor | Running | Not started | ❌ |
| Database Size | <500MB | 144MB (2x72MB) | ✅ |
| Response Time | <2s | Unknown | ⏳ |
| Active Bots | 1+ | Unknown | ⏳ |
| Paper Trading Active | Yes | Unknown | ⏳ |

---

## 📞 TROUBLESHOOTING CHECKLIST

When something doesn't work:
1. ✅ Am I in `/home/user/Cryptobot`? (`pwd`)
2. ✅ Is Python 3.11.14 available? (`python3 --version`)
3. ✅ Are dependencies installed? (`python3 -c "import streamlit"`)
4. ✅ Does `.env` exist? (`ls -la .env`)
5. ✅ Do databases exist? (`ls -lh data/*.db`)
6. ✅ Are there port conflicts? (`ss -tulpn | grep 8501`)
7. ✅ What do logs say? (`tail -50 dashboard.log`)

---

## 🔄 NEXT UPDATE SCHEDULE

This document should be updated:
- ✅ After completing any task from backlog
- ✅ When adding new features or files
- ✅ When encountering and solving new issues
- ✅ When system paths or configuration changes
- ✅ At the start of each new working session

**Last Updated By:** Claude AI Assistant
**Next Update:** When next task is started

---

## 📚 RELATED DOCUMENTATION

- [DASHBOARD_STATUS_REPORT.md](./DASHBOARD_STATUS_REPORT.md) - Current dashboard status
- [AI_HANDOVER.md](./AI_HANDOVER.md) - AI context for continuity
- [PRODUCT_STRATEGY_2026.md](./PRODUCT_STRATEGY_2026.md) - Product roadmap
- [VPS_DEPLOYMENT_GUIDE_V3.md](./VPS_DEPLOYMENT_GUIDE_V3.md) - Deployment guide
- [MASTER_ROADMAP_AND_ARCHITECTURE.md](./MASTER_ROADMAP_AND_ARCHITECTURE.md) - Architecture

---

**🎯 REMEMBER: Always `cd /home/user/Cryptobot` first!**
