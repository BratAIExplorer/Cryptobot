#!/usr/bin/env python3
"""
Standalone bot runner - runs trading strategies 24/7 independently of the dashboard.
"""
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine

def main():
    print("=" * 60)
    print("🤖 Crypto Trading Bot - Standalone Runner")
    print("=" * 60)
    
    # Telegram config from environment variables
    telegram_config = None
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if tg_token and tg_chat_id:
        telegram_config = {'token': tg_token, 'chat_id': tg_chat_id}
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️  Telegram notifications disabled")
    
    # Initialize engine
    engine = TradingEngine(mode='paper', telegram_config=telegram_config)
    
    # ==========================================
    # 🚀 ALL-STAR PORTFOLIO CONFIGURATION
    # Based on Top 15 Coin Backtest Results
    # ==========================================
    
    # 1. SMA TREND BOT (The Champion)
    # Best for catching big moves. 40% of Capital.
    engine.add_bot({
        'name': 'SMA Trend Bot',
        'type': 'SMA',
        'symbols': ['DOGE/USDT', 'XRP/USDT', 'DOT/USDT', 'ATOM/USDT', 'ADA/USDT'],
        'amount': 800,  # $800 per coin ($4000 total)
        'initial_balance': 50000,
        'take_profit_pct': 0.03,  # 3%
        'stop_loss_pct': 0.05,    # 5%
        'max_hold_hours': 24,     # Force exit after 24h
        'max_exposure_per_coin': 800
    })
    
    # 2. BUY-THE-DIP STRATEGY (Value Investing)
    # Best for volatile dips. 25% of Capital.
    engine.add_bot({
        'name': 'Buy-the-Dip Strategy',
        'type': 'Buy-the-Dip',
        'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT', 'AVAX/USDT', 'SHIB/USDT', 'DOT/USDT', 'LINK/USDT', 'BCH/USDT', 'NEAR/USDT', 'LTC/USDT', 'UNI/USDT', 'PEPE/USDT', 'APT/USDT', 'ICP/USDT', 'ETC/USDT'],
        'amount': 800,  # $800 per coin ($2400 total)
        'initial_balance': 50000,
        'take_profit_pct': 0.10,  # Target 10% (Tiered exits handle the rest)
        'stop_loss_pct': 0.30,    # Max drawdown 30%
        'max_hold_hours': 2880,   # 120 days
        'max_exposure_per_coin': 800
    })
    
    # 3. HYPER-SCALPER BOT (Cash Flow)
    # Best for high volume. 35% of Capital.
    engine.add_bot({
        'name': 'Hyper-Scalper Bot',
        'type': 'Hyper-Scalper',
        'symbols': ['SOL/USDT', 'ETH/USDT', 'BTC/USDT', 'XRP/USDT'],
        'amount': 800,  # $800 per coin ($3200 total)
        'initial_balance': 50000,
        'rsi_limit': 30,          # Relaxed from 15 to 30 (Expert Rec)
        'take_profit_pct': 0.035, # 3.5% Aggressive Target (Expert Rec)
        'stop_loss_pct': 0.01,    # 1% Tight stop
        'max_hold_hours': 0.5,    # CRITICAL: 30 minutes max
        'max_exposure_per_coin': 800
    })

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
        'initial_balance': 50000,
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
        'initial_balance': 50000,
        'max_exposure_per_coin': 1000
    })

    # 5. HIDDEN GEM MONITOR (Paper Mode Exploration)
    # Tracking top 50 coins for dip opportunities.
    engine.add_bot({
        'name': 'Hidden Gem Monitor',
        'type': 'Buy-the-Dip',
        'symbols': [
            'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 
            'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'NEAR/USDT', 'ALGO/USDT',
            'FIL/USDT', 'HBAR/USDT', 'ICP/USDT', 'VET/USDT', 'SAND/USDT',
            'MANA/USDT', 'AAVE/USDT', 'EOS/USDT', 'XTZ/USDT', 'THETA/USDT'
        ],
        'amount': 100,  # Small test amount
        'initial_balance': 50000,
        'take_profit_pct': 0.10,
        'stop_loss_pct': 0.20,
        'max_hold_hours': 72,
        'max_exposure_per_coin': 100
    })
    
    print(f"✅ Loaded 5 Strategies: SMA Trend, Buy-the-Dip, Hyper-Scalper, Grid Bots, Hidden Gem Monitor")
    print("=" * 60)
    print("🚀 Starting bot... (Press Ctrl+C to stop)")
    print("=" * 60)
    
    try:
        engine.start()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping bot...")
        engine.stop()
        print("✅ Bot stopped successfully")

if __name__ == "__main__":
    main()
