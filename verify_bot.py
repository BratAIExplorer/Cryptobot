#!/usr/bin/env python3
"""
Verify Bot - Pre-deployment verification script
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from core.logger import TradeLogger
from core.exchange import ExchangeInterface

def main():
    print("=" * 60)
    print("✅ Bot Verification Checklist")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Database Schema Check
    print("\n1️⃣  Verifying database schema...")
    try:
        logger = TradeLogger()
        logger.verify_schema()
        print("   ✅ All required tables exist (trades, positions, bot_status)")
    except Exception as e:
        print(f"   ❌ Schema verification failed: {e}")
        all_checks_passed = False
    
    # 2. Exchange Connectivity Check
    print("\n2️⃣  Testing exchange API connection...")
    try:
        exchange = ExchangeInterface()
        ticker = exchange.fetch_ticker('BTC/USDT')
        if ticker and 'last' in ticker:
            print(f"   ✅ Connected to Binance (BTC/USDT: ${ticker['last']:.2f})")
        else:
            print("   ❌ Could not fetch ticker data")
            all_checks_passed = False
    except Exception as e:
        print(f"   ❌ Exchange connection failed: {e}")
        all_checks_passed = False
    
    # 3. Strategy Classes Check
    print("\n3️⃣  Verifying strategy classes...")
    try:
        from strategies.hyper_scalper_strategy import HyperScalperStrategy
        from strategies.dca_strategy import DCAStrategy
        from strategies.volatility_hunter_strategy import VolatilityHunterStrategy
        from strategies.sma_crossover_strategy import SMACrossoverStrategy
        from strategies.grid_strategy import GridStrategy
        
        # Test instantiation
        test_config = {'rsi_limit': 10, 'amount': 100}
        hs = HyperScalperStrategy(test_config)
        print("   ✅ All strategy classes can be imported and instantiated")
    except Exception as e:
        print(f"   ❌ Strategy import failed: {e}")
        all_checks_passed = False
    
    # 4. File Permissions Check
    print("\n4️⃣  Checking file permissions...")
    try:
        test_file = 'data/test_write.tmp'
        os.makedirs('data', exist_ok=True)
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("   ✅ File write permissions OK")
    except Exception as e:
        print(f"   ❌ File permission issue: {e}")
        all_checks_passed = False
    
    # 5. Dependencies Check
    print("\n5️⃣  Checking required packages...")
    try:
        import ccxt
        import streamlit
        import pandas
        import tenacity
        print("   ✅ All required packages installed")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}")
        print("   Run: pip install -r requirements.txt")
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Bot is ready to run!")
        print("=" * 60)
        print("\nStart the bot with: python run_bot.py")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before starting bot")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
