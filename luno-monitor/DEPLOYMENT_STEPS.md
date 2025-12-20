# Deployment Steps - Copy Files to VPS

## Method 1: Using WinSCP (Recommended for Windows)

### Download WinSCP
1. Download from: https://winscp.net/eng/download.php
2. Install and open WinSCP

### Connect to VPS
1. **Host name**: `srv1010193`
2. **User name**: `root`
3. **Password**: (your VPS root password)
4. Click **Login**

### Transfer Files
1. **Left panel** (Local): Navigate to `c:\CryptoBot_Project\luno-monitor`
2. **Right panel** (VPS): Navigate to `/root/luno-monitor`
3. Copy these 6 files from left to right:
   - `config.py`
   - `alert_state_manager.py`
   - `main.py`
   - `src/currency_converter.py`
   - `src/price_monitor.py`
   - `src/portfolio_analyzer.py`
4. When prompted to overwrite, click **Yes**

---

## Method 2: Using SCP Command (Git Bash/WSL/PowerShell)

Open Git Bash or WSL on your Windows machine and run:

```bash
cd /c/CryptoBot_Project/luno-monitor

# Copy files one by one
scp config.py root@srv1010193:/root/luno-monitor/
scp alert_state_manager.py root@srv1010193:/root/luno-monitor/
scp main.py root@srv1010193:/root/luno-monitor/
scp src/currency_converter.py root@srv1010193:/root/luno-monitor/src/
scp src/price_monitor.py root@srv1010193:/root/luno-monitor/src/
scp src/portfolio_analyzer.py root@srv1010193:/root/luno-monitor/src/
```

**You'll be prompted for the VPS password 6 times** (once per file)

---

## Method 3: Using PowerShell SCP (Windows 10/11)

Open PowerShell and run:

```powershell
cd C:\CryptoBot_Project\luno-monitor

scp config.py root@srv1010193:/root/luno-monitor/
scp alert_state_manager.py root@srv1010193:/root/luno-monitor/
scp main.py root@srv1010193:/root/luno-monitor/
scp src/currency_converter.py root@srv1010193:/root/luno-monitor/src/
scp src/price_monitor.py root@srv1010193:/root/luno-monitor/src/
scp src/portfolio_analyzer.py root@srv1010193:/root/luno-monitor/src/
```

---

## After Transfer - Restart Bot on VPS

Run these commands on your VPS:

```bash
# Stop old bot
pkill -f 'luno-monitor/main.py'

# Verify files were copied
cd /root/luno-monitor
ls -lh config.py main.py alert_state_manager.py
ls -lh src/currency_converter.py src/price_monitor.py src/portfolio_analyzer.py

# Restart bot
cd /root/luno-monitor
python3 main.py
```

---

## Verify Success

You should see:
```
Profit targets: [20.0, 35.0, 50.0]%  ✅ CORRECT
```

NOT:
```
Profit targets: [10.0, 15.0, 20.0, 25.0]%  ❌ OLD VERSION
```
