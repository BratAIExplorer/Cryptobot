#!/bin/bash
# 🔧 Setup systemd service for crypto bot

echo "================================================"
echo "🔧 Setting up Systemd Service"
echo "================================================"

# Get absolute path to bot directory
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER=$(whoami)

echo "Bot Directory: $BOT_DIR"
echo "Running as user: $USER"
echo ""

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/cryptobot.service"

echo "Creating service file: $SERVICE_FILE"

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Crypto Trading Bot (Paper Mode)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/run_bot.py

# Auto-restart configuration
Restart=always
RestartSec=10

# Environment variables (optional - can also use .env file)
# Environment=TELEGRAM_BOT_TOKEN=your_token_here
# Environment=TELEGRAM_CHAT_ID=your_chat_id_here
# Environment=CRYPTOPANIC_API_KEY=your_key_here

# Logging
StandardOutput=append:$BOT_DIR/logs/bot_systemd.log
StandardError=append:$BOT_DIR/logs/bot_systemd_error.log

# Security (optional but recommended)
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"
echo ""

# Create logs directory if doesn't exist
mkdir -p "$BOT_DIR/logs"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service (start on boot)
echo "Enabling service..."
sudo systemctl enable cryptobot

echo ""
echo "================================================"
echo "✅ Systemd service installed successfully!"
echo "================================================"
echo ""
echo "📝 COMMANDS:"
echo "   Start:   sudo systemctl start cryptobot"
echo "   Stop:    sudo systemctl stop cryptobot"
echo "   Restart: sudo systemctl restart cryptobot"
echo "   Status:  sudo systemctl status cryptobot"
echo "   Logs:    journalctl -u cryptobot -f"
echo ""
echo "🔍 To start the bot now:"
echo "   sudo systemctl start cryptobot"
echo ""
