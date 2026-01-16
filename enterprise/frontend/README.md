# CryptoBot Enterprise Platform - Frontend

Next.js 14 web application for managing CryptoBot trading system.

## 🎨 Features

- **Authentication**: Login/register with JWT
- **Dashboard**: Real-time bot status and controls
- **Trading Data**: View trades, portfolio, and performance
- **Bot Control**: Start/stop/restart bot from UI
- **Responsive Design**: Mobile-friendly interface
- **Dark Mode**: Full dark mode support
- **Real-time Updates**: Auto-refresh every 30 seconds

## 📦 Installation

### 1. Install Dependencies

```bash
cd enterprise/frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
nano .env.local
```

**Required settings:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🚀 Production Build

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

### Deploy to VPS

```bash
# Build on VPS
cd /root/cryptobot_v3/enterprise/frontend
npm install
npm run build

# Serve with PM2 or systemd
pm2 start npm --name "cryptobot-frontend" -- start
# OR
sudo cp deployment/cryptobot-frontend.service /etc/systemd/system/
sudo systemctl enable cryptobot-frontend
sudo systemctl start cryptobot-frontend
```

## 🛣️ Routes

- `/` - Home (redirects to dashboard or login)
- `/login` - Login page
- `/register` - Registration page
- `/dashboard` - Main dashboard (protected)

## 🎨 UI Components

Built with:
- **Tailwind CSS** - Utility-first styling
- **Shadcn/ui** - High-quality React components
- **Radix UI** - Accessible component primitives
- **Lucide Icons** - Beautiful icon set

## 📱 Mobile Support

The interface is fully responsive and works on:
- Desktop (1920x1080+)
- Laptop (1366x768+)
- Tablet (768px+)
- Mobile (375px+)

## 🔐 Authentication Flow

1. User enters credentials on `/login`
2. Frontend sends POST to `/api/auth/login/json`
3. Backend returns JWT token
4. Token stored in localStorage
5. Token sent in Authorization header for all requests
6. Auto-redirect to `/login` if token expires (401)

## 📊 Data Flow

```
Frontend (Next.js)
  ↓
API Client (axios)
  ↓
Backend API (FastAPI)
  ↓
PostgreSQL (users) + SQLite (trades)
```

## 🧪 Testing

### Test Authentication

```bash
# Visit http://localhost:3000/login
# Use: admin@cryptobot.local / change_me_immediately
```

### Test Bot Control

1. Login to dashboard
2. Check bot status (should show current state)
3. Try start/stop buttons
4. Verify changes reflect immediately

### Test Data Display

1. Ensure bot has executed trades
2. Check portfolio summary displays correctly
3. Verify recent trades table populates
4. Confirm strategy performance shows

## 🐛 Troubleshooting

### Backend Connection Error

**Problem**: "Network Error" or "Failed to load data"

**Solution**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check NEXT_PUBLIC_API_URL in .env.local
# Should be: http://localhost:8000
```

### Login Fails with "Incorrect email or password"

**Solution**:
```bash
# Verify default admin exists in backend
# Check backend logs for errors
# Ensure PostgreSQL is running
```

### Data Not Showing

**Problem**: Dashboard shows "No trades" but bot has run

**Solution**:
```bash
# Check BOT_DB_PATH in backend .env
# Verify bot database exists:
ls -lh ../../data/multi/trades_paper.db

# Test backend endpoint directly:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/trades/portfolio
```

## 🔧 Development

### Add New Pages

```bash
# Create new route
mkdir src/app/my-page
touch src/app/my-page/page.tsx
```

### Add New Components

```bash
# Create component
touch src/components/MyComponent.tsx
```

### Add New API Calls

```typescript
// In src/lib/api.ts
async getMyData() {
  const response = await this.client.get('/api/my-endpoint');
  return response.data;
}
```

## 📝 License

Part of CryptoBot V3 project.
