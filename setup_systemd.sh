#!/bin/bash
# 🔧 INFRASTRUCTURE SCRIPT 1/4: Systemd Service Setup
# This makes the bot start automatically and restart on crashes

echo "========================================================================"
echo "🔧 INFRASTRUCTURE SETUP #1: Systemd Service"
echo "========================================================================"
echo ""
echo "📖 WHAT THIS DOES:"
echo "   • Makes bot start automatically when server boots"
echo "   • Auto-restarts bot if it crashes"
echo "   • Survives server reboots"
echo "   • Proper logging to systemd journal"
echo ""
echo "⏱️  Time needed: 2 minutes"
echo "🔒 Requires: sudo access"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Get absolute path to bot directory
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER=$(whoami)

echo ""
echo "Configuration:"
echo "   Bot Directory: $BOT_DIR"
echo "   User: $USER"
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

# Load environment variables from .env file (if exists)
EnvironmentFile=-$BOT_DIR/.env

# Logging
StandardOutput=append:$BOT_DIR/logs/bot_systemd.log
StandardError=append:$BOT_DIR/logs/bot_systemd_error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Create logs directory
mkdir -p "$BOT_DIR/logs"

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service (auto-start on boot)..."
sudo systemctl enable cryptobot

echo ""
echo "========================================================================"
echo "✅ Systemd service installed successfully!"
echo "========================================================================"
echo ""
echo "📝 COMMANDS TO USE:"
echo "   sudo systemctl start cryptobot     # Start the bot"
echo "   sudo systemctl stop cryptobot      # Stop the bot"
echo "   sudo systemctl restart cryptobot   # Restart the bot"
echo "   sudo systemctl status cryptobot    # Check status"
echo "   journalctl -u cryptobot -f         # View live logs"
echo ""
echo "🚀 To start now:"
echo "   sudo systemctl start cryptobot"
echo ""
