#!/usr/bin/env python3
"""
Test Capital Recycling Mechanism
Verifies that capital is properly released after sells
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.capital_controller import CapitalController
from core.logger import TradeLogger

def test_recycling():
    """Test complete buy-sell-rebuy cycle"""
    print("=" * 70)
    print("🔄 CAPITAL RECYCLING TEST")
    print("=" * 70)

    # Setup (use temporary test database)
    test_db = 'data/test_capital_recycling.db'
    if os.path.exists(test_db):
        os.remove(test_db)

    logger = TradeLogger(db_path=test_db)
    controller = CapitalController(logger)

    # Configure bot with $100 allocation
    BOT_NAME = 'Test_Grid_BTC'
    ALLOCATION = 100
    controller.set_bot_allocation(BOT_NAME, ALLOCATION)

    print(f"\n✅ Bot configured: {BOT_NAME} with ${ALLOCATION:,.2f} allocation\n")

    # Test Sequence
    tests_passed = 0
    tests_total = 7

    # TEST 1: Initial state
    print(f"TEST 1: Initial State")
    available = controller.get_available_capital(BOT_NAME)
    if available == ALLOCATION:
        print(f"   ✅ Available capital: ${available:,.2f}")
        tests_passed += 1
    else:
        print(f"   ❌ Expected ${ALLOCATION}, got ${available}")

    # TEST 2: First BUY allowed
    print(f"\nTEST 2: First BUY ($50)")
    allowed, reason = controller.check_trade_allowed(BOT_NAME, 50, 'BTC/USDT')
    if allowed:
        controller.record_trade(BOT_NAME, 50, 'BUY')
        available = controller.get_available_capital(BOT_NAME)
        if available == 50:
            print(f"   ✅ BUY executed, available now: ${available:,.2f}")
            tests_passed += 1
        else:
            print(f"   ❌ Expected $50 available, got ${available}")
    else:
        print(f"   ❌ Trade blocked: {reason}")

    # TEST 3: Second BUY allowed
    print(f"\nTEST 3: Second BUY ($50)")
    allowed, reason = controller.check_trade_allowed(BOT_NAME, 50, 'BTC/USDT')
    if allowed:
        controller.record_trade(BOT_NAME, 50, 'BUY')
        available = controller.get_available_capital(BOT_NAME)
        if available == 0:
            print(f"   ✅ Second BUY executed, available now: ${available:,.2f}")
            tests_passed += 1
        else:
            print(f"   ❌ Expected $0 available, got ${available}")
    else:
        print(f"   ❌ Trade blocked: {reason}")

    # TEST 4: Third BUY blocked (no capital)
    print(f"\nTEST 4: Third BUY ($50) - Should BLOCK")
    allowed, reason = controller.check_trade_allowed(BOT_NAME, 50, 'BTC/USDT')
    if not allowed:
        print(f"   ✅ Correctly blocked: {reason}")
        tests_passed += 1
    else:
        print(f"   ❌ Should have blocked (no capital available)")

    # TEST 5: SELL releases capital
    print(f"\nTEST 5: SELL first position ($50) - Release Capital")
    controller.record_trade(BOT_NAME, 50, 'SELL')
    available = controller.get_available_capital(BOT_NAME)
    if available == 50:
        print(f"   ✅ Capital released! Available: ${available:,.2f}")
        tests_passed += 1
    else:
        print(f"   ❌ Expected $50 available, got ${available}")

    # TEST 6: BUY again now possible (capital recycling works!)
    print(f"\nTEST 6: BUY again ($50) - Capital Recycling")
    allowed, reason = controller.check_trade_allowed(BOT_NAME, 50, 'BTC/USDT')
    if allowed:
        controller.record_trade(BOT_NAME, 50, 'BUY')
        available = controller.get_available_capital(BOT_NAME)
        if available == 0:
            print(f"   ✅ CAPITAL RECYCLING WORKS! Bought again successfully")
            tests_passed += 1
        else:
            print(f"   ❌ Expected $0 available after buy, got ${available}")
    else:
        print(f"   ❌ Trade blocked: {reason}")

    # TEST 7: Sell both positions, verify full capital recovered
    print(f"\nTEST 7: SELL both positions - Full Recovery")
    controller.record_trade(BOT_NAME, 50, 'SELL')
    controller.record_trade(BOT_NAME, 50, 'SELL')
    available = controller.get_available_capital(BOT_NAME)
    if available == ALLOCATION:
        print(f"   ✅ Full capital recovered: ${available:,.2f}")
        tests_passed += 1
    else:
        print(f"   ❌ Expected ${ALLOCATION}, got ${available}")

    # Summary
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {tests_passed}/{tests_total} passed")
    print("=" * 70)

    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED - Capital recycling works correctly!")
        print("\n📊 How it works:")
        print("   1. BUY locks capital (reduces available)")
        print("   2. SELL releases capital (increases available)")
        print("   3. Released capital immediately available for new trades")
        print("   4. Same allocation can generate unlimited trades via recycling")
        print("\n🚀 READY FOR LIVE TRADING!")
        return 0
    else:
        print(f"\n❌ {tests_total - tests_passed} TESTS FAILED - Fix before going live!")
        return 1

    # Cleanup
    try:
        os.remove(test_db)
    except:
        pass

if __name__ == "__main__":
    sys.exit(test_recycling())
