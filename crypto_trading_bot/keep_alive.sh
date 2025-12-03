#!/bin/bash
while true; do
    echo "🚀 Starting Bot..."
    
    # Log Rotation: Keep only last 10000 lines to prevent disk overflow
    if [ -f bot_output.log ]; then
        tail -n 10000 bot_output.log > bot_output.log.tmp && mv bot_output.log.tmp bot_output.log
    fi
    
    python3 -u run_bot.py >> bot_output.log 2>&1
    
    echo "⚠️ Bot crashed! Restarting in 5 seconds..."
    sleep 5
done
