"""
Test script for position updater fix.
Creates fake positions, updates them, verifies P&L calculation.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project to path
sys.path.append(os.getcwd())

from core.logger import TradeLogger
from core.exchanges.binance_adapter import BinanceAdapter

def test_updater():
    print("🧪 Testing Position Updater...")
    
    # Create test database
    test_db = "data/test_updater.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Initialize
    logger = TradeLogger(db_path=test_db, mode='paper')
    exchange = BinanceAdapter(mode='paper')
    
    print("\n1️⃣ Creating test position...")
    
    # Create a fake position (BTC at $90,000)
    position_id = logger.log_position(
        symbol='BTC/USDT',
        buy_price=90000.0,
        amount=0.001,
        bot_id='test-bot',
        strategy='Test Strategy'
    )
    
    print(f"   ✅ Position created: {position_id}")
    
    # Verify initial state
    import pandas as pd
    from sqlalchemy import text
    
    with logger.db.engine.connect() as conn:
        df = pd.read_sql(text("SELECT symbol, entry_price, current_price, unrealized_pnl_pct FROM positions WHERE status='OPEN'"), conn)
    
    print(f"\n2️⃣ Initial state:")
    print(df.to_string(index=False))
    
    # Update prices
    print(f"\n3️⃣ Updating prices from exchange...")
    updated = logger.update_open_position_prices(exchange)
    print(f"   ✅ Updated {updated} position(s)")
    
    # Verify update
    with logger.db.engine.connect() as conn:
        df = pd.read_sql(text("SELECT symbol, entry_price, current_price, unrealized_pnl_pct, unrealized_pnl_usd FROM positions WHERE status='OPEN'"), conn)
    
    print(f"\n4️⃣ After update:")
    print(df.to_string(index=False))
    
    # Validation
    if df.iloc[0]['current_price'] != df.iloc[0]['entry_price']:
        print("\n✅ TEST PASSED: current_price was updated!")
        print(f"   Entry: ${df.iloc[0]['entry_price']:.2f}")
        print(f"   Current: ${df.iloc[0]['current_price']:.2f}")
        print(f"   P&L: {df.iloc[0]['unrealized_pnl_pct']:.2f}%")
    else:
        print("\n❌ TEST FAILED: current_price still equals entry_price")
    
    # Cleanup
    os.remove(test_db)
    print("\n🧹 Cleanup complete")

if __name__ == "__main__":
    test_updater()
