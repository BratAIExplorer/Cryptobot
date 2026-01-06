# 🚀 Quick Start: Automated Performance Monitoring

**For:** Lumina/Antigravity CryptoIntel Hub
**Time Required:** 15 minutes
**Technical Level:** Non-technical (copy-paste commands)

---

## ✅ What You'll Get

After this setup:
- ✅ **Every 6 hours**: VPS exports performance data automatically
- ✅ **Every 6 hours**: Reports pushed to your Git repository
- ✅ **Anytime**: Pull reports locally and share with Claude for analysis
- ✅ **All 3 Pillars tracked**: Trading bots (Pillar B) + Intelligence scores (Pillar C)

---

## 📋 Step 1: Test Locally (Windows)

**On your local machine** (C:\CryptoBot_Project):

1. **Open PowerShell** and navigate to your project:
   ```powershell
   cd C:\CryptoBot_Project
   ```

2. **Run the export script**:
   ```powershell
   python export_performance.py data/trades_v3.db performance_reports
   ```

3. **Check the output**:
   ```powershell
   dir performance_reports
   type performance_reports\summary.txt
   ```

   You should see:
   - `latest_performance.json`
   - `summary.txt`
   - `performance_YYYY-MM-DD.json`

4. **Commit and push to Git**:
   ```powershell
   git add .
   git commit -m "Add automated monitoring system"
   git push
   ```

✅ **If this works, proceed to Step 2!**

---

## 📋 Step 2: Deploy to VPS (Linux)

1. **SSH into your Hostinger VPS**:
   ```bash
   ssh root@your-vps-ip
   ```

2. **Navigate to bot directory**:
   ```bash
   cd /Antigravity/antigravity/scratch/crypto_trading_bot
   ```

3. **Pull latest code from Git**:
   ```bash
   git pull
   ```

4. **Run the setup script** (one command does everything):
   ```bash
   bash setup_vps_automation.sh
   ```

5. **Follow the prompts**:
   - Choose option `1` (Every 6 hours)
   - Press Enter for default Git settings
   - Wait for automatic test

6. **Verify it worked**:
   ```bash
   # Check cron was created
   crontab -l

   # Check reports were generated
   ls -la performance_reports/

   # View the summary
   cat performance_reports/summary.txt
   ```

✅ **Done! Your VPS is now automated.**

---

## 📋 Step 3: Your New Weekly Workflow

**Every week (or whenever you want analysis):**

### On Your Local Machine (Windows):

1. **Pull latest reports**:
   ```powershell
   cd C:\CryptoBot_Project
   git pull
   ```

2. **Open conversation with Claude** and say:
   > "Analyze my bot performance. Reports are in C:\CryptoBot_Project\performance_reports\"

3. **Claude will:**
   - Read all performance data
   - Analyze trading performance
   - Review Intelligence scores
   - Suggest optimizations

4. **If Claude suggests code changes:**
   - Review the changes locally
   - Test if needed
   - Commit and push:
     ```powershell
     git add .
     git commit -m "Apply Claude optimizations"
     git push
     ```

5. **Deploy to VPS**:
   ```bash
   # SSH to VPS
   ssh root@your-vps-ip

   # Navigate and pull
   cd /Antigravity/antigravity/scratch/crypto_trading_bot
   git pull

   # Restart bot (if needed)
   pm2 restart crypto_bot
   ```

**That's it! 5-10 minutes per week.**

---

## 🔧 Common Operations

### **Check VPS Logs**
```bash
# SSH to VPS first
tail -f /var/log/bot_sync.log
```

### **Manual Sync (Skip Wait for Next Cron)**
```bash
cd /Antigravity/antigravity/scratch/crypto_trading_bot
./vps_auto_sync.sh
```

### **Check Bot Status**
```bash
pm2 status crypto_bot
pm2 logs crypto_bot --lines 50
```

### **View Latest Performance**
```bash
cat performance_reports/summary.txt
```

### **Change Sync Frequency**
```bash
crontab -e
# Edit the schedule:
# Every 6 hours: 0 */6 * * *
# Every 12 hours: 0 */12 * * *
# Daily at midnight: 0 0 * * *
```

---

## 🎯 What Gets Exported

### **Pillar B: Trading Bots (MEXC)**
- Open positions (symbol, entry price, P&L)
- Recent trades (last 7 days)
- Bot status for each strategy
- Win rate, realized/unrealized P&L
- Portfolio equity snapshot

### **Pillar C: Intelligence**
- Latest regulatory scores (XRP, ADA, SOL, etc.)
- Score breakdowns (regulatory, institutional, ecosystem, market)
- Recommendations (BUY, HOLD, AVOID)
- Confidence levels

### **System Health**
- Bot running status (via PM2)
- Database health
- Three Pillar system status

---

## 🛟 Troubleshooting

### **Problem: Export script fails**
```bash
# Check Python dependencies
pip3 install -r requirements.txt

# Test manually
python3 export_performance.py data/trades_v3_paper.db performance_reports
```

### **Problem: Git push fails**
```bash
# Set up credentials
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# For GitHub with token
git remote set-url origin https://YOUR_TOKEN@github.com/username/repo.git
```

### **Problem: Cron not running**
```bash
# Check cron service
sudo service cron status

# View cron jobs
crontab -l

# Check logs
grep CRON /var/log/syslog
```

### **Problem: Permission denied**
```bash
chmod +x vps_auto_sync.sh
chmod +x setup_vps_automation.sh
chmod +x export_performance.py
```

---

## 📊 Sample Workflow with Claude

**You (Weekly check-in):**
```
git pull
```
```
Analyze my latest bot performance and intelligence scores
```

**Claude:**
- Reads `performance_reports/latest_performance.json`
- Analyzes:
  - Grid Bot ETH: +100% in 2 weeks → "Performing excellently, consider scaling"
  - Buy-the-Dip: Clean slate testing → "Monitor for 2 more weeks"
  - XRP Intelligence: 70/100 (BUY) → "Strong regulatory score, consider allocation"
- Provides specific recommendations

**You:**
- Review Claude's analysis
- Ask follow-up questions
- Accept code improvements
- Deploy changes

---

## 🎓 Pro Tips

1. **Check reports before asking Claude** - Skim `summary.txt` to know what to ask

2. **Use specific questions**:
   - ❌ "How's my bot?"
   - ✅ "Why is Grid Bot ETH outperforming BTC? Should I rebalance?"

3. **Track Intelligence scores over time**:
   ```bash
   # Compare XRP scores from different dates
   cat performance_reports/performance_2025-12-25.json | grep XRP
   cat performance_reports/performance_2025-12-29.json | grep XRP
   ```

4. **Set up mobile notifications** (optional):
   - Your bot already has Telegram integration
   - Reports go to Git (check on GitHub mobile app)

5. **Create Git branches for experiments**:
   ```bash
   git checkout -b test-new-strategy
   # Test changes here without affecting main
   ```

---

## 📈 Success Metrics

After 1 week, you should see:
- ✅ 4-6 automatic commits in your Git repo
- ✅ Performance reports updating every 6 hours
- ✅ Complete data on all open/closed positions
- ✅ Intelligence scores for regulatory assets

After 1 month:
- ✅ Historical trend data (30+ reports)
- ✅ Pattern recognition from Claude
- ✅ Optimized bot parameters
- ✅ 95% reduction in manual monitoring time

---

## 🆘 Need Help?

1. **Check logs**: `/var/log/bot_sync.log`
2. **Read error message**: Copy exact error to Claude
3. **Ask Claude**: "I got this error when running vps_auto_sync.sh: [paste error]"

---

**🎉 You're all set! Your CryptoIntel Hub is now on autopilot with world-class AI analysis available anytime.**
