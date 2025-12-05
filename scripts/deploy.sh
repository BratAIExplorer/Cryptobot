# Run Database Migrations (Safety Check)
if [ -f "migrate_add_rsi_columns.py" ]; then
    echo "🛠️ Checking for DB updates..."
    python3 migrate_add_rsi_columns.py
fi

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart crypto_bot_runner.service
sudo systemctl restart crypto_bot.service
sudo systemctl restart portfolio_monitor.service

# Check status
echo ""
echo "✅ Deployment complete. Checking status..."
sleep 2
python3 scripts/check_status.py
