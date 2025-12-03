import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.notifier import TelegramNotifier

def test_telegram():
    print("="*60)
    print("🔔 TELEGRAM DRY RUN TEST")
    print("="*60)
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("❌ MISSING CONFIGURATION")
        print("Please set your environment variables:")
        print("export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("export TELEGRAM_CHAT_ID='your_chat_id_here'")
        return

    print(f"🔑 Token: {token[:5]}...{token[-5:]}")
    print(f"🆔 Chat ID: {chat_id}")
    print("\nAttempting to send test message...")

    notifier = TelegramNotifier(token, chat_id)
    success = notifier.send_message("🔔 *Dry Run Test*\n\nIf you see this, your Telegram alerts are working! 🚀")

    if success:
        print("✅ SUCCESS! Message sent.")
    else:
        print("❌ FAILED. Please check your Token and Chat ID.")

if __name__ == "__main__":
    test_telegram()
