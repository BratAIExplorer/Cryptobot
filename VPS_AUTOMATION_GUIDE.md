# 🤖 VPS Automation Guide - Minimal Manual Intervention Setup

This guide will help you set up **automated performance monitoring** for your crypto trading bot with minimal manual work required.

---

## 📋 Overview

**What gets automated:**
- ✅ Daily performance data export from your VPS database
- ✅ Automatic Git commits with performance reports
- ✅ Push to your Git repository (optional)
- ✅ Clean-up of old reports (keeps last 30 days)

**What you'll do:**
- 🕐 **One-time setup**: 10-15 minutes on VPS
- 🕐 **Weekly/monthly**: Share reports with Claude for analysis (2-3 minutes)

---

## 🚀 Step-by-Step Setup

### **Part 1: Local Testing (Do This First!)**

Before deploying to VPS, test on your local machine:

1. **Open PowerShell/Terminal** in your bot directory:
   ```bash
   cd C:\CryptoBot_Project
   ```

2. **Test the export script**:
   ```bash
   python export_performance.py data/trades_v3.db performance_reports
   ```

3. **Check the output**:
   - You should see a new `performance_reports/` folder
   - Files created:
     - `latest_performance.json` (main report)
     - `summary.txt` (human-readable)
     - `performance_YYYY-MM-DD.json` (dated archive)

4. **Commit to Git** (first time):
   ```bash
   git add .gitignore
   git add export_performance.py
   git add vps_auto_sync.sh
   git add setup_vps_automation.sh
   git add VPS_AUTOMATION_GUIDE.md
   git add performance_reports/
   git commit -m "Add automated performance monitoring system"
   git push
   ```

✅ **If this works, proceed to Part 2!**

---

### **Part 2: VPS Deployment**

1. **SSH into your VPS** (use PuTTY or Terminal):
   ```bash
   ssh root@your-vps-ip
   ```

2. **Navigate to your bot directory**:
   ```bash
   cd ~/CryptoBot_Project  # or wherever your bot is located
   ```

3. **Pull latest code from Git**:
   ```bash
   git pull
   ```

4. **Run the automated setup script**:
   ```bash
   bash setup_vps_automation.sh
   ```

5. **Follow the prompts**:
   - Choose sync frequency (recommend: Every 6 hours)
   - Enter Git credentials if prompted
   - The script will test everything automatically

6. **Verify cron job was created**:
   ```bash
   crontab -l
   ```
   You should see a line like:
   ```
   0 */6 * * * /root/CryptoBot_Project/vps_auto_sync.sh >> /var/log/bot_sync.log 2>&1
   ```

---

### **Part 3: Verification**

1. **Check that the first report was created**:
   ```bash
   ls -la performance_reports/
   cat performance_reports/summary.txt
   ```

2. **Verify Git push worked**:
   ```bash
   git log -1
   ```
   Should show the auto-sync commit.

3. **Monitor the cron logs** (optional):
   ```bash
   tail -f /var/log/bot_sync.log
   ```

4. **Pull reports to your local machine**:
   ```bash
   # On your local machine:
   cd C:\CryptoBot_Project
   git pull
   ```

✅ **Done! Your VPS now automatically exports performance data every 6 hours!**

---

## 📊 How to Work with Claude

### **Weekly/Monthly Workflow (5 minutes):**

1. **Pull latest reports** from Git:
   ```bash
   cd C:\CryptoBot_Project
   git pull
   ```

2. **Share with Claude**:
   In your conversation with Claude, simply say:
   > "Analyze my bot performance. The reports are in C:\CryptoBot_Project\performance_reports\"

3. **Claude will:**
   - Read the latest performance data
   - Analyze profitability, win rates, bot performance
   - Identify issues or opportunities
   - Suggest code improvements

4. **If Claude suggests changes:**
   - Review the code changes locally
   - Test if needed
   - Commit and push to Git
   - On VPS: `git pull` to deploy

---

## 🔧 Manual Operations (If Needed)

### **Manually trigger sync on VPS:**
```bash
cd ~/CryptoBot_Project
./vps_auto_sync.sh
```

### **Check cron logs:**
```bash
tail -50 /var/log/bot_sync.log
```

### **Disable auto-push** (commit locally, push manually):
Edit `vps_auto_sync.sh` and comment out the push section:
```bash
# Step 5: Push to remote (optional - comment out if you want manual control)
# echo -e "${YELLOW}🚀 Pushing to Git repository...${NC}"
# git push origin main
```

### **Change sync frequency:**
```bash
crontab -e
```
Modify the schedule:
- Every 6 hours: `0 */6 * * *`
- Every 12 hours: `0 */12 * * *`
- Daily at midnight: `0 0 * * *`
- Twice daily (8am & 8pm): `0 8,20 * * *`

---

## 📁 What Gets Tracked in Git

**✅ Included in Git:**
- `performance_reports/latest_performance.json` (always current)
- `performance_reports/summary.txt` (human-readable)
- Recent dated reports (last ~30 days)

**❌ Excluded from Git:**
- `data/*.db` (databases with sensitive trading data)
- `*.log` files
- `.env` files (API keys)
- Old reports (auto-cleaned after 30 days)

---

## 🛟 Troubleshooting

### **Problem: Export script fails on VPS**
```bash
# Check Python dependencies
pip3 install -r requirements.txt

# Test manually
python3 export_performance.py data/trades_v3.db performance_reports
```

### **Problem: Git push fails (authentication)**
```bash
# Set up Git credentials
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# For GitHub, use Personal Access Token instead of password
git remote set-url origin https://YOUR_TOKEN@github.com/username/repo.git
```

### **Problem: Cron job not running**
```bash
# Check cron service is running
sudo service cron status

# View cron logs
grep CRON /var/log/syslog
```

### **Problem: Permission denied on VPS**
```bash
# Make scripts executable
chmod +x vps_auto_sync.sh
chmod +x setup_vps_automation.sh
chmod +x export_performance.py
```

---

## 🎯 Expected Workflow After Setup

### **Automated (No Work Required):**
- Every 6 hours: VPS exports performance → commits → pushes to Git
- Every 30 days: Old reports auto-deleted

### **You Do (Weekly/Monthly - 5 mins):**
1. `git pull` on local machine
2. Share with Claude: "Analyze my latest performance"
3. Review Claude's suggestions
4. If accepting changes: commit → push → `git pull` on VPS

### **Result:**
- 📉 **95% reduction in manual work**
- 📊 **Always have up-to-date performance data**
- 🤖 **Claude can analyze and improve continuously**
- 🔒 **Secure (no direct VPS access needed)**

---

## 🎓 Pro Tips

1. **Check reports regularly** - Even if automated, glance at `summary.txt` weekly

2. **Use GitHub/GitLab mobile app** - View reports on your phone anytime

3. **Set up Telegram alerts** - Your bot already supports this for critical events

4. **Create Git branches for experiments**:
   ```bash
   git checkout -b test-new-strategy
   # Test changes here
   git checkout main  # Switch back to stable
   ```

5. **Ask Claude proactively** - Don't wait for problems:
   - "Analyze this week's performance"
   - "Any optimization opportunities?"
   - "Review my Grid Bot settings"

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Share the error with Claude (paste exact error message)
3. Claude can help debug and fix issues

---

**🎉 Congratulations! Your bot is now on autopilot with minimal maintenance required!**
