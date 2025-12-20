#!/usr/bin/env python3
"""
Grid Bot Backtest for MEXC
12-month validation with MEXC-specific parameters

DATABASE SEPARATION:
- Results: backtest_results/grid_bot_mexc_*.json
- Exchange tag: 'MEXC'
- Mode tag: 'backtest'
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtest_mexc_engine import MEXCBacktestEngine
import pandas as pd

def grid_bot_strategy(symbol='BTC/USDT', num_grids=5, range_pct=0.10):
    """
    Proper Grid Bot strategy for MEXC backtest
    
    How it works:
    1. Calculate price range from recent volatility
    2. Create grid levels (buy zones and sell zones)
    3. Buy when price drops to lower grid, sell when rises to upper grid
    4. Uses mean reversion: buy low, sell high within range
    
    Parameters:
    - num_grids: Number of grid levels (default 5)
    - range_pct: Trading range as % (default 10%)
    """
    
    # Track state between calls
    state = {'position': False, 'last_action': None, 'buy_price': 0}
    
    def strategy_func(data, i):
        if i < 200:  # Need more history for stable grid
            return None
        
        current_price = data['close'].iloc[i]
        
        # Calculate grid range from recent price action
        lookback = data.iloc[i-200:i]
        price_high = lookback['high'].max()
        price_low = lookback['low'].min()
        price_mid = (price_high + price_low) / 2
        
        # Define grid range (10% above and below mid)
        range_size = price_mid * range_pct
        upper_bound = price_mid + range_size
        lower_bound = price_mid - range_size
        
        # Calculate grid step
        grid_step = (upper_bound - lower_bound) / num_grids
        
        # Buy logic: Price in lower 40% of range and no position
        buy_threshold = lower_bound + (grid_step * 2)  # Lower 2 grids
        
        # Sell logic: Price in upper 40% of range and have position
        sell_threshold = upper_bound - (grid_step * 2)  # Upper 2 grids
        
        # Execute trades
        if current_price <= buy_threshold and not state['position']:
            state['position'] = True
            state['buy_price'] = current_price
            state['last_action'] = 'BUY'
            return 'BUY'
        
        elif current_price >= sell_threshold and state['position']:
            # Only sell if we have a profit
            if current_price > state['buy_price'] * 1.005:  # At least 0.5% profit
                state['position'] = False
                state['last_action'] = 'SELL'
                return 'SELL'
        
        return None
    
    return strategy_func

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
    capital = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    # Load MEXC historical data
    data_file = f'data/mexc_history/{symbol.replace("/", "_")}_1h_12m.csv'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print(f"   Run: python download_mexc_history.py first")
        sys.exit(1)
    
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['symbol'] = symbol
    
    # Run backtest with proper initialization
    engine = MEXCBacktestEngine(f'Grid_Bot_{symbol.replace("/", "_")}', initial_capital=capital)
    
    # Use fewer grids and wider range for better results
    strategy = grid_bot_strategy(symbol=symbol, num_grids=5, range_pct=0.10)
    
    print(f"\n🤖 Running Grid Bot backtest on {symbol}")
    print(f"   Capital: ${capital}")
    print(f"   Period: 12 months")
    print(f"   Strategy: 5-level grid, 10% range\n")
    
    engine.run_backtest(df, strategy)
    
    # Save results
    report = engine.save_results()
    
    # Print verdict
    if report:
        if report['win_rate_pct'] > 55 and report['roi_pct'] > 15:
            print(f"\n✅ VERDICT: DEPLOY TO MEXC")
        elif report['win_rate_pct'] > 50 and report['roi_pct'] > 10:
            print(f"\n🟡 VERDICT: NEEDS OPTIMIZATION")
        else:
            print(f"\n🔴 VERDICT: DO NOT DEPLOY")
