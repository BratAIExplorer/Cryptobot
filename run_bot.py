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
        # PROFITABILITY ANALYSIS (OPTIMIZED):
        # Investment Budget: $250 (Small Start)
        # Price Range: $90,000 - $100,000 (Centered on current $95k)
        # Grid Step: ~$256 price change per line (0.27% spread)
        # Net Profit: ~0.4% per successful trade (higher frequency)
        # Trade Size: $20 (allows ~12 active positions max with $250)
        # Expected: 15-30 trades/day vs 1 trade/day previously
        'amount': 20,           # Trade size per grid line (reduced for more positions)
        'grid_levels': 40,      # Increased from 20 (more trading opportunities)
        'atr_multiplier': 2.0,
        'atr_period': 14,
        'lower_limit': 90000,   # Tightened from 85000 (better price tracking)
        'upper_limit': 100000,  # Tightened from 110000 ($10k range instead of $25k)
        'initial_balance': 250,
        'max_exposure_per_coin': 250,
        'max_concurrent_positions': 10  # Allow pyramiding (was implicitly 1)
    })
    
    engine.add_bot({
        'name': 'Grid Bot ETH',
        'type': 'Grid',
        'symbols': ['ETH/USDT'],
        # Budget: $250
        # Current config is GOOD ($48 grid step)
        # Just adding max_concurrent_positions to allow pyramiding
        'amount': 25,
        'grid_levels': 30,
        'atr_multiplier': 2.5,
        'atr_period': 14,
        'lower_limit': 2800,
        'upper_limit': 4200,
        'initial_balance': 250,
        'max_exposure_per_coin': 250,
        'max_concurrent_positions': 10  # Allow pyramiding
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

    # engine.add_bot({
    #     'name': 'SMA Trend Bot V2',
    #     'type': 'SMA',
    #     'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT'],
    #     'amount': 300,
    #     'initial_balance': 4000,
    #     'max_exposure_per_coin': 900,
    #     'sma_fast': 20,
    #     'sma_slow': 50,
    #     'use_crossover': True,
    #     'adx_threshold': 25,
    #     'take_profit_pct': 0.10,
    #     'stop_loss_pct': 0.05,
    #     'trailing_stop': True,
    #     'trailing_stop_pct': 0.04,
    #     'trailing_activates_at': 0.06,
    #     'max_hold_hours': 504,
    #     'circuit_breaker_daily': -100,
    #     'circuit_breaker_weekly': -300
    # })
    
    # ==========================================
    # 🚀 PRIORITY 3: BUY-THE-DIP (HYBRID V2.0)
    # Dynamic Time-Weighted TP + Trailing Stops + Quality Floors
    # ==========================================

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

        # Entry Conditions (V3) - OPTIMIZED FOR RANGING MARKET
        'dip_threshold': 0.02,       # Lowered from 3% to 2% (current market shows 2-3% dips)
        'rsi_limit': 35,             # V3 param (good as is)
        'cooldown_minutes': 60,

        # Legacy/Hybrid Fallbacks
        'dip_percentage': 0.02,      # Updated to match dip_threshold
        'min_confluence': 65,

        # PROFIT RULES (User Request: 5-10% Profit, NO Losses)
        'take_profit_pct': 0.08,      # Target 8% Profit
        'stop_loss_pct': None,        # DISABLING STOP LOSS (Hold until profit)
        'stop_loss_enabled': False,

        'max_daily_trades': 3,
        'circuit_breaker_daily': -100,
        'circuit_breaker_weekly': -300
    })
    
    # ==========================================
    # ⏸️  MOMENTUM SWING BOT (PAUSED - NEEDS BACKTEST!)
    # ==========================================
    # STATUS: Reduced to $500 test allocation
    # ISSUE: Strategy type 'Momentum' not implemented (falls back to DCA)
    # ACTION NEEDED: Backtest first, then decide fix or kill
    # Expected backtest time: 2 hours

    # engine.add_bot({
    #     'name': 'Momentum Swing Bot',
    #     'type': 'Momentum',  # WARNING: Not implemented! Falls back to DCA
    #     'symbols': ['BTC/USDT', 'ETH/USDT'],
    #     'amount': 75,
    #     'initial_balance': 500,
    #     'max_positions': 2,
    #     'min_24h_move': 0.05,
    #     'must_be_above_sma20': True,
    #     'min_volume_ratio': 1.3,
    #     'min_confluence': 70,
    #     'take_profit_pct': 0.10,
    #     'stop_loss_pct': 0.04,
    #     'trailing_stop_pct': 0.06,
    #     'max_hold_hours': 288,
    #     'circuit_breaker_daily': -60,
    #     'circuit_breaker_weekly': -150
    # })
    
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
