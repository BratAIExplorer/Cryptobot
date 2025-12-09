import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import TradeLogger

def verify_migration():
    print("="*60)
    print("🔍 Verifying V3 Database Migration")
    print("="*60)
    
    logger = TradeLogger() # Defaults to trades_v3.db in logger.py
    
    # 1. Check Positions
    positions = logger.get_open_positions()
    print(f"\n[Open Positions] Count: {len(positions)}")
    if not positions.empty:
        print(positions[['id', 'symbol', 'strategy', 'entry_price', 'status']].head())
    else:
        print("   No open positions found.")

    # 2. Check Trades
    trades = logger.get_trades()
    print(f"\n[Trades History] Count: {len(trades)}")
    if not trades.empty:
        print(trades[['id', 'symbol', 'side', 'price', 'timestamp']].head())
    else:
        print("   No trades found.")

    # 3. Check PnL (Dynamic)
    print(f"\n[PnL Summary by Strategy]")
    
    # Get all unique strategies from trades or bot_status
    session = logger.db.get_session()
    try:
        # distinct strategies from positions
        strategies = pd.read_sql_query("SELECT DISTINCT strategy FROM positions", logger.db.engine)
        strategy_list = strategies['strategy'].tolist()
        
        total_pnl = 0.0
        for strat in strategy_list:
            pnl = logger.get_pnl_summary(strat)
            print(f"   {strat:<25}: ${pnl:.2f}")
            total_pnl += pnl
            
        print(f"   {'-'*35}")
        print(f"   {'TOTAL PROJECT PnL':<25}: ${total_pnl:.2f}")
        
    except Exception as e:
        print(f"   Error fetching strategies: {e}")
    finally:
        session.close()

    print("\n✅ Verification Complete")
    
if __name__ == "__main__":
    verify_migration()
