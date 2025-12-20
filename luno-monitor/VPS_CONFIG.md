# VPS Configuration - Luno Monitor

## VPS Connection Details
- **VPS Host**: `root@srv1010193`
- **SSH Access**: `ssh root@srv1010193`

## Project Paths

### Luno Monitor
- **VPS Path**: `/root/luno-monitor`
- **Local Path**: `c:\CryptoBot_Project\luno-monitor`
- **Main Entry**: `/root/luno-monitor/main.py`
- **Dashboard**: `/root/luno-monitor/src/dashboard.py`

### Running Processes (as of Dec 15, 2025)
```
/root/luno-monitor/venv/bin/python3 src/dashboard.py
/usr/bin/python3 /Antigravity/antigravity/scratch/crypto_trading_bot/luno-monitor/main.py
```

## Deployment Commands

### Stop Bot
```bash
pkill -f 'luno-monitor/main.py'
```

### Start Bot
```bash
cd /root/luno-monitor
python3 main.py
```

### Deploy Files from Local to VPS
```bash
# From local machine (Git Bash/WSL)
scp <filename> root@srv1010193:/root/luno-monitor/
```

### Check Bot Status
```bash
ps aux | grep luno
```

## Quick Reference

### File Transfer
```bash
# Single file
scp c:\CryptoBot_Project\luno-monitor\config.py root@srv1010193:/root/luno-monitor/

# Directory
scp -r c:\CryptoBot_Project\luno-monitor\src root@srv1010193:/root/luno-monitor/
```

### VPS File Locations
- Config: `/root/luno-monitor/config.py`
- Environment: `/root/luno-monitor/.env`
- Alert State: `/root/luno-monitor/alert_state.json`
- Virtual Env: `/root/luno-monitor/venv`

## Notes
- Not a git repository (manual deployment required)
- Python 3.11 installed
- Virtual environment located at `/root/luno-monitor/venv`
