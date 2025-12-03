#!/bin/bash
# Setup cron job to send Telegram reports every 4 hours

SCRIPT_DIR="/Antigravity/antigravity/scratch/crypto_trading_bot/scripts"

echo "Setting up 4-hour Telegram reports..."

# Create cron job entry
CRON_ENTRY="0 */4 * * * cd /Antigravity/antigravity/scratch/crypto_trading_bot && python3 scripts/telegram_report.py >> /var/log/telegram_report.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "telegram_report.py") && echo "⚠️  Cron job already exists" || {
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job added: Reports every 4 hours at :00 minutes"
}

# Test the script manually
echo ""
echo "📊 Testing Telegram report now..."
cd /Antigravity/antigravity/scratch/crypto_trading_bot
python3 scripts/telegram_report.py

echo ""
echo "✅ Setup complete!"
echo "Reports will be sent at: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00"
