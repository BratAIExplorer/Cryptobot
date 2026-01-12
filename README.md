# CryptoBots V3 🤖💹

**Intelligent Crypto Trading Bot with Health Monitoring & Simple Proven Strategies**

## 🎯 Project Philosophy
- **Safety First**: Robust Health Monitor to prevent disasters
- **Simple Strategies**: No gambling, only proven low-risk approaches
- **Transparent**: Full backtesting with historical data
- **Modular**: Easy to add new strategies

---

## 🏥 Health Monitor Features
The bot constantly monitors itself to prevent failures:
- ✅ **Heartbeat System**: Checks every 60s to ensure the bot is alive
- ✅ **API Connectivity**: Detects 403, timeouts, and rate limits
- ✅ **Data Freshness**: Alerts if price data is stale (>10s old)
- ✅ **System Vitals**: CPU, RAM, Disk usage tracking
- ✅ **Emergency Kill Switch**: Auto-stop on rapid balance drops or manual override

---

## 📊 Trading Strategies

### 1. Buy @ DIP
- **Logic**: Buy when price drops 5% below recent 24h high
- **Risk**: Max 1 buy per 4 hours (avoid falling knives)

### 2. Sell @ X% (Take Profit)
- **Logic**: Exit at 3% profit with 1% trailing stop
- **Risk**: Always set -2% stop-loss

### 3. Simple Trend Following
- **Logic**: Golden Cross (50 MA > 200 MA) = BUY, Death Cross = SELL
- **Risk**: Max drawdown limit of 5%

---

## 🚀 Quick Start

### Installation
```bash
# 1. Clone the repository
cd "c:/Users/user/OneDrive/Documents/CryptoBots V3-Jan2026"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API keys
cp .env.example .env
# Edit .env with your actual API credentials
```

### Run Health Monitor
```bash
python health_monitor.py --debug
```
**Expected Output**:
```
🟢 [2026-01-12 21:20:00] Heartbeat: OK
🟢 [2026-01-12 21:20:00] API Connection: OK (Binance)
🟢 [2026-01-12 21:20:00] Data Latency: 0.8s
🟢 [2026-01-12 21:20:00] System: CPU 12% | RAM 45% | Disk 78%
```

### Run Backtest
```bash
# Test "Buy @ DIP" strategy on BTC/USDT (2024 data)
python backtest_engine.py --strategy buy_dip --symbol BTC/USDT --start 2024-01-01 --end 2024-12-31
```

---

## 📁 Project Structure
```
CryptoBots V3-Jan2026/
├── health_monitor.py          # Core monitoring module
├── backtest_engine.py          # Strategy backtesting framework
├── strategies/
│   ├── buy_dip_strategy.py     # Buy @ DIP logic
│   ├── take_profit_strategy.py # Take Profit + Trailing Stop
│   └── simple_trend_strategy.py # Moving Average crossover
├── tests/
│   ├── test_health_monitor.py
│   └── test_strategies.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚠️ Safety Rules
1. **Never trade with real money until backtested**: Validate strategies with 1+ year of historical data
2. **Always use stop-losses**: Every trade must have a maximum loss limit
3. **Start small**: Use 1-2% of capital per trade initially
4. **Monitor the Health Monitor**: Check `health_status.json` regularly

---

## 🛠️ Development Status
- [x] Research & Planning
- [x] Health Monitor Design
- [ ] Core Implementation (In Progress)
- [ ] Backtesting Framework
- [ ] Live Trading Integration

---

## 📚 Resources
- [CCXT Documentation](https://docs.ccxt.com/)
- [QuantConnect Learning](https://www.quantconnect.com/learning)
- [CryptoQuant On-Chain Data](https://cryptoquant.com/)

---

## 📝 License
Private Project - All Rights Reserved
