#!/bin/bash
# Single-instance wrapper for run_bot.py

PIDFILE="/tmp/cryptobot.pid"
BOTDIR="/Antigravity/antigravity/scratch/crypto_trading_bot"

# Check if already running
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Bot already running (PID: $OLD_PID). Exiting."
        exit 0
    else
        echo "Stale PID file found. Removing."
        rm -f "$PIDFILE"
    fi
fi

# Kill any existing run_bot.py processes
pkill -9 -f "python.*run_bot.py" || true
sleep 1

# Start bot and save PID
cd "$BOTDIR"
/usr/bin/python3 -u run_bot.py &
echo $! > "$PIDFILE"

# Wait for bot to exit
wait

# Clean up PID file
rm -f "$PIDFILE"
