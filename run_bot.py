#!/usr/bin/env python3
"""
🤖 REFINED PARAMETERS - Post-Analysis Implementation
Version: 2025.12.25 (Christmas Edition - Clean Slate)

Key Changes:
- Grid Bots: Scaled from $2K to $6K (proven winners)
- SMA Trend: Added 20/50 crossover specs, trailing stop activation
- Buy-the-Dip: Smart conditional cooldown, multi-timeframe filters, 60-day max hold
- Momentum Swing: NEW strategy (converted from Hyper-Scalper)
- All bots: Circuit breakers added for safety
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine

def check_stop_signal():
    """Check for manual stop signal file"""
    if os.path.exists("STOP_SIGNAL"):
        print("\n🛑 STOP SIGNAL DETECTED. Shutting down...")
        try:
            os.remove("STOP_SIGNAL")
        except:
            pass
        return True
    return False

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
VERSION_ID = "2025.12.25"
TRADING_MODE = 'paper'
# ==========================================

def main():
    print("=" * 80, flush=True)
    print(f"🤖 Crypto Bot - Refined Parameters (v{VERSION_ID})", flush=True)
    print("=" * 80, flush=True)
    
    # Telegram config
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️  Telegram notifications disabled")
    
    # Initialize engine
    # V4: Multi-Exchange Support (Binance Only for now, Luno reserved for Intelligence)
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange=['BINANCE']
    )
    
    # ==========================================
    # 🏆 PRIORITY 1: GRID BOTS ($250 each)
    # ==========================================
    
    engine.add_bot({
        'name': 'Grid Bot BTC',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],
        # PROFITABILITY ANALYSIS:
        # Investment Budget: $250 (Small Start)
        # Price Range: $85,000 - $110,000 (Covers $25k price movement)
        # Grid Step: ~$1,250 price change per line (1.47% spread)
        # Net Profit: ~1.27% per successful trade.
        # Trade Size: $25 (allows ~10 active positions max with $250)
        'amount': 25,           # Trade size per grid line
        'grid_levels': 20,      # Total lines (not all active at once)
        'atr_multiplier': 2.0,
        'atr_period': 14,
        'lower_limit': 85000,
        'upper_limit': 110000,
        'initial_balance': 250, 
        'max_exposure_per_coin': 250
    })
    
    engine.add_bot({
        'name': 'Grid Bot ETH',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],
        # Budget: $250
        'amount': 25,           
        'grid_levels': 30,
        'atr_multiplier': 2.5,
        'atr_period': 14,
        'lower_limit': 2800,
        'upper_limit': 4200,
        'initial_balance': 250,  
        'max_exposure_per_coin': 250
    })
    
    # ==========================================
    # 💎 BUY-THE-DIP V3 (Top 10 Coins - $1000 Total)
    # ==========================================
    top_10 = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
        'ADA/USDT', 'DOGE/USDT', 'TRX/USDT', 'DOT/USDT', 'LINK/USDT'
    ]

    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': top_10,
        
        # Budget: $1000 Total ($100 per coin)
        'amount': 15,                 # $15 per buy
        'initial_balance': 1000,
        'max_exposure_per_coin': 100, # Cap at $100 per coin

        # Entry Conditions (V3)
        'dip_threshold': 0.03,       # 3% dip
        'rsi_limit': 35,             # V3 param
        'cooldown_minutes': 60,
        
        # Legacy/Hybrid Fallbacks
        'dip_percentage': 0.03,
        'min_confluence': 0,  # A/B TEST: Collect data on all trades to find optimal threshold
        
        # PROFIT RULES (User Request: 5-10% Profit, NO Losses)
        'take_profit_pct': 0.08,      # Target 8% Profit
        'stop_loss_pct': None,        # DISABLING STOP LOSS (Hold until profit)
        'stop_loss_enabled': False,   
        
        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })

    # Send startup notification
    if engine.notifier:
        active_bots_summary = []
        for b in engine.active_bots:
            syms = [s.split('/')[0] for s in b.get('symbols', [])[:5]]
            if len(b.get('symbols', [])) > 5:
                syms.append("...")
            
            # Retrieve PNL and wallet balance for each bot
            total_pnl = engine.logger.get_pnl_summary(b['name'])
            wallet_balance = engine.logger.get_wallet_balance(b['name'], initial_balance=b.get('initial_balance', 0.0))

            active_bots_summary.append({
                'name': b['name'],
                'symbols': syms,
                'total_count': len(b.get('symbols', [])),
                'total_pnl': total_pnl,
                'wallet_balance': wallet_balance
            })
        engine.notifier.notify_startup(TRADING_MODE, active_bots_summary)
    
    # Initialize and run
    try:
        engine.start()
    except Exception as e:
        print(f"⚠️ Engine startup warning: {e}")
    
    print("=" * 80)
    print(f"🚀 Bot Running - {TRADING_MODE.upper()} Mode")
    print("   Portfolio Allocation (VPS Config):")
    print("   - Grid Bots:      $500 ($250 BTC + $250 ETH)")
    print("   - Buy-the-Dip:    $1,000 (Top 10 Coins)")
    print("   - Total Capital:  $1,500")
    print("=" * 80)
    print("Press Ctrl+C to stop.")
    print()
    
    try:
        while True:
            if check_stop_signal():
                break
            
            try:
                engine.run_cycle()
            except Exception as e:
                print(f"❌ Error in run_cycle: {e}")
                import traceback
                traceback.print_exc()
                print("💤 Sleeping 300s before retry...")
                time.sleep(300)
                continue
            
            time.sleep(180)  # 3 minutes between cycles
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        engine.stop()
        print("✅ Bot stopped successfully")

if __name__ == "__main__":
    main()
