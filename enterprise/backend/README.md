# CryptoBot Enterprise Platform - Backend

FastAPI-based REST API for managing CryptoBot trading system.

## 🏗️ Architecture

This backend is **completely isolated** from the main trading bot:

- **Separate Database**: Uses PostgreSQL for user management (bot uses SQLite for trades)
- **Read-Only Access**: Only reads from bot's database, never modifies it
- **Independent**: Can start/stop without affecting trading bot
- **Different Port**: Runs on port 8000 (bot runs independently)

## 📦 Installation

### 1. Install Dependencies

```bash
cd enterprise/backend
pip install -r requirements.txt
```

### 2. Setup PostgreSQL

```bash
# Install PostgreSQL (if not already installed)
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb cryptobot_enterprise

# Create user (optional)
sudo -u postgres createuser cryptobot_user
sudo -u postgres psql -c "ALTER USER cryptobot_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cryptobot_enterprise TO cryptobot_user;"
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Required settings:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `ADMIN_EMAIL` and `ADMIN_PASSWORD`: Default admin credentials
- `BOT_DB_PATH`: Path to bot's SQLite database (read-only)

### 4. Initialize Database

Database tables are created automatically on first run.

## 🚀 Running

### Development Mode

```bash
# Auto-reload on code changes
python main.py
```

### Production Mode

```bash
# Using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using systemd (recommended)
sudo cp deployment/cryptobot-api.service /etc/systemd/system/
sudo systemctl enable cryptobot-api
sudo systemctl start cryptobot-api
```

## 📚 API Documentation

Once running, access interactive API docs at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Get Access Token

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@cryptobot.local", "password": "change_me_immediately"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Use Token in Requests

```bash
curl http://localhost:8000/api/bots/status \
  -H "Authorization: Bearer eyJhbGc..."
```

## 🛣️ API Endpoints

### Authentication (`/api/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (OAuth2 form)
- `POST /auth/login/json` - Login (JSON)
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### Users (`/api/users`)
- `GET /users/` - List users (admin only)
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user (admin only)
- `GET /users/{id}/activity` - Get activity log

### Bots (`/api/bots`)
- `GET /bots/status` - Get bot status (running/stopped)
- `POST /bots/start` - Start bot
- `POST /bots/stop` - Stop bot
- `POST /bots/restart` - Restart bot
- `GET /bots/configs` - List bot configurations
- `POST /bots/configs` - Create bot config
- `PUT /bots/configs/{id}` - Update config
- `DELETE /bots/configs/{id}` - Delete config

### Trades (`/api/trades`)
- `GET /trades/` - Get trade history (paginated)
- `GET /trades/count` - Get trade count
- `GET /trades/recent` - Get recent trades (last N hours)
- `GET /trades/portfolio` - Get portfolio summary
- `GET /trades/performance` - Get strategy performance

## 🔒 Security

### Default Admin Account

**⚠️ IMPORTANT**: Change the default admin password immediately!

```bash
# After first login, update password via API
curl -X PUT http://localhost:8000/api/users/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "your_new_secure_password"}'
```

### Role-Based Access Control (RBAC)

- **admin**: Full access (user management, all bots)
- **user**: Own bots only, trading data access
- **viewer**: Read-only access (no bot control)

### Best Practices

1. Use HTTPS in production (nginx with Let's Encrypt)
2. Keep SECRET_KEY secure (never commit to git)
3. Use strong passwords (minimum 8 characters)
4. Regularly rotate admin credentials
5. Review activity logs for suspicious actions

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application
├── database.py             # Database connection
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── auth.py                # JWT authentication
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── api/
│   ├── auth.py           # Auth endpoints
│   ├── users.py          # User management
│   ├── bots.py           # Bot control
│   └── trades.py         # Trading data
└── utils/
    └── bot_reader.py     # Read-only bot database access
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Test Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### Test Bot Status

```bash
TOKEN="your_access_token_here"

curl http://localhost:8000/api/bots/status \
  -H "Authorization: Bearer $TOKEN"
```

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d cryptobot_enterprise
```

### Bot Database Not Found

```bash
# Check BOT_DB_PATH in .env points to correct location
# Default: ../../data/multi/trades_paper.db

# Verify file exists
ls -lah ../../data/multi/trades_paper.db
```

### Import Errors

```bash
# Ensure you're in the backend directory
cd enterprise/backend

# Python path might need adjustment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py
```

## 🚢 Deployment

See `docs/ENTERPRISE_ARCHITECTURE.md` for full deployment guide including:

- nginx reverse proxy setup
- SSL certificate configuration
- systemd service management
- Production environment variables

## 📝 License

Part of CryptoBot V3 project.
