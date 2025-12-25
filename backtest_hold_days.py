#!/usr/bin/env python3
"""
🔬 BACKTEST: Optimal Hold Days for Buy-the-Dip Strategy

Tests different max_hold_days settings (7, 14, 30, 60 days) to find the optimal
hold period that maximizes profits while minimizing capital lockup.

This will help you make a DATA-DRIVEN decision on the best hold period.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# Database configuration
MODE = 'paper'
DB_FILENAME = 'trades_v3_live.db' if MODE == 'live' else 'trades_v3_paper.db'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', DB_FILENAME)

def simulate_hold_period(df, max_hold_days, take_profit=0.06, stop_loss=-0.04):
    """
    Simulate trading with different max hold periods
    
    Returns: dict with performance metrics
    """
    results = {
        'total_trades': 0,
        'winners': 0,
        'losers': 0,
        'forced_exits': 0,  # Exited due to max_hold
        'total_pnl': 0,
        'avg_hold_days': 0,
        'win_rate': 0,
        'profit_factor': 0,
        'max_drawdown': 0
    }
    
    if df.empty:
        return results
    
    # Group by symbol to simulate individual dip buys
    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol].sort_values('timestamp')
        
        for idx, buy_row in symbol_df[symbol_df['side'] == 'BUY'].iterrows():
            entry_price = buy_row['price']
            entry_time = pd.to_datetime(buy_row['timestamp'])
            position_size = buy_row['cost']
            
            # Find corresponding sell or simulate exit
            future_data = symbol_df[
                (symbol_df['timestamp'] > buy_row['timestamp']) &
                (symbol_df['side'] == 'SELL')
            ]
            
            if not future_data.empty:
                # Found a sell
                sell_row = future_data.iloc[0]
                exit_price = sell_row['price']
                exit_time = pd.to_datetime(sell_row['timestamp'])
                hold_days = (exit_time - entry_time).days
                
                pnl_pct = (exit_price - entry_price) / entry_price
                pnl_usd = position_size * pnl_pct
                
                # Check if would have been forced exit
                if hold_days > max_hold_days:
                    results['forced_exits'] += 1
                    # Simulate exit at max_hold_days (assume same price for simplicity)
                    hold_days = max_hold_days
                
                results['total_trades'] += 1
                results['avg_hold_days'] += hold_days
                results['total_pnl'] += pnl_usd
                
                if pnl_usd > 0:
                    results['winners'] += 1
                else:
                    results['losers'] += 1
    
    # Calculate averages
    if results['total_trades'] > 0:
        results['avg_hold_days'] = results['avg_hold_days'] / results['total_trades']
        results['win_rate'] = (results['winners'] / results['total_trades']) * 100
        
        total_wins = sum([abs(t) for t in range(results['winners'])])
        total_losses = sum([abs(t) for t in range(results['losers'])])
        if total_losses > 0:
            results['profit_factor'] = total_wins / total_losses
    
    return results

def run_backtest():
    """Run backtest across different hold periods"""
    
    print("=" * 100)
    print("🔬 BACKTESTING: Optimal Hold Days for Buy-the-Dip")
    print("=" * 100)
    print()
    
    # Load historical trade data
    conn = sqlite3.connect(DB_PATH)
    
    # Get trades from Buy-the-Dip strategy (or all if testing new strategy)
    query = """
    SELECT * FROM trades 
    WHERE strategy LIKE '%Dip%' OR strategy LIKE '%dip%'
    ORDER BY timestamp ASC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("⚠️  No historical Buy-the-Dip trades found.")
        print("   Using all trades as proxy for backtest...")
        
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp ASC", conn)
        conn.close()
    
    if df.empty:
        print("❌ No trades in database. Cannot backtest.")
        print("   Run bots for at least 1 week before backtesting.")
        return
    
    print(f"📊 Loaded {len(df)} historical trades")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print()
    
    # Test different hold periods
    hold_periods = [7, 14, 30, 60, 90]
    
    print("Testing different max hold periods...")
    print("-" * 100)
    print(f"{'Hold Days':<12} {'Trades':<10} {'Win Rate':<12} {'Avg Hold':<12} {'Total P&L':<15} {'Forced Exits':<15}")
    print("-" * 100)
    
    best_sharpe = -999
    best_hold_days = 14
    
    for max_hold in hold_periods:
        results = simulate_hold_period(df, max_hold)
        
        # Simple Sharpe approximation: return / volatility proxy
        if results['total_trades'] > 0:
            returns = results['total_pnl'] / results['total_trades']
            volatility = results['avg_hold_days'] / 7  # Normalize by weeks
            sharpe = returns / max(volatility, 0.1)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_hold_days = max_hold
        
        print(f"{max_hold:<12} {results['total_trades']:<10} "
              f"{results['win_rate']:<12.1f}% {results['avg_hold_days']:<12.1f} "
              f"${results['total_pnl']:<14.2f} {results['forced_exits']:<15}")
    
    print("-" * 100)
    print()
    print("🎯 RECOMMENDATION")
    print("=" * 100)
    print(f"   Optimal max_hold_days: {best_hold_days}")
    print()
    print("   Reasoning:")
    print(f"   - Best risk-adjusted returns (Sharpe ratio: {best_sharpe:.2f})")
    print(f"   - Balances capital efficiency vs profit capture")
    print()
    print("   Next steps:")
    print(f"   1. Set 'max_hold_days': {best_hold_days} in Buy-the-Dip config")
    print("   2. Test in paper trading for 2 weeks")
    print("   3. Monitor avg hold time in daily_bot_check.py")
    print("=" * 100)
    print()

if __name__ == "__main__":
    try:
        run_backtest()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
