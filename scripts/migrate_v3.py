import sqlite3
import pandas as pd
import sys
import os
from datetime import datetime
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database, Position, Trade

def migrate():
    print("="*60)
    print("🚀 Starting Database Migration to V3 (SQLAlchemy)")
    print("="*60)
    
    # 1. Paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    old_db_path = os.path.join(root_dir, 'data', 'trades.db')
    new_db_path = os.path.join(root_dir, 'data', 'trades_v3.db')
    
    if not os.path.exists(old_db_path):
        print(f"❌ Old database not found at {old_db_path}")
        return

    # 2. Init New DB
    print(f"[1/4] Initializing new database: {new_db_path}")
    db = Database(new_db_path)
    db.init_db()
    session = db.get_session()
    
    # Check if already migrated
    existing_count = session.query(Position).count()
    if existing_count > 0:
        print(f"⚠️  Database already contains {existing_count} positions.")
        print("    Skipping migration to prevent duplicates.")
        print("    If you want to re-run, delete 'data/trades_v3.db' first.")
        return

    # 3. Connect to Old DB
    print(f"[2/4] Reading data from old database: {old_db_path}")
    conn_old = sqlite3.connect(old_db_path)
    
    # --- MIGRATE POSITIONS ---
    try:
        df_pos = pd.read_sql_query("SELECT * FROM positions", conn_old)
        print(f"      Found {len(df_pos)} positions to migrate")
        
        # Mapping old ID (int) -> new ID (UUID)
        pos_id_map = {}
        
        for index, row in df_pos.iterrows():
            # Generate new UUID
            new_id = str(uuid.uuid4())
            pos_id_map[row['id']] = new_id
            
            # Parse dates
            buy_ts = pd.to_datetime(row['buy_timestamp']).to_pydatetime() if row['buy_timestamp'] else datetime.utcnow()
            
            # Handle sell_timestamp if it exists (for closed positions)
            sell_ts_val = row.get('sell_timestamp')
            updated_at = pd.to_datetime(sell_ts_val).to_pydatetime() if sell_ts_val else buy_ts
            
            # Create new Position object
            pos = Position(
                id=new_id,
                bot_id=row.get('strategy', 'Unknown_Bot'), # In old schema, strategy column fits here
                strategy=row.get('strategy', 'Unknown_Strategy'),
                symbol=row['symbol'],
                entry_date=buy_ts,
                entry_price=row['buy_price'],
                amount=row['amount'],
                position_size_usd=row['cost'],
                
                # Snapshot of current state
                current_price=row['buy_price'], # Reset to entry, updated by bot later
                current_value_usd=row['cost'],
                unrealized_pnl_pct=0.0,
                unrealized_pnl_usd=0.0,
                
                status=row['status'],
                entry_rsi=row.get('entry_rsi'),
                
                created_at=buy_ts,
                updated_at=updated_at
            )
            session.add(pos)
            
        session.commit()
        print(f"      ✅ Migrated {len(df_pos)} positions")
        
    except Exception as e:
        print(f"      ⚠️ Error migrating positions (maybe table empty?): {e}")

    # --- MIGRATE TRADES ---
    try:
        df_trades = pd.read_sql_query("SELECT * FROM trades", conn_old)
        print(f"      Found {len(df_trades)} trades to migrate")
        
        count = 0
        for index, row in df_trades.iterrows():
            # Check if this trade is linked to an old position
            old_pos_id = row.get('position_id')
            new_pos_id = pos_id_map.get(old_pos_id) if old_pos_id else None
            
            # Parse date
            ts = pd.to_datetime(row['timestamp']).to_pydatetime() if row['timestamp'] else datetime.utcnow()
            
            trade = Trade(
                timestamp=ts,
                strategy=row['strategy'],
                symbol=row['symbol'],
                side=row['side'],
                price=row['price'],
                amount=row['amount'],
                cost=row['cost'],
                fee=row.get('fee', 0.0),
                rsi=row.get('rsi'),
                market_condition=row.get('market_condition'),
                position_id=new_pos_id 
            )
            session.add(trade)
            count += 1
            
        session.commit()
        print(f"      ✅ Migrated {count} trades")
        
    except Exception as e:
        print(f"      ⚠️ Error migrating trades: {e}")

    print("="*60)
    print("✅ Migration Complete!")
    print(f"   New database is ready at: {new_db_path}")
    print("   Update your .env or config to point to this new DB.")
    print("="*60)

if __name__ == "__main__":
    migrate()
