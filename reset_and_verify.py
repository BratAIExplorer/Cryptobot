import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logger import TradeLogger
from core.exchange import ExchangeInterface

def reset_bot():
    print("="*60)
    print("🔄 BOT RECOVERY & RESET UTILITY")
    print("="*60)
    
    logger = TradeLogger()
    
    # 1. Check current status
    status = logger.get_circuit_breaker_status()
    print(f"\nCurrent Status: {'🔴 OPEN' if status['is_open'] else '🟢 CLOSED'}")
    print(f"Consecutive Errors: {status['consecutive_errors']}")
    
    # 2. Reset Circuit Breaker
    print("\n[1/3] Resetting Circuit Breaker in Database...")
    logger.reset_circuit_breaker()
    
    new_status = logger.get_circuit_breaker_status()
    if not new_status['is_open'] and new_status['consecutive_errors'] == 0:
        print("✅ Success: Circuit Breaker Reset.")
    else:
        print("❌ Error: Failed to reset database state.")
        return

    # 3. Verify Exchange Connectivity
    print("\n[2/3] Verifying Exchange Connectivity...")
    try:
        # We test a simple public fetch to ensure API is reachable
        exchange = ExchangeInterface(mode='paper')
        ticker = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=1)
        if not ticker.empty:
            price = ticker['close'].iloc[-1]
            print(f"✅ Success: Connected to exchange. Current BTC: ${price:,.2f}")
        else:
            print("❌ Error: Connected but received empty data.")
    except Exception as e:
        print(f"❌ Error: Connectivity test failed: {e}")
        print("🚨 DO NOT RESTART yet. Check internet/API keys.")
        return

    # 4. Final Health Check
    print("\n[3/3] System Ready for Restart.")
    print("\nNext Steps:")
    print("1. Terminate any 'ghost' or stuck bot processes.")
    print("2. Run: ./start_bot.sh")
    print("="*60)

if __name__ == "__main__":
    reset_bot()
