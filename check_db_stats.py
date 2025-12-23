from core.database import Database, Position
import pandas as pd
import os

DB_PATH = 'data/trades_v3_paper.db'

def check():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB not found: {DB_PATH}")
        return

    db = Database(DB_PATH)
    session = db.get_session()
    
    try:
        # Check positions
        positions = session.query(Position).all()
        print(f"--- Database Stats ({DB_PATH}) ---")
        print(f"Total Positions: {len(positions)}")
        
        if positions:
            pnl_sum = sum(p.unrealized_pnl_usd for p in positions if p.unrealized_pnl_usd is not None)
            from collections import Counter
            strategies = Counter(p.strategy for p in positions)
            
            print(f"Total Migrated P&L: ${pnl_sum:.2f}")
            print("\nPositions per Strategy:")
            for strat, count in strategies.items():
                strat_pnl = sum(p.unrealized_pnl_usd for p in positions if p.strategy == strat and p.unrealized_pnl_usd is not None)
                print(f" - {strat}: {count} positions, P&L: ${strat_pnl:.2f}")
    except Exception as e:
        print(f"❌ Error checking DB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check()
