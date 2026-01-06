"""
Enhanced Telegram Notifier with LIVE Trading Mode Indicators
Wraps existing TelegramNotifier to add visual distinction for live trading
"""
import os
from .notifier import TelegramNotifier

class LiveTradingNotifier(TelegramNotifier):
    """
    Enhanced notifier that adds visual indicators for LIVE trading mode
    Prevents confusion between paper and live trading alerts
    """

    def __init__(self, token=None, chat_id=None, mode='paper'):
        super().__init__(token, chat_id)
        self.mode = mode.lower()
        self.is_live = self.mode == 'live'

    def _get_mode_prefix(self):
        """Get visual prefix based on trading mode"""
        if self.is_live:
            return "🔴 **LIVE TRADING** 🔴\n"
        else:
            return "📝 PAPER\n"

    def _wrap_message(self, message):
        """Wrap message with mode indicator"""
        if self.is_live:
            # Add prominent LIVE indicator
            return f"🔴 **LIVE** 🔴\n{message}\n\n⚠️ _Real money trade_"
        return message

    def send_message(self, message):
        """Override to add mode prefix"""
        wrapped = self._wrap_message(message)
        return super().send_message(wrapped)

    def notify_trade(self, symbol, side, price, amount, reason=""):
        """Enhanced trade notification with LIVE indicator"""
        mode_prefix = self._get_mode_prefix()
        icon = "🟢" if side == "BUY" else "🔴"

        msg = f"{mode_prefix}"
        msg += f"{icon} *{side} {symbol}*\n"
        msg += f"Price: `${price:.4f}`\n"
        msg += f"Amount: `{amount:.4f}`\n"
        msg += f"Value: `${price * amount:.2f}`\n"
        msg += f"Reason: _{reason}_"

        if self.is_live:
            msg += f"\n\n💰 **REAL MONEY EXECUTED**"

        # Don't call parent's notify_trade, use send_message directly
        TelegramNotifier.send_message(self, msg)

    def notify_startup(self, mode, active_bots):
        """Enhanced startup notification with balance info"""
        if not self.can_send_throttled_msg("bot_startup_alert", hours=4):
            print("🕒 [NOTIFIER] Startup notification throttled.")
            return

        mode_prefix = self._get_mode_prefix()
        bots_list = "\n".join([
            f"- {b['name']}: ${b.get('amount', 0):,.0f}"
            for b in active_bots
        ])

        total_allocation = sum([b.get('amount', 0) for b in active_bots])

        msg = f"{mode_prefix}"
        msg += f"🚀 *Bot Started* 🚀\n\n"
        msg += f"Mode: *{mode.upper()}*\n"
        msg += f"Total Allocation: `${total_allocation:,.2f}`\n\n"
        msg += f"Active Strategies:\n{bots_list}\n\n"

        if self.is_live:
            msg += f"⚠️ **LIVE MODE - Real Money Trading Active**\n"
            msg += f"🛑 Emergency Stop: touch STOP_SIGNAL\n"

        msg += f"✅ Systems Check: OK"

        TelegramNotifier.send_message(self, msg)

    def alert_bot_launched(self, bot_name, symbol, allocation):
        """Alert when individual bot launches"""
        mode_prefix = self._get_mode_prefix()

        msg = f"{mode_prefix}"
        msg += f"🤖 *Bot Activated*\n\n"
        msg += f"Name: {bot_name}\n"
        msg += f"Symbol: {symbol}\n"
        msg += f"Allocation: `${allocation:,.2f}`\n"

        if self.is_live:
            msg += f"\n⚠️ Trading with real funds"

        self.send_message(msg)

    def alert_capital_limit_reached(self, bot_name, attempted_amount, limit, reason):
        """Alert when bot tries to exceed capital allocation"""
        msg = f"🛑 *CAPITAL LIMIT BREACH PREVENTED*\n\n"
        msg += f"Bot: {bot_name}\n"
        msg += f"Attempted: `${attempted_amount:,.2f}`\n"
        msg += f"Limit: `${limit:,.2f}`\n"
        msg += f"Reason: {reason}\n\n"
        msg += f"✅ Trade blocked for safety"

        self.send_message(msg)

    def alert_daily_loss_limit(self, current_loss, limit):
        """Alert approaching or hitting daily loss limit"""
        msg = f"⚠️ *DAILY LOSS ALERT*\n\n"
        msg += f"Current Loss: `${current_loss:,.2f}`\n"
        msg += f"Daily Limit: `${limit:,.2f}`\n"
        msg += f"Remaining: `${limit - abs(current_loss):,.2f}`\n\n"

        if abs(current_loss) >= limit:
            msg += f"🛑 **LIMIT REACHED - TRADING PAUSED**"
        else:
            msg += f"⚠️ Approaching limit - trade carefully"

        self.send_message(msg)

    def send_daily_summary(self, stats):
        """Enhanced daily summary with LIVE indicator"""
        mode_prefix = self._get_mode_prefix()

        msg = f"{mode_prefix}"
        msg += f"📊 *DAILY SUMMARY*\n\n"
        msg += f"Date: `{stats['date']}`\n"
        msg += f"Total P&L: `${stats['total_pnl']:+.2f}`\n"
        msg += f"Trades: `{stats['total_trades']}`\n"
        msg += f"Win Rate: `{stats['win_rate']:.1f}%`\n\n"

        if 'best_strategy' in stats:
            msg += f"Best Strategy: *{stats['best_strategy']}*\n"
            msg += f"P&L: `${stats['best_pnl']:+.2f}`\n\n"

        if self.is_live:
            msg += f"💰 Real profit/loss reflected in MEXC balance"

        super(TelegramNotifier, self).send_message(msg)
