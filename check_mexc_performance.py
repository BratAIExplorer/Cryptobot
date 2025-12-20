
import sqlite3
import pandas as pd
import os

db_paths = [
    'c:/CryptoBot_Project/data/trades_v3.db',
    'c:/CryptoBot_Project/data/trades.db',
    'c:/CryptoBot_Project/data/trades_v3_paper.db',
    'c:/CryptoBot_Project/data/trades_mexc_paper.db'
]

def check_mexc_stats(db_path):
    if not os.path.exists(db_path):
        return None
    
    print(f"\n--- Checking DB: {db_path} ---")
    conn = sqlite3.connect(db_path)
    
    # Check Bot Status
    try:
        status_df = pd.read_sql_query("SELECT * FROM bot_status WHERE strategy LIKE '%MEXC%'", conn)
        if not status_df.empty:
            print("Bot Status:")
            print(status_df[['strategy', 'status', 'total_trades', 'total_pnl', 'wallet_balance']])
        else:
            print("No MEXC bots found in bot_status table.")
    except Exception as e:
        print(f"Error checking bot_status: {e}")
        
    # Check Active Positions
    try:
        pos_df = pd.read_sql_query("SELECT symbol, strategy, entry_price, current_price, unrealized_pnl_usd FROM positions WHERE status = 'OPEN' AND strategy LIKE '%MEXC%'", conn)
        if not pos_df.empty:
            print("\nOpen Positions:")
            print(pos_df)
        else:
            print("\nNo open MEXC positions.")
    except Exception as e:
        print(f"Error checking positions: {e}")

    # Check Total PnL from trades
    try:
        trades_df = pd.read_sql_query("SELECT strategy, side, symbol, price, amount FROM trades WHERE strategy LIKE '%MEXC%'", conn)
        if not trades_df.empty:
            print(f"\nTotal MEXC trades recorded: {len(trades_df)}")
        else:
             print("\nNo MEXC trades recorded.")
    except Exception as e:
        print(f"Error checking trades: {e}")

    conn.close()

for path in db_paths:
    check_mexc_stats(path)
