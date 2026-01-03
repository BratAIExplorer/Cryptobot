# Add these to your ~/.bashrc for quick access:

alias bot-status='sudo systemctl status cryptobot'
alias bot-start='sudo systemctl start cryptobot'
alias bot-stop='sudo systemctl stop cryptobot'
alias bot-restart='sudo systemctl restart cryptobot'
alias bot-logs='tail -f /Antigravity/antigravity/scratch/crypto_trading_bot/logs/bot_*.log'
alias bot-monitor='/Antigravity/antigravity/scratch/crypto_trading_bot/scripts/monitor.sh'
alias bot-watch='watch -n 60 /Antigravity/antigravity/scratch/crypto_trading_bot/scripts/monitor.sh'
