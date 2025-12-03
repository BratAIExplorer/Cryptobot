import sqlite3
import pandas as pd
import os

db_path = 'c:/CryptoBot_Project/crypto_trading_bot/data/trades.db'

def analyze_performance():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    # Get all trades
    query = "SELECT * FROM trades"
    try:
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No trades found in database.")
            return

        print(f"Total Trades Analyzed: {len(df)}")
        print("-" * 30)

        # Group by strategy
        strategies = df['strategy'].unique()
        
        for strategy in strategies:
            strat_df = df[df['strategy'] == strategy]
            
            # Calculate metrics
            total_trades = len(strat_df)
            
            # Check if profit column exists and is numeric
            if 'profit' in strat_df.columns:
                # Filter for closed trades (where profit is not null/0 if that's how it's stored)
                # Assuming 'side' == 'SELL' contains the profit info or profit column is populated
                # Let's look at the schema from previous turns: profit is in 'positions' table usually, 
                # but let's check 'trades' table structure.
                # Actually, logger.py logs to 'trades' table. Let's verify if profit is logged there.
                pass
            
            # Let's look at the columns first to be sure
            print(f"\nStrategy: {strategy}")
            print(f"Columns: {strat_df.columns.tolist()}")
            print(f"Count: {total_trades}")
            
            # If we have a profit column
            if 'profit' in strat_df.columns:
                # Convert to numeric, forcing errors to NaN
                strat_df['profit'] = pd.to_numeric(strat_df['profit'], errors='coerce')
                
                wins = strat_df[strat_df['profit'] > 0]
                losses = strat_df[strat_df['profit'] <= 0]
                
                win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
                total_pnl = strat_df['profit'].sum()
                
                print(f"Win Rate: {win_rate:.2f}%")
                print(f"Total PnL: ${total_pnl:.2f}")
                
                # Check for rapid firing (churn)
                # Convert timestamp
                if 'timestamp' in strat_df.columns:
                    strat_df['timestamp'] = pd.to_datetime(strat_df['timestamp'])
                    strat_df = strat_df.sort_values('timestamp')
                    
                    # Calculate time difference between trades
                    strat_df['time_diff'] = strat_df['timestamp'].diff().dt.total_seconds() / 60 # in minutes
                    avg_time_diff = strat_df['time_diff'].mean()
                    print(f"Avg Time Between Trades: {avg_time_diff:.1f} minutes")
                    
                    # Check for very fast trades (< 1 min)
                    fast_trades = len(strat_df[strat_df['time_diff'] < 1])
                    if fast_trades > 0:
                        print(f"⚠️ Warning: {fast_trades} trades executed within 1 minute of previous trade.")

    except Exception as e:
        print(f"Error analyzing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_performance()
