import sqlite3
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logger import TradeLogger

def main():
    print("=" * 60)
    print("🤖 Crypto Bot Performance Report (Secondary DB)")
    print("=" * 60)
    
    # Use default DB path (which is now absolute in logger.py)
    logger = TradeLogger()
    
    # 1. Bot Status
    print("\n📊 Bot Status:")
    try:
        bot_status = logger.get_bot_status()
        if bot_status is not None and not bot_status.empty:
            print(bot_status[['strategy', 'status', 'total_pnl', 'wallet_balance', 'total_trades']].to_string(index=False))
        else:
            print("No active bots found in database.")
    except Exception as e:
        print(f"Error reading bot status: {e}")

    # 2. Open Positions
    print("\n📈 Open Positions:")
    try:
        positions = logger.get_open_positions()
        if not positions.empty:
            print(positions[['strategy', 'symbol', 'buy_price', 'amount', 'cost', 'buy_timestamp']].to_string(index=False))
        else:
            print("No open positions.")
    except Exception as e:
        print(f"Error reading positions: {e}")

    # 3. Recent Trades
    print("\n📜 Recent Trades (Last 10):")
    try:
        trades = logger.get_trades()
        if not trades.empty:
            print(trades[['timestamp', 'strategy', 'symbol', 'side', 'price', 'amount', 'cost']].head(10).to_string(index=False))
        else:
            print("No trades executed yet.")
    except Exception as e:
        print(f"Error reading trades: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
