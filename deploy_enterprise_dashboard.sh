#!/bin/bash
################################################################################
# PART B: Deploy Enterprise Dashboard
# Run this on VPS: bash deploy_enterprise_dashboard.sh
#
# Deploys:
# - Backend API (FastAPI) on port 8000
# - Frontend Web UI (Next.js) on port 3000
#
# Total time: ~30 minutes (depends on npm install speed)
################################################################################

set -e  # Exit on error

# Get VPS IP for configuration
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")

echo "========================================================================"
echo "🚀 PART B: Deploy Enterprise Dashboard"
echo "========================================================================"
echo ""
echo "This will deploy:"
echo "  • Backend API (FastAPI) → http://$VPS_IP:8000"
echo "  • Frontend Web UI (Next.js) → http://$VPS_IP:3000"
echo ""
echo "Prerequisites:"
echo "  ✅ Node.js installed (for frontend)"
echo "  ✅ PostgreSQL installed (for user database)"
echo "  ✅ Python 3.8+ (already have)"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
else
    echo "❌ Node.js not found"
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "✅ Node.js installed"
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm: v$NPM_VERSION"
else
    echo "❌ npm not found (should be installed with Node.js)"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version)
    echo "✅ PostgreSQL: $PG_VERSION"
else
    echo "❌ PostgreSQL not found"
    echo "Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo "✅ PostgreSQL installed and started"
fi

echo ""
cd ~/cryptobot_v3

################################################################################
# BACKEND SETUP
################################################################################

echo "========================================================================"
echo "📦 STEP 1: Setup Backend (FastAPI)"
echo "========================================================================"
echo ""

cd enterprise/backend

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✅ Backend dependencies installed"
echo ""

# Setup PostgreSQL database
echo "Setting up PostgreSQL database..."
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname='cryptobot_enterprise'" | grep -q 1 || \
    sudo -u postgres createdb cryptobot_enterprise
echo "✅ Database 'cryptobot_enterprise' ready"
echo ""

# Generate secret key
echo "Generating secret key..."
SECRET_KEY=$(openssl rand -hex 32)
echo "✅ Secret key generated"
echo ""

# Create .env file
echo "Creating backend .env file..."
cat > .env <<EOF
# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@localhost/cryptobot_enterprise

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Default Admin Account (CHANGE AFTER FIRST LOGIN!)
ADMIN_EMAIL=admin@cryptobot.local
ADMIN_PASSWORD=change_me_immediately
ADMIN_USERNAME=admin

# Bot Database (Read-Only Access)
BOT_DB_PATH=../../data/multi/trades_paper.db

# API Settings
ALLOWED_ORIGINS=http://localhost:3000,http://$VPS_IP:3000
EOF

echo "✅ Backend .env created"
echo ""

# Test backend starts
echo "Testing backend startup..."
timeout 10 python3 main.py > /tmp/backend_test.log 2>&1 &
BACKEND_TEST_PID=$!
sleep 5

if ps -p $BACKEND_TEST_PID > /dev/null; then
    echo "✅ Backend starts successfully"
    kill $BACKEND_TEST_PID 2>/dev/null || true
else
    echo "⚠️  Backend test had issues, check /tmp/backend_test.log"
fi
echo ""

# Start backend permanently
echo "Starting backend API..."
nohup python3 main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   Logs: ~/cryptobot_v3/enterprise/backend/logs/backend.log"
echo "   API docs: http://$VPS_IP:8000/docs"
echo ""

sleep 3

# Test backend is responding
echo "Testing backend API..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ Backend API is responding"
else
    echo "⚠️  Backend might not be ready yet, wait 30 seconds"
fi
echo ""

################################################################################
# FRONTEND SETUP
################################################################################

echo "========================================================================"
echo "📦 STEP 2: Setup Frontend (Next.js)"
echo "========================================================================"
echo ""

cd ~/cryptobot_v3/enterprise/frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies (this may take 5-10 minutes)..."
npm install
echo "✅ Frontend dependencies installed"
echo ""

# Create .env.local file
echo "Creating frontend .env.local file..."
cat > .env.local <<EOF
# Backend API URL
NEXT_PUBLIC_API_URL=http://$VPS_IP:8000
EOF

echo "✅ Frontend .env.local created"
echo ""

# Build production bundle
echo "Building production bundle (this may take 3-5 minutes)..."
npm run build
echo "✅ Frontend built successfully"
echo ""

# Start frontend
echo "Starting frontend server..."
nohup npm start > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   Logs: ~/cryptobot_v3/enterprise/frontend/logs/frontend.log"
echo "   Web UI: http://$VPS_IP:3000"
echo ""

sleep 5

# Test frontend is responding
echo "Testing frontend..."
if curl -s http://localhost:3000 | grep -q "<!DOCTYPE html>"; then
    echo "✅ Frontend is responding"
else
    echo "⚠️  Frontend might not be ready yet, wait 30 seconds"
fi
echo ""

################################################################################
# FIREWALL CONFIGURATION
################################################################################

echo "========================================================================"
echo "📦 STEP 3: Configure Firewall"
echo "========================================================================"
echo ""

# Check if ufw is installed
if command -v ufw &> /dev/null; then
    echo "Opening ports 3000 and 8000..."
    sudo ufw allow 3000/tcp comment 'Enterprise Dashboard Frontend'
    sudo ufw allow 8000/tcp comment 'Enterprise Dashboard Backend API'
    echo "✅ Firewall configured"
else
    echo "ℹ️  UFW not installed, skipping firewall config"
    echo "   If using cloud provider, open ports 3000 and 8000 in security groups"
fi
echo ""

################################################################################
# VERIFICATION
################################################################################

echo "========================================================================"
echo "🧪 STEP 4: Verification"
echo "========================================================================"
echo ""

# Check processes
echo "Checking running processes..."
if pgrep -f "main.py" > /dev/null; then
    echo "✅ Backend process running"
else
    echo "❌ Backend process not found"
fi

if pgrep -f "next start" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
    echo "✅ Frontend process running"
else
    echo "❌ Frontend process not found"
fi
echo ""

# Test endpoints
echo "Testing endpoints..."

# Backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API: http://$VPS_IP:8000 (healthy)"
else
    echo "⚠️  Backend API: Not responding yet"
fi

# Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend UI: http://$VPS_IP:3000 (accessible)"
else
    echo "⚠️  Frontend UI: Not responding yet"
fi
echo ""

################################################################################
# FIRST LOGIN INSTRUCTIONS
################################################################################

echo "========================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================================================"
echo ""
echo "🌐 Access Your Dashboard:"
echo ""
echo "   Web Interface: http://$VPS_IP:3000"
echo "   API Documentation: http://$VPS_IP:8000/docs"
echo ""
echo "🔐 First Login:"
echo ""
echo "   Email:    admin@cryptobot.local"
echo "   Password: change_me_immediately"
echo ""
echo "   ⚠️  IMPORTANT: Change password after first login!"
echo ""
echo "📊 What You Can Do:"
echo ""
echo "   ✅ View all trades and portfolio"
echo "   ✅ See real-time profit/loss"
echo "   ✅ Start/stop/restart bot (click buttons)"
echo "   ✅ Monitor bot status"
echo "   ✅ View strategy performance"
echo "   ✅ Access from phone/tablet/desktop"
echo ""
echo "📝 Process Management:"
echo ""
echo "   View backend logs:  tail -f ~/cryptobot_v3/enterprise/backend/logs/backend.log"
echo "   View frontend logs: tail -f ~/cryptobot_v3/enterprise/frontend/logs/frontend.log"
echo "   View bot logs:      tail -f ~/cryptobot_v3/logs/bot.log"
echo ""
echo "   Stop backend:  pkill -f 'main.py'"
echo "   Stop frontend: pkill -f 'next start'"
echo "   Stop bot:      pkill -f 'run_bot.py'"
echo ""
echo "   Restart all:   bash deploy_enterprise_dashboard.sh"
echo ""
echo "🔧 Troubleshooting:"
echo ""
echo "   If backend won't start:"
echo "     - Check PostgreSQL: sudo systemctl status postgresql"
echo "     - Check logs: tail -100 ~/cryptobot_v3/enterprise/backend/logs/backend.log"
echo ""
echo "   If frontend won't start:"
echo "     - Check Node.js: node --version"
echo "     - Check logs: tail -100 ~/cryptobot_v3/enterprise/frontend/logs/frontend.log"
echo "     - Rebuild: cd ~/cryptobot_v3/enterprise/frontend && npm run build"
echo ""
echo "   If can't login:"
echo "     - Check backend is running: curl http://localhost:8000/health"
echo "     - Check credentials: admin@cryptobot.local / change_me_immediately"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "   1. Open browser: http://$VPS_IP:3000"
echo "   2. Login with credentials above"
echo "   3. Change password immediately"
echo "   4. Explore dashboard features"
echo "   5. Try starting/stopping bot from UI"
echo ""
echo "🚨 Security Notes:"
echo ""
echo "   - Dashboard is accessible from any IP (not just localhost)"
echo "   - Use strong password after first login"
echo "   - Consider setting up HTTPS with nginx + Let's Encrypt"
echo "   - Consider IP whitelisting in firewall"
echo ""
echo "📚 Documentation:"
echo ""
echo "   Backend README:  ~/cryptobot_v3/enterprise/backend/README.md"
echo "   Frontend README: ~/cryptobot_v3/enterprise/frontend/README.md"
echo "   Full Analysis:   ~/cryptobot_v3/ENTERPRISE_DASHBOARD_COMPLETE_ANALYSIS.md"
echo ""
echo "========================================================================"
echo ""
