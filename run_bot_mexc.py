#!/usr/bin/env python3
"""
MEXC Bot Runner - Paper Trading Mode
All 6 strategies with $3,600 total budget

CRITICAL DATABASE SEPARATION:
- Database: data/trades_mexc_paper.db (NOT trades.db!)
- All trades tagged: exchange='MEXC', mode='paper'
- Bot names: MEXC_Grid_BTC, MEXC_Buy_Dip, etc.
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom components
from core.engine import TradingEngine

# Stop signal check
def check_stop_signal():
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL")
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ MEXC CONFIGURATION
# ==========================================
TRADING_MODE = 'paper'  # Paper trading mode
EXCHANGE = 'MEXC'        # Use MEXC exchange
DATABASE_FILE = 'data/trades_mexc_paper.db'  # Separate database!
# ==========================================

def main():
    print("=" * 80)
    print("🚀 MEXC Crypto Bot - Paper Trading Mode")
    print("=" * 80)
    print(f"Exchange: {EXCHANGE}")
    print(f"Mode: {TRADING_MODE}")
    print(f"Database: {DATABASE_FILE}")
    print("=" * 80)
    
    # Telegram config
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️  Telegram notifications disabled")
    
    # Initialize engine with MEXC
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange=EXCHANGE,  # Use MEXC
        db_path=DATABASE_FILE  # Separate database (VPS uses db_path)
    )
    
    print("\n" + "=" * 80)
    print("💰 CAPITAL ALLOCATION: $20,500 Total ($500/coin)")
    print("=" * 80)
    
    # ==========================================
    # STRATEGY 1: BUY-THE-DIP - $10,000
    # ==========================================
    print("\n1️⃣  Buy-the-Dip Strategy: $10,000 ($500/coin x 20)")
    engine.add_bot({
        'name': 'MEXC_Buy_Dip',  # MEXC-specific name
        'type': 'DIP',
        'symbols': [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT',
            'BNB/USDT', 'ADA/USDT', 'DOGE/USDT', 'SUI/USDT', 'LINK/USDT',
            'TRX/USDT', 'AVAX/USDT', 'DOT/USDT', 'LTC/USDT', 'BCH/USDT',
            'UNI/USDT', 'APT/USDT', 'ATOM/USDT', 'NEAR/USDT', 'ICP/USDT'
        ],
        'amount': 500,  # $500 per coin
        'dip_percentage': 0.08,  # Buy on 8% drop
        'profit_target': 0.05,   # 5% profit target
        'max_positions': 20,
        'exchange': EXCHANGE,  # Tag with MEXC
        'mode': TRADING_MODE,  # Tag with paper
    })
    
    # ==========================================
    # STRATEGY 2: GRID BOT BTC - $500
    # ==========================================
    print("2️⃣  Grid Bot BTC: $500")
    engine.add_bot({
        'name': 'MEXC_Grid_BTC',  # MEXC-specific name
        'type': 'GRID',
        'symbols': ['BTC/USDT'],
        'amount': 500,
        'grid_levels': 5,
        'range_pct': 0.10,  # 10% range
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })
    
    # ==========================================
    # STRATEGY 3: GRID BOT ETH - $500
    # ==========================================
    print("3️⃣  Grid Bot ETH: $500")
    engine.add_bot({
        'name': 'MEXC_Grid_ETH',
        'type': 'GRID',
        'symbols': ['ETH/USDT'],
        'amount': 500,
        'grid_levels': 5,
        'range_pct': 0.10,
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })
    
    # ==========================================
    # STRATEGY 4: HYPER-SCALPER - $2,000
    # ==========================================
    print("4️⃣  Hyper-Scalper: $2,000 ($500/coin x 4)")
    engine.add_bot({
        'name': 'MEXC_Hyper_Scalper',
        'type': 'SCALPER',
        'symbols': ['SOL/USDT', 'AVAX/USDT', 'DOGE/USDT', 'XRP/USDT'],
        'amount': 500,  # $500 per coin
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'profit_target': 0.01,  # 1% profit
        'stop_loss': 0.005,     # 0.5% stop
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })
    
    # ==========================================
    # STRATEGY 5: SMA TREND - $2,500
    # ==========================================
    print("5️⃣  SMA Trend Bot: $2,500 ($500/coin x 5)")
    engine.add_bot({
        'name': 'MEXC_SMA_Trend',
        'type': 'SMA',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'SUI/USDT', 'ATOM/USDT'],
        'amount': 500,  # $500 per coin
        'fast_sma': 20,
        'slow_sma': 50,
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.05,
        'max_hold_hours': 48,
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })
    
    # ==========================================
    # STRATEGY 6: HIDDEN GEM - $5,000
    # ==========================================
    print("6️⃣  Hidden Gem Monitor: $5,000 ($500/coin x 10)")
    engine.add_bot({
        'name': 'MEXC_Hidden_Gem',
        'type': 'HIDDEN_GEM',
        'symbols': [
            'MANA/USDT', 'XTZ/USDT', 'AAVE/USDT', 'HYPE/USDT', 'SAND/USDT',
            'CRV/USDT', 'LDO/USDT', 'OP/USDT', 'ARB/USDT', 'IMX/USDT'
        ],
        'amount': 500,  # $500 per coin
        'volume_spike_threshold': 3.0,  # 3x volume
        'price_spike_threshold': 0.05,  # 5% price
        'profit_target': 0.10,  # 10% profit
        'exchange': EXCHANGE,
        'mode': TRADING_MODE,
    })
    
    print("\n" + "=" * 80)
    print("✅ All 6 strategies configured!")
    print("💰 Total Budget: $20,500 ($500/coin)")
    print("🗄️  Database: data/trades_mexc_paper.db")
    print("🏷️  All trades tagged: exchange='MEXC', mode='paper'")
    print("=" * 80)
    
    # Run the engine (use start() not run_cycle())
    print("\n🚀 Starting MEXC bots...")
    try:
        engine.start()  # Fixed: use start() method
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Shutting down gracefully...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ MEXC bot stopped.")
        print(f"📊 Review results: python analyze_trades.py --db {DATABASE_FILE}")

if __name__ == "__main__":
    main()
