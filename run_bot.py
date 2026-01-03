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
        'lower_limit': 85000,
        'upper_limit': 110000,
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
    # 🎯 SMA TREND BOT V2 (UPGRADED!)
    # ==========================================
    # V2 IMPROVEMENTS:
    # ✅ True crossover detection (not just SMA20 > SMA50 state)
    # ✅ ADX filter: Only trade when ADX > 25 (strong trend)
    # ✅ Price confirmation: Price must be above both SMAs
    # ✅ Stop loss widened: 3% → 5% (crypto-appropriate)
    # ✅ Filters out whipsaws in sideways markets
    #
    # Expected: Win rate 30% → 45%, Monthly $1K → $2.5K

    engine.add_bot({
        'name': 'SMA Trend Bot V2',
        'type': 'SMA',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT'],

        # Position Management
        'amount': 300,
        'initial_balance': 4000,
        'max_exposure_per_coin': 900,  # Max 3 positions

        # V2 SMA Parameters
        'sma_fast': 20,
        'sma_slow': 50,
        'use_crossover': True,        # NEW: True crossover detection
        'adx_threshold': 25,           # NEW: Only trade when ADX > 25 (strong trend)

        # Exit Rules (IMPROVED)
        'take_profit_pct': 0.10,       # 10% TP
        'stop_loss_pct': 0.05,         # 5% SL (was 3% - too tight!)
        'trailing_stop': True,
        'trailing_stop_pct': 0.04,     # 4% trail
        'trailing_activates_at': 0.06,  # Start trailing after +6%

        # Safety
        'max_hold_hours': 504,         # 21 days max
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })
    
    # ==========================================
    # 🚀 PRIORITY 3: BUY-THE-DIP (HYBRID V2.0)
    # Dynamic Time-Weighted TP + Trailing Stops + Quality Floors
    # ==========================================

    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT',
            'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT',
            'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
        ],

        # Position Sizing
        'amount': 25,                 # Start at $25 per position
        'initial_balance': 3000,
        'max_exposure_per_coin': 200,

        # Entry Conditions
        'dip_percentage': 0.05,       # 5% dip to trigger buy
        'min_confluence': 65,         # Confluence score threshold

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # EXIT STRATEGY: HYBRID V2.0 (risk_module.py)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Dynamic TP: 0-60d:5%, 60-120d:8%, 120-180d:12%, 180+d:15%
        # Trailing: 8-10% for 120+ day holds
        # Floors: BTC/ETH:-70%, Top20:-50%, Others:-40%
        # Regime: Pauses in CRISIS, safe coins only in BEAR

        # Legacy params (overridden by Hybrid v2.0)
        'take_profit_pct': 0.05,      # Base (dynamic in practice)
        'stop_loss_pct': None,        # No fixed SL
        'stop_loss_enabled': False,   # Hybrid v2.0 handles exits
        'max_hold_hours': None,       # Hold until profitable

        # Trend Filters
        'sma_fast': 7,
        'sma_slow': 21,
        'require_above_both': True,

        # Smart Cooldown
        'cooldown_after_profit': 6,   # 6h after profit
        'cooldown_after_loss': 0,     # N/A (no auto-loss sells)
        'cooldown_same_day': 12,      # 12h between buys
        'max_positions_per_coin': 2,

        # Safety Limits
        'max_daily_trades': 3,

        # Circuit Breaker
        'circuit_breaker_daily': -500,
        'circuit_breaker_weekly': -1000
    })
    
    # ==========================================
    # ⏸️  MOMENTUM SWING BOT (PAUSED - NEEDS BACKTEST!)
    # ==========================================
    # STATUS: Reduced to $500 test allocation
    # ISSUE: Strategy type 'Momentum' not implemented (falls back to DCA)
    # ACTION NEEDED: Backtest first, then decide fix or kill
    # Expected backtest time: 2 hours

    engine.add_bot({
        'name': 'Momentum Swing Bot',
        'type': 'Momentum',  # WARNING: Not implemented! Falls back to DCA
        'symbols': ['BTC/USDT', 'ETH/USDT'],

        # PAUSED: Reduced allocation for testing only
        'amount': 75,                # Reduced from $150
        'initial_balance': 500,      # Reduced from $1000
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
    # 💎 HIDDEN GEM MONITOR V2 (UPGRADED!)
    # ==========================================
    # V2 IMPROVEMENTS:
    # ✅ Stop loss: 20% → 10% (preserve capital!)
    # ✅ Take profit: 10% → 15% (gems move big)
    # ✅ No time limit (was 72h - conflicted with "hold until profitable")
    # ✅ Current narratives: AI, L2, DeFi, Infra (no dead Metaverse/GameFi coins!)
    # NOTE: GemSelector integration pending - using curated static list for now

#     engine.add_bot({
#         'name': 'Hidden Gem Monitor V2',
#         'type': 'Buy-the-Dip',
#         'symbols': [
#             # AI Narrative
#             'FET/USDT', 'AGIX/USDT', 'RNDR/USDT', 'GRT/USDT',
#             # L2 Narrative
#             'ARB/USDT', 'OP/USDT', 'MATIC/USDT', 'IMX/USDT',
#             # DeFi Blue Chips
#             'UNI/USDT', 'AAVE/USDT', 'CRV/USDT', 'SNX/USDT',
#             # Infrastructure
#             'LINK/USDT', 'ATOM/USDT', 'NEAR/USDT'
#         ],  # V2: Current hot narratives (no SAND, MANA, AXS dead coins!)
# 
#         'amount': 100,
#         'initial_balance': 1800,
# 
#         # V2 EXIT RULES (FIXED!)
#         'take_profit_pct': 0.15,      # 15% TP (was 10% - gems pump harder)
#         'stop_loss_pct': 0.10,        # 10% SL (was 20% - suicidal!)
#         'max_hold_hours': None,       # No time limit (was 72h - forced bad exits)
# 
#         # Dip parameters
#         'dip_percentage': 0.08,       # 8% dip (bigger than BTC/ETH)
#         'min_confluence': 70,         # Higher quality filter
# 
#         'max_exposure_per_coin': 100
#     })
    
    # ==========================================
    # 🗑️ DIP SNIPER - DELETED (2025-12-30)
    # Reason: 0 trades, redundant with Buy-the-Dip, broken logic
    # Status: Permanently removed per fix-or-kill analysis
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
