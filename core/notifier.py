import requests

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage" if token else None

    def send_message(self, message):
        """Send a message to the configured Telegram chat."""
        if not self.token or not self.chat_id:
            print(f"[Notifier] No token/chat_id configured. Message skipped: {message}")
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.base_url, json=payload, timeout=5)
            if response.status_code == 200:
                return True
            else:
                print(f"[Notifier] Error sending message: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Exception: {e}")
            return False

    def notify_trade(self, symbol, side, price, amount, reason=""):
        """Format and send a trade notification."""
        icon = "🟢" if side == "BUY" else "🔴"
        msg = f"{icon} *{side} {symbol}*\n" \
              f"Price: `${price:.4f}`\n" \
              f"Amount: `{amount:.4f}`\n" \
              f"Reason: _{reason}_"
        self.send_message(msg)
    
    # ==================== CRITICAL ALERTS ====================
    
    def alert_circuit_breaker(self, error_count, auto_recovery_minutes=30):
        """Alert when circuit breaker is triggered."""
        msg = f"🔴 *CIRCUIT BREAKER TRIGGERED*\n\n" \
              f"⚠️ Bot has been paused due to {error_count} consecutive errors.\n" \
              f"⏰ Auto-recovery in {auto_recovery_minutes} minutes.\n\n" \
              f"Check logs for details: `journalctl -u crypto_bot_runner -f`"
        self.send_message(msg)
    
    def alert_max_drawdown(self, current_pct, max_pct, current_equity, peak_equity):
        """Alert when approaching or hitting max drawdown limit."""
        if current_pct >= max_pct:
            icon = "🚨"
            status = "MAX DRAWDOWN HIT - BOT PAUSED"
        else:
            icon = "⚠️"
            status = "DRAWDOWN WARNING"
        
        msg = f"{icon} *{status}*\n\n" \
              f"Current Drawdown: `{current_pct:.1f}%`\n" \
              f"Max Allowed: `{max_pct:.0f}%`\n" \
              f"Peak Equity: `${peak_equity:,.2f}`\n" \
              f"Current Equity: `${current_equity:,.2f}`\n\n" \
              f"Loss: `${peak_equity - current_equity:,.2f}`"
        self.send_message(msg)
    
    def alert_no_activity(self, hours):
        """Alert when bot hasn't traded for specified hours."""
        msg = f"⏰ *NO TRADING ACTIVITY*\n\n" \
              f"Bot hasn't made any trades in the last {hours} hours.\n\n" \
              f"Possible reasons:\n" \
              f"• No market opportunities\n" \
              f"• Exposure limits reached\n" \
              f"• Circuit breaker active\n\n" \
              f"Check status: http://srv1010193:8501"
        self.send_message(msg)
    
    def alert_service_restart(self):
        """Notify when bot service restarts."""
        msg = f"🔄 *BOT SERVICE RESTARTED*\n\n" \
              f"The trading bot has been restarted.\n" \
              f"All strategies are initializing...\n\n" \
              f"Status: ✅ Running"
        self.send_message(msg)
    
    def alert_large_loss(self, symbol, loss_amount, loss_pct):
        """Alert on significant single trade loss."""
        msg = f"💥 *LARGE LOSS ALERT*\n\n" \
              f"Symbol: `{symbol}`\n" \
              f"Loss: `${loss_amount:.2f}` ({loss_pct:.1f}%)\n\n" \
              f"Review trade details on dashboard."
        self.send_message(msg)
    
    def send_daily_summary(self, stats):
        """Send daily performance summary."""
        msg = f"📊 *DAILY SUMMARY*\n\n" \
              f"Date: `{stats['date']}`\n" \
              f"Total P&L: `${stats['total_pnl']:+.2f}`\n" \
              f"Trades: `{stats['total_trades']}`\n" \
              f"Win Rate: `{stats['win_rate']:.1f}%`\n\n" \
              f"Best Strategy: *{stats['best_strategy']}*\n" \
              f"P&L: `${stats['best_pnl']:+.2f}`"
        self.send_message(msg)
    
    def alert_profit_milestone(self, milestone, total_pnl):
        """Celebrate profit milestones."""
        msg = f"🎉 *PROFIT MILESTONE REACHED!*\n\n" \
              f"Total Realized P&L: `${total_pnl:,.2f}`\n" \
              f"Milestone: `${milestone:,.0f}` 🏆\n\n" \
              f"Keep up the great work!"
        self.send_message(msg)

