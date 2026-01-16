# 🚀 Enterprise Bot Management Platform - Architecture

**Date:** 2026-01-16
**Project:** CryptoBot V3 - Non-Technical Management Interface
**Status:** Design Phase
**Timeline:** 1-2 days development

---

## 📊 SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE BOT PLATFORM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────┐ │
│  │   Web App    │◄────┤  FastAPI     │◄────┤  Trading Bot    │ │
│  │  (React/     │     │  REST API    │     │  (run_bot.py)   │ │
│  │   Next.js)   │     │  (Backend)   │     │                 │ │
│  └──────────────┘     └──────────────┘     └─────────────────┘ │
│         │                     │                      │           │
│         │                     │                      │           │
│         ▼                     ▼                      ▼           │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────┐ │
│  │   Browser    │     │  PostgreSQL  │     │  SQLite         │ │
│  │  (Family/    │     │  (Users,     │     │  (Trades Data)  │ │
│  │   Friends)   │     │   Configs)   │     │                 │ │
│  └──────────────┘     └──────────────┘     └─────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ TECHNOLOGY STACK

### **Frontend**
- **Framework:** Next.js 14 (React 18)
- **UI Library:** Shadcn/ui + Tailwind CSS
- **Charts:** Recharts / TradingView Lightweight Charts
- **State Management:** React Query (TanStack Query)
- **Forms:** React Hook Form + Zod validation
- **Real-time:** Socket.IO client

### **Backend**
- **Framework:** FastAPI (Python 3.11+)
- **Auth:** JWT tokens (python-jose)
- **Database:** PostgreSQL 15+ (production) / SQLite (dev)
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic v2
- **Real-time:** Socket.IO (python-socketio)
- **Task Queue:** Celery + Redis (optional - for background jobs)

### **Deployment**
- **Web Server:** Nginx (reverse proxy)
- **Process Manager:** Systemd (FastAPI) + nohup (trading bot)
- **SSL:** Let's Encrypt (Certbot)
- **Monitoring:** PM2 (optional) or systemd journalctl

---

## 📁 PROJECT STRUCTURE

```
cryptobot-enterprise/
├── frontend/                    # Next.js frontend
│   ├── app/                    # App router (Next.js 14)
│   │   ├── (auth)/
│   │   │   ├── login/          # Login page
│   │   │   └── register/       # Registration page
│   │   ├── dashboard/          # Main dashboard
│   │   ├── bots/               # Bot management
│   │   ├── trades/             # Trade history
│   │   ├── analytics/          # Performance analytics
│   │   └── settings/           # User settings
│   ├── components/             # Reusable components
│   │   ├── charts/             # Chart components
│   │   ├── forms/              # Form components
│   │   └── ui/                 # UI primitives (shadcn)
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Helper functions
│   ├── public/                 # Static assets
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database connection
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── bot.py
│   │   │   ├── trade.py
│   │   │   └── config.py
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── bot.py
│   │   │   └── trade.py
│   │   ├── routers/            # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── bots.py
│   │   │   ├── trades.py
│   │   │   └── analytics.py
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── bot_service.py
│   │   │   └── trade_service.py
│   │   └── utils/              # Utilities
│   │       ├── security.py     # JWT, password hashing
│   │       └── bot_controller.py  # Bot start/stop control
│   ├── requirements.txt
│   └── alembic/                # Database migrations
│
├── shared/                      # Shared code
│   └── constants.py            # Shared constants
│
└── docs/
    ├── API_DOCUMENTATION.md    # API reference
    ├── USER_GUIDE.md           # End-user guide
    └── DEPLOYMENT_GUIDE.md     # Deployment instructions
```

---

## 🗄️ DATABASE SCHEMA

### **PostgreSQL (Platform Data)**

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- 'admin', 'user', 'viewer'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bots table (bot configurations per user)
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,  -- 'Grid', 'Buy-the-Dip', 'SMA'
    status VARCHAR(50) DEFAULT 'stopped',  -- 'running', 'stopped', 'paused'
    config JSONB NOT NULL,  -- Bot-specific configuration
    initial_balance DECIMAL(20, 8),
    current_balance DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- User sessions (optional - for session management)
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,  -- JWT ID
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Activity log (audit trail)
CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(255) NOT NULL,  -- 'bot_started', 'bot_stopped', 'trade_executed'
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **SQLite (Trading Data - Existing)**
```sql
-- trades table (already exists in /root/cryptobot_v3/data/multi/trades_paper.db)
-- No changes needed - backend will READ from this database
```

---

## 🔌 API ENDPOINTS

### **Authentication**
```
POST   /api/auth/register        # Create new user account
POST   /api/auth/login           # Login and get JWT token
POST   /api/auth/refresh         # Refresh JWT token
POST   /api/auth/logout          # Logout (invalidate token)
GET    /api/auth/me              # Get current user info
```

### **Bot Management**
```
GET    /api/bots                 # List all bots for current user
POST   /api/bots                 # Create new bot configuration
GET    /api/bots/{id}            # Get bot details
PUT    /api/bots/{id}            # Update bot configuration
DELETE /api/bots/{id}            # Delete bot
POST   /api/bots/{id}/start      # Start bot
POST   /api/bots/{id}/stop       # Stop bot
POST   /api/bots/{id}/restart    # Restart bot
GET    /api/bots/{id}/status     # Get bot status (running/stopped)
GET    /api/bots/{id}/logs       # Get bot logs (last N lines)
```

### **Trades**
```
GET    /api/trades               # List trades (with filters)
GET    /api/trades/{id}          # Get trade details
GET    /api/trades/summary       # Get P&L summary
GET    /api/trades/stats         # Get performance statistics
```

### **Analytics**
```
GET    /api/analytics/pnl        # P&L chart data
GET    /api/analytics/performance  # Performance metrics
GET    /api/analytics/symbols    # Per-symbol statistics
GET    /api/analytics/strategies # Per-strategy statistics
```

### **Admin (Admin Role Only)**
```
GET    /api/admin/users          # List all users
PUT    /api/admin/users/{id}     # Update user (activate/deactivate)
DELETE /api/admin/users/{id}     # Delete user
GET    /api/admin/activity       # View activity log
GET    /api/admin/system         # System health/status
```

### **WebSocket (Real-time)**
```
WS     /ws                       # WebSocket connection
       - Events: trade_executed, bot_status_changed, balance_updated
```

---

## 🔐 SECURITY

### **Authentication Flow**
1. User registers: `POST /api/auth/register`
2. User logs in: `POST /api/auth/login` → Returns JWT access token
3. Frontend stores token in memory (NOT localStorage for security)
4. All API requests include: `Authorization: Bearer <token>`
5. Token expires after 1 hour → Refresh token flow

### **Password Hashing**
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### **JWT Configuration**
```python
SECRET_KEY = "your-secret-key-here"  # From environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### **Role-Based Access Control (RBAC)**
- **Admin**: Full access (manage all users, bots, system)
- **User**: Manage own bots, view own trades
- **Viewer**: Read-only access (view bots/trades, no modifications)

---

## 🎨 UI/UX FEATURES

### **Dashboard Page**
- Portfolio overview card (total balance, P&L today, P&L all-time)
- Active bots list (name, status, balance, P&L)
- Recent trades table (last 20 trades)
- P&L chart (last 7 days)

### **Bot Management Page**
- List of all bots with quick actions (start/stop/edit)
- "Add New Bot" button
- Bot configuration modal:
  - Strategy selection (dropdown)
  - Symbol selection (multi-select)
  - Amount/budget inputs
  - Strategy-specific parameters
  - Save/Cancel buttons

### **Trade History Page**
- Searchable/filterable table
- Filters: Date range, Strategy, Symbol, Side (BUY/SELL)
- Pagination
- Export to CSV button

### **Analytics Page**
- P&L chart (time series)
- Win rate by strategy (pie chart)
- Top performing symbols (bar chart)
- Strategy comparison table

### **Settings Page**
- Profile settings (name, email, password change)
- Notification preferences
- Theme toggle (light/dark mode)
- Logout button

---

## 🚀 DEPLOYMENT PLAN

### **Phase 1: Local Development (Day 1)**
1. Setup FastAPI backend
2. Setup PostgreSQL database
3. Implement authentication
4. Build core API endpoints
5. Test with Postman/curl

### **Phase 2: Frontend Development (Day 1-2)**
1. Setup Next.js project
2. Implement auth pages (login/register)
3. Build dashboard components
4. Integrate with backend API
5. Test locally

### **Phase 3: VPS Deployment (Day 2)**
1. Install PostgreSQL on VPS
2. Deploy FastAPI backend (systemd service)
3. Build Next.js production bundle
4. Configure nginx reverse proxy:
   ```nginx
   # Frontend
   location / {
       proxy_pass http://localhost:3000;
   }

   # Backend API
   location /api/ {
       proxy_pass http://localhost:8000;
   }

   # WebSocket
   location /ws {
       proxy_pass http://localhost:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```
5. Setup SSL with Let's Encrypt
6. Start services

### **Phase 4: Testing (Day 2)**
1. Test user registration/login
2. Test bot creation/start/stop
3. Test trade viewing
4. Test mobile responsiveness
5. Invite family/friends for beta testing

---

## 📱 MOBILE SUPPORT

### **Progressive Web App (PWA)**
```json
// next.config.js
module.exports = {
  pwa: {
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development'
  }
}
```

**Features:**
- Add to home screen
- Offline support (cached data)
- Push notifications (future)

---

## 🔄 INTEGRATION WITH EXISTING BOT

### **Bot Control**
```python
# backend/app/utils/bot_controller.py

import subprocess
import os
import signal

class BotController:
    def __init__(self, bot_dir="/root/cryptobot_v3"):
        self.bot_dir = bot_dir
        self.pid_file = f"{bot_dir}/.bot.pid"

    def start_bot(self, bot_id: int, config: dict):
        """Start trading bot process"""
        # Generate run_bot.py with config
        # Run: nohup python3 -u run_bot.py > bot.log 2>&1 &
        # Save PID to .bot.pid
        pass

    def stop_bot(self, bot_id: int):
        """Stop trading bot process"""
        # Read PID from .bot.pid
        # Run: kill <PID>
        pass

    def get_status(self, bot_id: int):
        """Check if bot is running"""
        # Read PID from .bot.pid
        # Check if process exists: ps -p <PID>
        pass
```

### **Trade Data Access**
```python
# backend/app/services/trade_service.py

import sqlite3

class TradeService:
    def __init__(self, db_path="/root/cryptobot_v3/data/multi/trades_paper.db"):
        self.db_path = db_path

    def get_trades(self, user_id: int, filters: dict):
        """Fetch trades from SQLite"""
        conn = sqlite3.connect(self.db_path)
        # Query trades table
        # Apply filters (date range, strategy, symbol, etc.)
        # Return results
        pass
```

---

## 📊 NEXT STEPS

1. **Review this architecture** - User approval needed
2. **Create wireframes** - UI mockups for approval
3. **Start implementation** - Begin with backend + database
4. **Iterate** - Build, test, deploy in phases

**Estimated Timeline:**
- Backend + Auth: 6-8 hours
- Frontend + UI: 8-10 hours
- Deployment + Testing: 2-4 hours
- **Total: 16-22 hours** (split over 2 days)

---

**Questions?** Let me know if you want to:
- Modify the tech stack
- Add/remove features
- Change the deployment approach
- See UI mockups first
