import sqlite3
import shutil
import os

# Paths
ROOT_DB = 'data/trades.db'
INNER_DB = 'crypto_trading_bot/data/trades.db'
MERGED_DB = 'data/trades_merged.db'

def merge_databases():
    print("Starting Database Merge...")
    
    # 1. Start with the Inner DB (it has more data)
    if os.path.exists(MERGED_DB):
        os.remove(MERGED_DB)
    shutil.copy(INNER_DB, MERGED_DB)
    print(f"Copied Inner DB ({INNER_DB}) to {MERGED_DB}")
    
    # 2. Connect to both
    conn_dest = sqlite3.connect(MERGED_DB)
    conn_src = sqlite3.connect(ROOT_DB)
    
    c_dest = conn_dest.cursor()
    c_src = conn_src.cursor()
    
    # 2b. Migrate Schema if needed (Add RSI columns)
    print("Checking schema compatibility...")
    c_dest.execute("PRAGMA table_info(positions)")
    columns = {row[1] for row in c_dest.fetchall()}
    
    if 'entry_rsi' not in columns:
        print("  Migrating: Adding entry_rsi column")
        c_dest.execute("ALTER TABLE positions ADD COLUMN entry_rsi REAL")
    if 'exit_rsi' not in columns:
        print("  Migrating: Adding exit_rsi column")
        c_dest.execute("ALTER TABLE positions ADD COLUMN exit_rsi REAL")
        
    # Check trades table too
    c_dest.execute("PRAGMA table_info(trades)")
    trade_columns = {row[1] for row in c_dest.fetchall()}
    if 'engine_version' not in trade_columns:
        print("  Migrating: Adding engine_version column")
        c_dest.execute("ALTER TABLE trades ADD COLUMN engine_version TEXT DEFAULT '2.0'")
    if 'strategy_version' not in trade_columns:
        print("  Migrating: Adding strategy_version column")
        c_dest.execute("ALTER TABLE trades ADD COLUMN strategy_version TEXT DEFAULT '1.0'")
        
    conn_dest.commit()

    
    # 3. Merge Bot Status (Upsert)
    print("Merging Bot Status...")
    c_src.execute("SELECT * FROM bot_status")
    rows = c_src.fetchall()
    for row in rows:
        # Strategy is primary key (index 0)
        strategy = row[0]
        print(f"  Processing status for: {strategy}")
        
        # Check if exists in dest
        c_dest.execute("SELECT * FROM bot_status WHERE strategy = ?", (strategy,))
        existing = c_dest.fetchone()
        
        if not existing:
            print(f"    -> Importing new strategy status: {strategy}")
            c_dest.execute("INSERT INTO bot_status VALUES (?,?,?,?,?,?,?)", row)
        else:
            print(f"    -> Strategy {strategy} already exists. Keeping Inner DB version (likely more recent).")

    # 4. Merge Positions
    print("Merging Positions...")
    # We need to be careful with IDs. We should reset IDs or just append and let AutoIncrement handle it?
    # Actually, if we just append, we lose the link to trades if trades use position_id.
    # But the Root DB only has SMA Trend Bot trades. The Inner DB has others.
    # Let's check if IDs collide.
    
    c_src.execute("SELECT * FROM positions")
    src_positions = c_src.fetchall()
    
    # Get max ID in dest
    c_dest.execute("SELECT MAX(id) FROM positions")
    max_id = c_dest.fetchone()[0] or 0
    
    id_map = {} # Old ID -> New ID
    
    for pos in src_positions:
        old_id = pos[0]
        # Check if this position (same symbol/strategy/buy_time) already exists
        # This is to prevent duplicates if the DBs were partially synced
        symbol = pos[1]
        strategy = pos[2]
        buy_time = pos[4]
        
        c_dest.execute("SELECT id FROM positions WHERE symbol=? AND strategy=? AND buy_timestamp=?", (symbol, strategy, buy_time))
        existing = c_dest.fetchone()
        
        if existing:
            print(f"  Skipping duplicate position: {symbol} ({strategy})")
            id_map[old_id] = existing[0]
        else:
            # Insert as new
            new_pos = list(pos)
            new_pos[0] = None # Let DB assign new ID
            
            # We need to construct the INSERT statement dynamically or explicitly
            # positions table has 13 columns in the schema I saw earlier
            placeholders = ','.join(['?'] * len(new_pos))
            c_dest.execute(f"INSERT INTO positions VALUES ({placeholders})", new_pos)
            new_id = c_dest.lastrowid
            id_map[old_id] = new_id
            print(f"  Imported position {old_id} -> {new_id}: {symbol} ({strategy})")

    # 5. Merge Trades
    print("Merging Trades...")
    c_src.execute("SELECT * FROM trades")
    src_trades = c_src.fetchall()
    
    for trade in src_trades:
        # Check duplicate (timestamp, strategy, symbol, side)
        timestamp = trade[1]
        strategy = trade[2]
        symbol = trade[3]
        side = trade[4]
        
        c_dest.execute("SELECT id FROM trades WHERE timestamp=? AND strategy=? AND symbol=? AND side=?", (timestamp, strategy, symbol, side))
        existing = c_dest.fetchone()
        
        if existing:
            print(f"  Skipping duplicate trade: {side} {symbol}")
        else:
            new_trade = list(trade)
            new_trade[0] = None # New ID
            
            # Update position_id if it exists
            old_pos_id = new_trade[10] # position_id is usually index 10, check schema
            if old_pos_id in id_map:
                new_trade[10] = id_map[old_pos_id]
            
            placeholders = ','.join(['?'] * len(new_trade))
            c_dest.execute(f"INSERT INTO trades VALUES ({placeholders})", new_trade)
            print(f"  Imported trade: {side} {symbol}")

    conn_dest.commit()
    conn_dest.close()
    conn_src.close()
    print("Merge Complete!")
    print(f"Merged DB saved to: {MERGED_DB}")

if __name__ == "__main__":
    merge_databases()
