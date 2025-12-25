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
    engine = TradingEngine(
        mode=TRADING_MODE,
        telegram_config=telegram_config,
        exchange='MEXC',
        db_path='data/trades_v3_paper.db'
    )
    
    # ==========================================
    # 🏆 PRIORITY 1: GRID BOTS (SCALE UP!)
    # Proven winners: +$4,800 in 2 weeks with $2K
    # Scaling to $6K total for ~$14K/month potential
    # ==========================================
    
    engine.add_bot({
        'name': 'Grid Bot BTC',
        'type': 'Grid',
        'symbols': ['BTC/USDT'],
        'amount': 150,          # Increased from $50
        'grid_levels': 20,
        'atr_multiplier': 2.0,
        'atr_period': 14,
        'lower_limit': 88000,
        'upper_limit': 108000,
        'initial_balance': 3000,  # Scaled from $1K to $3K
        'max_exposure_per_coin': 3000
    })
    
    engine.add_bot({
        'name': 'Grid Bot ETH',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],
        'amount': 100,          # Increased from $30
        'grid_levels': 30,
        'atr_multiplier': 2.5,
        'atr_period': 14,
        'lower_limit': 2800,
        'upper_limit': 3600,
        'initial_balance': 3000,  # Scaled from $1K to $3K
        'max_exposure_per_coin': 3000
    })
    
    # ==========================================
    # 🎯 PRIORITY 2: SMA TREND BOT (OPTIMIZE)
    # Already profitable, now with proper specs
    # ==========================================
    
    engine.add_bot({
        'name': 'SMA Trend Bot',
        'type': 'SMA',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT'],
        
        # Position Management (Conservative $300 max instead of $400)
        'amount': 300,
        'initial_balance': 4000,
        'max_exposure_per_coin': 900,  # Max 3 positions
        
        # SMA Parameters (NOW SPECIFIED!)
        'sma_fast': 20,
        'sma_slow': 50,
        'entry_signal': 'crossover',  # 20 crosses above 50
        
        # Exit Rules
        'take_profit_pct': 0.10,      # 10% target
        'stop_loss_pct': 0.03,        # -3% hard stop
        'trailing_stop': True,
        'trailing_stop_pct': 0.04,    # 4% trail
        'trailing_activates_at': 0.06, # Start trailing after +6% gain
        
        # Safety
        'max_hold_hours': 504,        # 21 days max
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })
    
    # ==========================================
    # 🔄 PRIORITY 3: BUY-THE-DIP (CLEAN SLATE TEST)
    # Refined with smart cooldown, trend filters, circuit breakers
    # ==========================================
    
    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
            'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT',
            'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
        ],
        
        # Position Sizing (Start small, scale gradually)
        'amount': 25,  # START AT $25, scale to $200 if profitable
        'initial_balance': 3000,  # Reduced from $16K
        'max_exposure_per_coin': 200,
        
        # Entry/Exit
        'dip_percentage': 0.05,       # 5% dip threshold
        'take_profit_pct': 0.06,      # 6% target (net 5.6% after fees)
        'stop_loss_pct': 0.04,        # -4% hard stop
        'stop_loss_enabled': True,     # ENABLED (was disabled before!)
        
        # Trend Filters (MULTI-TIMEFRAME)
        'sma_fast': 7,                # 7-day SMA (crypto-speed)
        'sma_slow': 21,               # 21-day SMA (traditional)
        'require_above_both': True,    # Must be above BOTH SMAs
        
        # Smart Conditional Cooldown
        'cooldown_after_profit': 6,   # 6 hours if trade was profitable
        'cooldown_after_loss': 48,    # 48 hours if stopped out
        'cooldown_same_day': 12,      # 12h minimum between buys
        'max_positions_per_coin': 2,  # Can scale in once
        
        # Safety Limits
        'max_daily_trades': 3,
        'max_hold_hours': 1440,       # 60 days (will backtest to optimize)
        'min_confluence': 65,
        
        # Circuit Breaker
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })
    
    # ==========================================
    # 🚀 PRIORITY 4: MOMENTUM SWING BOT (NEW - TEST SMALL)
    # Converted from Hyper-Scalper, unproven strategy
    # ==========================================
    
    engine.add_bot({
        'name': 'Momentum Swing Bot',
        'type': 'Momentum',  # NEW type
        'symbols': ['BTC/USDT', 'ETH/USDT'],  # Only top 2 for safety
        
        # Position Management (SMALLEST allocation - unproven)
        'amount': 150,
        'initial_balance': 1000,
        'max_positions': 2,
        
        # Entry Criteria
        'min_24h_move': 0.05,         # 5% move in 24h to trigger
        'must_be_above_sma20': True,  # Trend confirmation
        'min_volume_ratio': 1.3,      # 30% above average volume
        'min_confluence': 70,
        
       # Exit Rules
        'take_profit_pct': 0.10,      # 10% target (let momentum run)
        'stop_loss_pct': 0.04,        # -4% stop (wider than scalping)
        'trailing_stop_pct': 0.06,    # 6% trail once +8%
        'max_hold_hours': 288,        # 12 days max (momentum swing timeframe)
        
        # Safety
        'circuit_breaker_daily': -60,
        'circuit_breaker_weekly': -150
    })
    
    # ==========================================
    # 🔍 KEEP RUNNING: HIDDEN GEM MONITOR
    # Already profitable (+$720), no changes needed
    # ==========================================
    
    engine.add_bot({
        'name': 'Hidden Gem Monitor',
        'type': 'Buy-the-Dip',
        'symbols': [
            'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'POL/USDT',
            'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'NEAR/USDT', 'ALGO/USDT',
            'FIL/USDT', 'HBAR/USDT', 'ICP/USDT', 'VET/USDT', 'SAND/USDT',
            'MANA/USDT', 'AAVE/USDT', 'XTZ/USDT'
        ],
        'amount': 100,
        'initial_balance': 1800,
        'take_profit_pct': 0.10,
        'stop_loss_pct': 0.20,
        'max_hold_hours': 72,
        'max_exposure_per_coin': 100
    })
    
    # ==========================================
    # 🔕 DEACTIVATED: DIP SNIPER (0 TRADES - BROKEN)
    # Will investigate separately
    # ==========================================
    
    # Send startup notification
    if engine.notifier:
        active_bots_summary = []
        for b in engine.active_bots:
            syms = [s.split('/')[0] for s in b.get('symbols', [])[:5]]
            if len(b.get('symbols', [])) > 5:
                syms.append("...")
            active_bots_summary.append({
                'name': b['name'],
                'symbols': syms,
                'total_count': len(b.get('symbols', []))
            })
        engine.notifier.notify_startup(TRADING_MODE, active_bots_summary)
    
    # Initialize and run
    try:
        engine.start()
    except Exception as e:
        print(f"⚠️ Engine startup warning: {e}")
    
    print("=" * 80)
    print(f"🚀 Bot Running - {TRADING_MODE.upper()} Mode")
    print("   Portfolio Allocation:")
    print("   - Grid Bots:      $6,000 (43%) ← SCALED UP!")
    print("   - SMA Trend:      $4,000 (29%)")
    print("   - Buy-the-Dip:    $3,000 (21%) ← Clean slate test")
    print("   - Momentum Swing: $1,000 (7%)  ← New strategy")
    print("   Expected Monthly: +$7,730 (55% return)")
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
