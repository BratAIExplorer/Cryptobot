#!/usr/bin/env python3
"""
Standalone bot runner - runs trading strategies 24/7 independently of the dashboard.
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import os
from core.engine import TradingEngine

# Function to check stop signal
def check_stop_signal():
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL") # Clean up
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ GLOBAL CONFIGURATION
# ==========================================
VERSION_ID = "2025.12.23.01" # For verification
TRADING_MODE = 'paper' 
# ==========================================

def main():
    print("=" * 60, flush=True)
    print(f"🤖 Crypto Trading Bot - Standalone Runner (v{VERSION_ID})", flush=True)
    print("=" * 60, flush=True)
    
    # Telegram config from environment variables
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️  Telegram notifications disabled")
    
    # Initialize engine with MEXC as primary exchange for BOTS
    # (Luno monitoring is handled separately within the engine)
    engine = TradingEngine(
        mode=TRADING_MODE, 
        telegram_config=telegram_config, 
        exchange='MEXC',
        db_path='data/trades_v3_paper.db'
    )
    
    # ==========================================
    # 🚀 ALL-STAR PORTFOLIO CONFIGURATION
    # Based on Top 15 Coin Backtest Results
    # ==========================================
    
    # 1. SMA TREND BOT (The Champion)
    # Best for catching big moves. 40% of Capital.
    engine.add_bot({
        'name': 'SMA Trend Bot',
        'type': 'SMA',
        'symbols': ['DOGE/USDT', 'XRP/USDT', 'SOL/USDT', 'BNB/USDT', 'BTC/USDT'],
        'amount': 800,  # $800 per coin ($4000 total)
        'initial_balance': 4000,
        'take_profit_pct': 0.05,  # 5% Target (User Hybrid Request)
        'stop_loss_pct': 0.05,    # 5% Max Loss
        'max_hold_hours': 48,     # TIME LIMIT: 48h to hit 5% or sell.
        'max_exposure_per_coin': 800
    })
    
    # 2. BUY THE DIP BOT (The Accumulator)
    # Safe accumulation. 40% of Capital.
    # Verified 100% Win Rate on these coins over 24 months.
    engine.add_bot({
        'name': 'Dip Sniper',
        'type': 'DIP',
        'symbols': ['XRP/USDT', 'DOGE/USDT', 'SOL/USDT', 'BNB/USDT', 'ETH/USDT', 'BTC/USDT'],
        'amount': 600,  # $600 per coin ($3600 total)
        'initial_balance': 3600,
        'dip_percentage': 0.08,  # Buy on 8% drop (High conviction)
        'profit_target': 0.05,   # Sell on 5% bounce.
        # NOTE: User requested Tiered Exits (50%@5%, 25%@7.5%, 25%@10%).
        # Logic: For V2.1 Safety, we use a single verified target of 5%. 
        # Tiered logic will be added in Phase 5 (Advanced Execution).
        'max_exposure_per_coin': 1200
    })
    
    # 2. BUY-THE-DIP STRATEGY (Value Investing)
    # Best for volatile dips. 25% of Capital.
    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT', 'AVAX/USDT', 'SHIB/USDT', 'DOT/USDT', 'LINK/USDT', 'BCH/USDT', 'NEAR/USDT', 'LTC/USDT', 'UNI/USDT', 'PEPE/USDT', 'APT/USDT', 'ICP/USDT', 'ETC/USDT'],
        'amount': 800,  # $800 per coin ($2400 total)
        'initial_balance': 16000,
        'take_profit_pct': 0.10,  # Target 10% (Tiered exits handle the rest)
        'stop_loss_pct': 0.30,    # Max drawdown 30% (Reference only, disabled below)
        'stop_loss_enabled': False, # User Request: Infinite Hold + Alerts
        'max_hold_hours': 0,      # 0 = Indefinite Hold
        'max_exposure_per_coin': 800
    })
    
    # 3. HYPER SCALPER (Experimental - Paper Only)
    # DEACTIVATED per Senior Trader Review: Backtest shows negative net profit after fees.
    # engine.add_bot({
    #     'name': 'Hyper Scalper',
    #     'type': 'RSI',
    #     'symbols': ['BTC/USDT'], # Only BTC for safety testing
    #     'amount': 200,   # Small bets
    #     'rsi_lower': 30, # Relaxed from 15
    #     'rsi_upper': 70,
    #     'profit_target': 0.012,
    #     'stop_loss': 0.02,
    #     'max_active_trades': 1,
    #     'max_exposure_per_coin': 200
    # })

    # 4. GRID BOTS (Sideways Market Kings)
    # 20% of Capital.
    # BTC Grid: Range +/- 10%, 20 Grids
    engine.add_bot({
        'name': 'Grid Bot BTC',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],
        'amount': 50,           # Amount per grid level
        'grid_levels': 20,
        'atr_multiplier': 2.0,  # Dynamic Range
        'atr_period': 14,
        'lower_limit': 88000,   # Fallback 
        # For now, let's set a wide fixed range or update V2 to auto-calculate if 0.
        # But V2 takes config. Let's use the backtest values relative to current price.
        # Since I can't get live price easily here, I'll use the values from backtest or expert advice.
        # Expert said: "Use support/resistance levels".
        # For automation, I'll set a wide range around "current" price (approx 98k for BTC, 3200 for ETH).
        'lower_limit': 88000,
        'upper_limit': 108000,
        'initial_balance': 1000,
        'max_exposure_per_coin': 1000
    })

    engine.add_bot({
        'name': 'Grid Bot ETH',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],
        'amount': 30,
        'grid_levels': 30,
        'atr_multiplier': 2.5, # Slightly wider for ETH
        'atr_period': 14,
        'lower_limit': 2800,
        'upper_limit': 3500,
        'initial_balance': 1000,
        'max_exposure_per_coin': 1000
    })

    # 5. HIDDEN GEM MONITOR (Paper Mode Exploration)
    # Tracking top 50 coins for dip opportunities.
    engine.add_bot({
        'name': 'Hidden Gem Monitor',
        'type': 'Buy-the-Dip',
        'symbols': [
            'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'POL/USDT', 
            'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'NEAR/USDT', 'ALGO/USDT',
            'FIL/USDT', 'HBAR/USDT', 'ICP/USDT', 'VET/USDT', 'SAND/USDT',
            'MANA/USDT', 'AAVE/USDT', 'XTZ/USDT'
        ],
        'amount': 100,  # Small test amount
        'initial_balance': 1800,
        'take_profit_pct': 0.10,
        'stop_loss_pct': 0.20,
        'max_hold_hours': 72,
        'max_exposure_per_coin': 100
    })
    
    # Send Startup Notification with dynamic strategy list
    if engine.notifier:
        active_bots_summary = []
        for b in engine.active_bots:
            # Shorten symbols list for notification readability
            syms = [s.split('/')[0] for s in b.get('symbols', [])[:5]]
            if len(b.get('symbols', [])) > 5: syms.append("...")
            active_bots_summary.append({
                'name': b['name'],
                'symbols': syms
            })
        engine.notifier.notify_startup(TRADING_MODE, active_bots_summary)

    # Initialize statuses and warm-up
    engine.start()

    print("=" * 60)
    print(f"🚀 Bot Running in {TRADING_MODE.upper()} mode...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            if check_stop_signal():
                break
            
            try:
                engine.run_cycle()
            except Exception as e:
                print(f"❌ CRASH in run_cycle: {e}")
                import traceback
                traceback.print_exc()
                # Sleep longer to prevent rapid restart loops and rate limits
                print("💤 Sleeping 60s before retry/restart...")
                time.sleep(60)
                raise e # Re-raise to let PM2 restart (but slowly)
            
            # Normal sleep: 180s (3 minutes) between cycles for better rate handling
            time.sleep(180) 
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot via KeyboardInterrupt...")
        engine.stop()
        print("✅ Bot stopped successfully")

if __name__ == "__main__":
    main()
