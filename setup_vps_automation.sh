#!/bin/bash
###############################################################################
# VPS Automation Setup Script
#
# Run this ONCE on your VPS to set up automated performance reporting
# Usage: bash setup_vps_automation.sh
###############################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "🔧 VPS Automation Setup"
echo "=========================================="

# Get the current directory
CURRENT_DIR=$(pwd)
echo "📁 Bot directory: $CURRENT_DIR"

# Step 1: Make scripts executable
echo -e "${YELLOW}🔒 Making scripts executable...${NC}"
chmod +x vps_auto_sync.sh
chmod +x export_performance.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Scripts are now executable${NC}"
else
    echo -e "${RED}❌ Failed to set permissions${NC}"
    exit 1
fi

# Step 2: Test the export script
echo -e "${YELLOW}🧪 Testing performance export script...${NC}"
python3 export_performance.py data/trades_v3.db performance_reports

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Export script works correctly${NC}"
else
    echo -e "${RED}❌ Export script failed. Check Python dependencies.${NC}"
    echo "   Try: pip3 install -r requirements.txt"
    exit 1
fi

# Step 3: Set up cron job
echo ""
echo -e "${YELLOW}📅 Setting up cron job...${NC}"
echo ""
echo "Choose how often you want to sync performance data:"
echo "1) Every 6 hours (recommended)"
echo "2) Every 12 hours"
echo "3) Daily (at midnight UTC)"
echo "4) Manual setup (skip cron)"
echo ""
read -p "Enter choice [1-4]: " choice

CRON_SCHEDULE=""
case $choice in
    1)
        CRON_SCHEDULE="0 */6 * * *"
        echo "✅ Selected: Every 6 hours"
        ;;
    2)
        CRON_SCHEDULE="0 */12 * * *"
        echo "✅ Selected: Every 12 hours"
        ;;
    3)
        CRON_SCHEDULE="0 0 * * *"
        echo "✅ Selected: Daily at midnight"
        ;;
    4)
        echo "⚠️  Skipping cron setup. You can run manually with: ./vps_auto_sync.sh"
        CRON_SCHEDULE=""
        ;;
    *)
        echo -e "${RED}Invalid choice. Skipping cron setup.${NC}"
        CRON_SCHEDULE=""
        ;;
esac

if [ -n "$CRON_SCHEDULE" ]; then
    # Create cron job
    CRON_JOB="$CRON_SCHEDULE $CURRENT_DIR/vps_auto_sync.sh >> /var/log/bot_sync.log 2>&1"

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "vps_auto_sync.sh"; then
        echo -e "${YELLOW}⚠️  Cron job already exists. Skipping.${NC}"
    else
        # Add cron job
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Cron job added successfully${NC}"
            echo "   Schedule: $CRON_SCHEDULE"
            echo "   Log file: /var/log/bot_sync.log"
        else
            echo -e "${RED}❌ Failed to add cron job${NC}"
        fi
    fi
fi

# Step 4: Update vps_auto_sync.sh with correct path
echo -e "${YELLOW}📝 Updating vps_auto_sync.sh with correct path...${NC}"
sed -i "s|BOT_DIR=\".*\"|BOT_DIR=\"$CURRENT_DIR\"|g" vps_auto_sync.sh
echo -e "${GREEN}✅ Path updated${NC}"

# Step 5: Configure Git (if not already done)
echo ""
echo -e "${YELLOW}🔐 Checking Git configuration...${NC}"

GIT_USER=$(git config user.name)
GIT_EMAIL=$(git config user.email)

if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
    echo -e "${YELLOW}⚠️  Git user not configured. Please set it up:${NC}"
    echo ""
    read -p "Enter your Git username: " git_username
    read -p "Enter your Git email: " git_email

    git config --global user.name "$git_username"
    git config --global user.email "$git_email"

    echo -e "${GREEN}✅ Git configured${NC}"
else
    echo -e "${GREEN}✅ Git already configured (User: $GIT_USER)${NC}"
fi

# Step 6: Create performance_reports directory
echo -e "${YELLOW}📁 Creating performance_reports directory...${NC}"
mkdir -p performance_reports

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Directory created${NC}"
else
    echo -e "${RED}❌ Failed to create directory${NC}"
fi

# Step 7: Test the full sync script
echo ""
echo -e "${YELLOW}🧪 Testing full sync script...${NC}"
./vps_auto_sync.sh

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Sync test successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Sync test had warnings (check output above)${NC}"
fi

# Final summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ VPS Automation Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📋 What was set up:"
echo "   ✅ Performance export script"
echo "   ✅ Automated sync script"
if [ -n "$CRON_SCHEDULE" ]; then
    echo "   ✅ Cron job ($CRON_SCHEDULE)"
fi
echo ""
echo "📖 Next Steps:"
echo "   1. Check that reports are in: $CURRENT_DIR/performance_reports/"
echo "   2. Verify Git push worked: git log"
if [ -n "$CRON_SCHEDULE" ]; then
    echo "   3. Monitor cron logs: tail -f /var/log/bot_sync.log"
fi
echo "   4. Share reports with Claude whenever you need analysis!"
echo ""
echo "🔄 To manually trigger sync: ./vps_auto_sync.sh"
echo "=========================================="
