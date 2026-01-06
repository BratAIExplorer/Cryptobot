#!/bin/bash
###############################################################################
# VPS Automated Performance Sync Script
#
# This script runs on your VPS and automatically:
# 1. Exports performance data from the trading bot database
# 2. Commits the reports to your Git repository
# 3. Pushes to GitHub/GitLab
#
# Setup: Run this script via cron (daily or hourly)
# Example cron: 0 */6 * * * /path/to/vps_auto_sync.sh >> /var/log/bot_sync.log 2>&1
###############################################################################

# Configuration
# Default VPS path for Antigravity/Lumina project
BOT_DIR="/Antigravity/antigravity/scratch/crypto_trading_bot"
DB_PATH="$BOT_DIR/data/trades_v3_paper.db"  # Change to trades_v3_mexc_live.db when live
PYTHON_CMD="python3"
EXPORT_SCRIPT="$BOT_DIR/export_performance.py"
PM2_PROCESS_NAME="crypto_bot"  # Your PM2 process name

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🤖 VPS Auto-Sync Script"
echo "Time: $(date)"
echo "=========================================="

# Change to bot directory
cd "$BOT_DIR" || {
    echo -e "${RED}❌ Error: Cannot access $BOT_DIR${NC}"
    exit 1
}

# Step 1: Check bot health (via PM2)
echo -e "${YELLOW}🏥 Checking bot health status...${NC}"
if command -v pm2 &> /dev/null; then
    PM2_STATUS=$(pm2 status "$PM2_PROCESS_NAME" 2>/dev/null | grep -c "online")
    if [ "$PM2_STATUS" -eq 0 ]; then
        echo -e "${RED}⚠️  Warning: Bot is not running in PM2${NC}"
    else
        echo -e "${GREEN}✅ Bot is running (PM2)${NC}"
    fi
fi

# Step 2: Export performance data
echo -e "${YELLOW}📊 Exporting performance data (3 Pillars)...${NC}"
$PYTHON_CMD "$EXPORT_SCRIPT" "$DB_PATH" performance_reports

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Performance export successful${NC}"
else
    echo -e "${RED}❌ Performance export failed${NC}"
    exit 1
fi

# Step 3: Check if there are changes to commit
echo -e "${YELLOW}🔍 Checking for changes...${NC}"
git status --porcelain performance_reports/

if [ -z "$(git status --porcelain performance_reports/)" ]; then
    echo -e "${GREEN}✅ No changes detected (reports up to date)${NC}"
    exit 0
fi

# Step 4: Stage the performance reports
echo -e "${YELLOW}📝 Staging performance reports...${NC}"
git add performance_reports/latest_performance.json
git add performance_reports/summary.txt
git add performance_reports/performance_$(date +%Y-%m-%d).json

# Step 5: Commit with timestamp
COMMIT_MSG="🤖 Auto-sync performance data - $(date '+%Y-%m-%d %H:%M UTC')"
echo -e "${YELLOW}💾 Committing changes...${NC}"
git commit -m "$COMMIT_MSG"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Commit successful${NC}"
else
    echo -e "${RED}❌ Commit failed${NC}"
    exit 1
fi

# Step 6: Push to remote (optional - comment out if you want manual control)
echo -e "${YELLOW}🚀 Pushing to Git repository...${NC}"
git push origin main  # Change 'main' to your branch name if different

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Push successful${NC}"
else
    echo -e "${YELLOW}⚠️  Push failed (may need manual resolution)${NC}"
    # Don't exit with error - we still exported successfully
fi

echo "=========================================="
echo -e "${GREEN}✅ Auto-sync completed successfully!${NC}"
echo "=========================================="

# Optional: Clean up old archived reports (keep last 30 days)
echo -e "${YELLOW}🧹 Cleaning up old reports (older than 30 days)...${NC}"
find "$BOT_DIR/performance_reports" -name "performance_*.json" -type f -mtime +30 -delete
echo -e "${GREEN}✅ Cleanup complete${NC}"

exit 0
