module.exports = {
    apps: [
        {
            name: "crypto-bot",
            script: "/Antigravity/antigravity/scratch/crypto_trading_bot/run_bot.py",
            interpreter: "python3",
            watch: false,
            autorestart: true,
            restart_delay: 5000,
            max_restarts: 10,
            env: {
                "PYTHONUNBUFFERED": "1"
            }
        },
        {
            name: "dashboard",
            script: "streamlit",
            args: "run /Antigravity/antigravity/scratch/crypto_trading_bot/dashboard/app.py --server.port 8501",
            interpreter: "none",
            watch: false,
            autorestart: true,
            restart_delay: 10000,
            env: {
                "PYTHONUNBUFFERED": "1"
            }
        }
    ]
}
