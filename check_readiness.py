import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def check_analysis_readiness():
    conn = sqlite3.connect('data/trades.db')
    
    # 1. Check Trades since Dec 5th (Deployment of Grid/Scalper V2)
    cutoff_time = datetime(2025, 12, 5, 18, 0) # Approx time of reboot
    
    # Get trades
    trades = pd.read_sql_query(f"SELECT * FROM trades WHERE timestamp > '{cutoff_time}'", conn)
    
    print(f"\n--- ANALYSIS READINESS REPORT ---")
    print(f"Time Since Update: {(datetime.now() - cutoff_time).total_seconds()/3600:.1f} hours")
    
    if trades.empty:
        print("❌ No trades found since update.")
        return
        
    print(f"Total Trades: {len(trades)}")
    
    # Breakdown by Strategy
    print("\n--- Strategy Breakdown ---")
    strategy_counts = trades['strategy'].value_counts()
    print(strategy_counts)
    
    # Check for Grid Bot Activity
    grid_trades = trades[trades['strategy'].str.contains('Grid', case=False, na=False)]
    if not grid_trades.empty:
        print(f"\n✅ Grid Bot Active: {len(grid_trades)} trades")
    else:
        print(f"\n⚠️ No Grid Bot trades yet.")

    # Check for Scalper Volume
    scalper_trades = trades[trades['strategy'].str.contains('Scalper', case=False, na=False)]
    if not scalper_trades.empty:
        print(f"✅ Scalper Active: {len(scalper_trades)} trades")
    else:
        print(f"⚠️ No Scalper trades (check RSI settings?)")
        
    # Recommendation
    print("\n--- RECOMMENDATION ---")
    if len(trades) < 20:
        print("WAIT. Not enough data for meaningful statistical analysis.")
    elif (datetime.now() - cutoff_time).total_seconds() < 24 * 3600:
        print("PRELIMINARY ONLY. Less than 24 hours of data. Good for spot-checking, but too early for strategy tuning.")
    else:
        print("GO. Sufficient data for initial review.")
        
    conn.close()

if __name__ == "__main__":
    check_analysis_readiness()
