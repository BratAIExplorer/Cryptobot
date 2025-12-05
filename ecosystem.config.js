module.exports = {
    apps: [{
        name: "crypto-bot",
        script: "run_bot.py",
        interpreter: "python3",
        watch: false,
        autorestart: true,
        restart_delay: 5000,
        max_restarts: 10,
        env: {
            "PYTHONUNBUFFERED": "1",
            "NODE_ENV": "production"
        }
    }]
}
