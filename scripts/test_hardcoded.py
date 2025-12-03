from core.notifier import TelegramNotifier

# REPLACE THESE WITH YOUR ACTUAL VALUES BEFORE RUNNING
TOKEN = "YOUR_FULL_TOKEN_HERE"  # e.g. 123456:ABC-DEF...
CHAT_ID = "794546792"

print(f"Testing with Token: {TOKEN[:5]}... and Chat ID: {CHAT_ID}")
notifier = TelegramNotifier(TOKEN, CHAT_ID)
success = notifier.send_message("🔔 If you see this, the code works (Env Vars were the problem)!")

if success:
    print("✅ SUCCESS!")
else:
    print("❌ FAILED. The Token or Chat ID is definitely wrong.")
