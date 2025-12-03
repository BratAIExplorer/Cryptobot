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
