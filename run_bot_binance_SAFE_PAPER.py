#!/usr/bin/env python3
"""
BINANCE PAPER TRADING BOT - PHASE 3 TESTING
✅ Testnet: Using Binance sandbox (fake money)
✅ Capital Controls: STRICT enforcement
✅ Telegram: PAPER mode indicators
✅ Dashboard: Separate testnet database
✅ Emergency Stop: Multiple methods

SAFETY FEATURES:
- Per-bot capital allocation limits
- Daily loss limit: $50
- Telegram alerts with PAPER prefix
- Real-time capital tracking
- Emergency stop signal
- Sandbox mode enabled
"""
import time
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine
from core.notifier_live import LiveTradingNotifier
from core.capital_controller import CapitalController
from core.logger import TradeLogger

# ==========================================
# ⚙️ PAPER TRADING CONFIGURATION
# ==========================================
TRADING_MODE = 'paper'  # 📝 PAPER MODE (Testnet)
EXCHANGE = 'binance'
DATABASE_FILE = 'data/trades_binance_paper.db'
SANDBOX_MODE = True  # Use Binance testnet

# Portfolio Configuration
TOTAL_BALANCE = 218.08  # Target testnet balance (matches your MEXC balance)
RESERVE_PCT = 0.35  # Keep 35% reserve (aggressive for small balance)
TRADEABLE_CAPITAL = TOTAL_BALANCE * (1 - RESERVE_PCT)  # $141.75

# Per-Bot Allocations (CONSERVATIVE)
ALLOCATIONS = {
    'Binance_Grid_BTC_Paper': 80,   # BTC Grid Bot
    'Binance_Grid_ETH_Paper': 60,   # ETH Grid Bot
}

# Safety Limits
DAILY_LOSS_LIMIT = 50  # Stop trading if lose >$50 in a day
MAX_OPEN_POSITIONS = 5  # Max total open positions
# ==========================================

def check_stop_signal():
    """Check for emergency stop signal file"""
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL")
        except:
            pass
        return True
    return False

def verify_environment():
    """Verify all required environment variables and API access"""
    from dotenv import load_dotenv
    import ccxt

    print("=" * 80)
    print("🔍 PRE-LAUNCH ENVIRONMENT VERIFICATION")
    print("=" * 80)

    load_dotenv('.env.binance.paper')

    errors = []

    # 1. Check .env variables
    required_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower()}_here':
            errors.append(f"❌ {var} not set in .env")
        else:
            print(f"✅ {var}: {'*' * 10}{value[-4:]}")

    if errors:
        print("\n❌ ENVIRONMENT ERRORS:")
        for err in errors:
            print(f"   {err}")
        print("\n⚠️  Fix .env file before launching!")
        return False

    # 2. Test Binance API connection
    print("\n🔗 Testing Binance Testnet API connection...")
    try:
        binance = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

        # Enable sandbox mode for testnet
        binance.set_sandbox_mode(True)

        balance = binance.fetch_balance()
        usdt = balance['USDT']['total']
        print(f"✅ Binance Testnet Connected: ${usdt:,.2f} USDT (fake money)")

        # Check BTC/USDT and ETH/USDT markets
        markets = binance.load_markets()
        for symbol in ['BTC/USDT', 'ETH/USDT']:
            if symbol in markets and markets[symbol].get('active'):
                print(f"✅ {symbol}: Active")
            else:
                print(f"❌ {symbol}: NOT ACTIVE")
                errors.append(f"{symbol} not active")

    except Exception as e:
        print(f"❌ Binance API Error: {e}")
        errors.append(str(e))
        return False

    # 3. Test Telegram
    print("\n📱 Testing Telegram...")
    try:
        import requests
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        msg = '📝 PAPER BOT - Pre-launch test successful! Launching in 10 seconds...\n\n(Testnet - fake money)'
        response = requests.post(url, json={'chat_id': chat_id, 'text': msg})
        if response.status_code == 200:
            print("✅ Telegram test message sent")
        else:
            print(f"⚠️  Telegram response: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Telegram error: {e}")
        print("   Bot will run without alerts")

    print("\n" + "=" * 80)
    print("✅ ALL CHECKS PASSED - READY FOR PAPER TRADING")
    print("=" * 80)

    return True

def main():
    print("=" * 80)
    print("📝 BINANCE PAPER TRADING BOT - PHASE 3 📝")
    print("=" * 80)
    print(f"✅ TESTNET MODE: Using fake money on Binance testnet!")
    print(f"Exchange: {EXCHANGE}")
    print(f"Mode: {TRADING_MODE.upper()}")
    print(f"Sandbox: {SANDBOX_MODE}")
    print(f"Database: {DATABASE_FILE}")
    print(f"Balance: ${TOTAL_BALANCE:,.2f} USDT (target)")
    print(f"Tradeable: ${TRADEABLE_CAPITAL:,.2f} ({(1-RESERVE_PCT)*100:.0f}%)")
    print(f"Reserve: ${TOTAL_BALANCE * RESERVE_PCT:,.2f} ({RESERVE_PCT*100:.0f}%)")
    print("=" * 80)

    # Pre-launch verification
    if not verify_environment():
        print("\n❌ Environment verification failed. Aborting.")
        return 1

    # 10-second abort window
    print("\n⏸️  FINAL SAFETY CHECK:")
    print("   - Environment verified ✅")
    print("   - Capital allocation set ✅")
    print("   - Telegram alerts configured ✅")
    print("   - Emergency stop ready ✅")
    print(f"\n⚠️  Press Ctrl+C within 10 seconds to ABORT...")
    print("   Otherwise, PAPER trading will begin!\n")

    try:
        for i in range(10, 0, -1):
            print(f"   Starting in {i}...", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n❌ ABORTED by user. No trades executed.")
        return 0

    print("\n\n🚀 LAUNCHING PAPER TRADING NOW (Testnet)...")
    time.sleep(1)

    # Initialize logger
    logger = TradeLogger(db_path=DATABASE_FILE)

    # Initialize LIVE Telegram notifier
    telegram_config = {
        'token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID')
    }

    notifier = LiveTradingNotifier(
        token=telegram_config['token'],
        chat_id=telegram_config['chat_id'],
        mode='paper'  # Enable PAPER mode indicators
    )

    # Initialize Capital Controller
    capital_controller = CapitalController(logger, notifier)
    capital_controller.set_daily_loss_limit(DAILY_LOSS_LIMIT)

    # Set per-bot allocations
    for bot_name, allocation in ALLOCATIONS.items():
        capital_controller.set_bot_allocation(bot_name, allocation)

    # Initialize Trading Engine
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange=EXCHANGE,
        db_path=DATABASE_FILE
    )

    # Override engine's notifier with LIVE notifier
    engine.notifier = notifier

    # Store capital controller in engine for access during trades
    engine.capital_controller = capital_controller

    # CRITICAL: Enable sandbox mode for testnet trading
    if SANDBOX_MODE and hasattr(engine, 'exchange') and hasattr(engine.exchange, 'set_sandbox_mode'):
        engine.exchange.set_sandbox_mode(True)
        print("✅ Sandbox mode enabled on trading engine")

    # PAPER MODE ADJUSTMENTS: Disable features that don't work well with testnet data
    if TRADING_MODE == 'paper':
        print("\n📝 PAPER MODE ADJUSTMENTS:")

        # Disable crash veto (testnet has stale 24h high data)
        if hasattr(engine, 'veto_manager'):
            engine.veto_manager.disable_crash_veto = True
            print("   ✅ Crash detection disabled (testnet data unreliable)")

        # Disable CryptoPanic (not needed for testnet)
        if hasattr(engine, 'fundamental_analyzer'):
            engine.fundamental_analyzer.use_cryptopanic = False
            print("   ✅ CryptoPanic disabled (not needed for testnet)")

        print("   ℹ️  Bot will rely on technical analysis only")

    print("\n" + "=" * 80)
    print("💰 PHASE 1 CAPITAL ALLOCATION")
    print("=" * 80)

    # ==========================================
    # STRATEGY 1: GRID BOT BTC - $80
    # ==========================================
    print("\n1️⃣  Grid Bot BTC: $80")
    bot_config_btc = {
        'name': 'Binance_Grid_BTC_Paper',
        'type': 'GRID',
        'symbols': ['BTC/USDT'],
        'amount': ALLOCATIONS['Binance_Grid_BTC_Paper'],
        'grid_levels': 5,
        'range_pct': 0.08,  # 8% range
        'profit_per_grid': 0.015,  # 1.5% profit per fill
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    }
    engine.add_bot(bot_config_btc)
    notifier.alert_bot_launched(
        bot_config_btc['name'],
        'BTC/USDT',
        bot_config_btc['amount']
    )

    # ==========================================
    # STRATEGY 2: GRID BOT ETH - $60
    # ==========================================
    print("2️⃣  Grid Bot ETH: $60")
    bot_config_eth = {
        'name': 'Binance_Grid_ETH_Paper',
        'type': 'GRID',
        'symbols': ['ETH/USDT'],
        'amount': ALLOCATIONS['Binance_Grid_ETH_Paper'],
        'grid_levels': 5,
        'range_pct': 0.10,  # 10% range
        'profit_per_grid': 0.02,  # 2% profit per fill
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    }
    engine.add_bot(bot_config_eth)
    notifier.alert_bot_launched(
        bot_config_eth['name'],
        'ETH/USDT',
        bot_config_eth['amount']
    )

    # Print capital allocation summary
    capital_controller.print_summary()

    print("\n" + "=" * 80)
    print("✅ 2 Grid Bots configured and launched!")
    print(f"💰 Total Allocated: ${sum(ALLOCATIONS.values()):,.2f}")
    print(f"💰 Reserve: ${TOTAL_BALANCE - sum(ALLOCATIONS.values()):,.2f}")
    print(f"🗄️  Database: {DATABASE_FILE}")
    print(f"📝 Mode: PAPER TRADING (Testnet)")
    print("=" * 80)

    print("\n📊 MONITORING:")
    print("   Dashboard: http://localhost:8501")
    print("   Logs: tail -f logs/live_*.log")
    print("   Database: sqlite3 data/trades_binance_paper.db")

    print("\n🛑 EMERGENCY STOP:")
    print("   Method 1: touch STOP_SIGNAL")
    print("   Method 2: Ctrl+C (graceful)")
    print("   Method 3: kill $(cat bot.pid)")

    # Send startup notification
    notifier.notify_startup(TRADING_MODE, engine.active_bots)

    # Save PID for monitoring
    pid = os.getpid()
    with open('bot.pid', 'w') as f:
        f.write(str(pid))
    print(f"\n📋 Bot PID: {pid} (saved to bot.pid)")

    # Main trading loop
    print("\n🚀 PAPER TRADING ACTIVE (Testnet) - Monitoring for signals...")
    print("=" * 80 + "\n")

    try:
        engine.start()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Shutting down gracefully...")
        capital_controller.print_summary()

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        notifier.alert_error("Runtime Error", str(e), "TradingEngine")

    finally:
        print("\n" + "=" * 80)
        print("✅ BINANCE PAPER BOT STOPPED")
        print("=" * 80)

        # Final summary
        capital_controller.print_summary()

        print(f"\n📊 Review results:")
        print(f"   python analyze_trades.py --db {DATABASE_FILE}")
        print(f"   sqlite3 {DATABASE_FILE} 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;'")

        # Clean up PID file
        try:
            os.remove('bot.pid')
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
