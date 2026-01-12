# 🚀 CryptoBots V3 - Quick Start Guide

## ✅ What's Ready

All components are built and installed:
- ✅ Health Monitor
- ✅ 3 Trading Strategies (Buy @ DIP, Take Profit, Trend Following)
- ✅ Strategy Engine
- ✅ Configuration Manager (with encryption)
- ✅ Web Dashboard (Streamlit)
- ✅ Dependencies Installed

---

## 🎯 Launch the Dashboard (3 Steps)

### Option 1: Using Launcher (Recommended)
```bash
cd "c:\Users\user\OneDrive\Documents\CryptoBots V3-Jan2026"
python kickstart.py
# Select option 1 for Web Dashboard
```

### Option 2: Direct Launch
```bash
cd "c:\Users\user\OneDrive\Documents\CryptoBots V3-Jan2026"
streamlit run dashboard.py
```

The dashboard will open at: **http://localhost:8501**

---

## ⚙️ Configure Your Bot

### 1. **Set API Keys** (Optional for Testing)
Create/edit `.env` file:
```env
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true
```

**OR** use paper trading mode (no API keys needed!)

### 2. **Customize Strategies**
In the dashboard:
1. Go to **⚙️ Configuration** tab
2. Adjust parameters for each strategy
3. Enable/disable strategies
4. Click **💾 Save**

### 3. **Start Trading**
1. Go to **📊 Dashboard** tab
2. Review health status
3. Click **▶️ Start Bot**
4. Monitor performance!

---

## 🎛️ Dashboard Features

### Pages:
- **📊 Dashboard**: Health status, performance, bot controls
- **⚙️ Configuration**: Customize all strategy parameters
- **📈 Performance**: View trades and P&L (coming soon)
- **🏥 Health Monitor**: Detailed system status

### Controls:
- ▶️ Start Bot
- ⏸️ Pause Bot
- 🔄 Run Health Check
- 🚨 Emergency Stop

---

## 🔧 Customizable Parameters

### Buy @ DIP
- Dip Trigger: 1-15% (default: 5%)
- Cooldown: 1-24 hours (default: 4h)
- Position Size: 1-25% (default: 10%)
- Stop Loss: 0.5-5% (default: 2%)

### Take Profit
- Profit Target: 0.5-10% (default: 3%)
- Trailing Stop: 0.1-3% (default: 1%)
- Max Stop Loss: 0.5-5% (default: 2%)

### Trend Following
- Fast MA: 10-100 (default: 50)
- Slow MA: 50-300 (default: 200)
- Max Drawdown: 1-15% (default: 5%)

**All adjustable via web dashboard - No code changes!**

---

## 🛡️ Safety Features

1. **Health Monitor**: 5-point health check every 60s
2. **Emergency Stop**: Auto + manual triggers
3. **Position Limits**: Per-strategy and portfolio-wide
4. **Paper Trading**: Test without real money
5. **Encrypted Keys**: API credentials stored securely

---

## 📁 Project Files

```
CryptoBots V3-Jan2026/
├── kickstart.py           # ← Launch here
├── dashboard.py           # Web interface
├── health_monitor.py      # Safety system
├── strategy_engine.py     # Core trading logic
├── config_manager.py      # Settings manager
└── strategies/
    ├── buy_dip_strategy.py
    ├── take_profit_strategy.py
    └── trend_following_strategy.py
```

---

## 🎉 Next Steps

1. **Launch Dashboard**: `python kickstart.py`
2. **Explore UI**: Familiarize yourself with controls
3. **Test Paper Trading**: Run without API keys first
4. **Configure Strategies**: Adjust to your risk tolerance
5. **Go Live**: Add API keys when ready

---

## ❓ Quick Troubleshooting

**Dashboard won't load?**
```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

**Need help?**
- Check `walkthrough.md` for detailed documentation
- Review `README.md` for project overview
- Check health monitor: `python health_monitor.py --debug`

---

**You're all set! 🚀**
