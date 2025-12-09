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

    # 3. Check PnL
    # Strategy specific PnL check
    dip_pnl = logger.get_pnl_summary('Buy-the-Dip Strategy')
    scalper_pnl = logger.get_pnl_summary('Hyper-Scalper Bot')
    
    print(f"\n[PnL Summary]")
    print(f"   Buy-the-Dip: ${dip_pnl:.2f}")
    print(f"   Hyper-Scalper: ${scalper_pnl:.2f}")

    print("\n✅ Verification Complete")
    
if __name__ == "__main__":
    verify_migration()
