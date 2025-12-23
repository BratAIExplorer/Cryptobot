import sqlite3
import pandas as pd
import os
import uuid
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LEGACY_DB = os.path.join(ROOT_DIR, 'data', 'trades.db')
NEW_DB = os.path.join(ROOT_DIR, 'data', 'trades_v3_paper.db')

from core.database import Database

def migrate():
    print(f"--- Migrating Legacy Data ---")
    print(f"Source: {LEGACY_DB}")
    print(f"Target: {NEW_DB}")

    if not os.path.exists(LEGACY_DB):
        print(f"❌ Legacy DB not found at {LEGACY_DB}")
        return

    # Initialize V3 Database (Create Tables)
    db_v3 = Database(NEW_DB)
    db_v3.init_db()
    print("✅ V3 Database Initialized (Tables Created)")

    conn_old = sqlite3.connect(LEGACY_DB)
    conn_new = sqlite3.connect(NEW_DB)

    # 1. Migrate Trades
    print("\nMigrating Trades...")
    trades_df = pd.read_sql_query("SELECT * FROM trades", conn_old)
    # Map columns to V3 schema
    # V3 Trades: id (auto), timestamp, strategy, symbol, side, price, expected_price, slippage_pct, amount, cost, fee, rsi, market_condition, exchange, position_id
    
    for _, row in trades_df.iterrows():
        cursor = conn_new.cursor()
        cursor.execute("""
            INSERT INTO trades (timestamp, strategy, symbol, side, price, amount, cost, exchange)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get('timestamp', datetime.utcnow().isoformat()),
            row.get('strategy'),
            row.get('symbol'),
            row.get('side'),
            row.get('price'),
            row.get('amount'),
            row.get('cost'),
            row.get('exchange', 'MEXC')
        ))
    
    print(f"✅ Migrated {len(trades_df)} trades.")

    # 2. Migrate Positions (Summary to Status)
    print("\nMigrating Positions...")
    pos_df = pd.read_sql_query("SELECT * FROM positions", conn_old)
    # V3 Positions: id (uuid), bot_id, symbol, entry_date, entry_price, amount, status, strategy, exchange, created_at, updated_at
    
    for _, row in pos_df.iterrows():
        cursor = conn_new.cursor()
        pos_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO positions (id, bot_id, strategy, symbol, entry_date, entry_price, amount, status, unrealized_pnl_usd, exchange, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pos_id,
            row.get('strategy'),
            row.get('strategy'),
            row.get('symbol'),
            row.get('entry_date', datetime.utcnow().isoformat()),
            row.get('entry_price', row.get('price', 0)),
            row.get('amount'),
            row.get('status', 'CLOSED'),
            row.get('realized_pnl', row.get('pnl', row.get('unrealized_pnl_usd', 0.0))),
            row.get('exchange', 'MEXC'),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
    
    print(f"✅ Migrated {len(pos_df)} positions.")

    # 3. Update Bot Status (Initial sync)
    print("\nInitializing Bot Status table...")
    strategies = trades_df['strategy'].unique()
    for strat in strategies:
        cursor = conn_new.cursor()
        # Get stats
        strat_trades = trades_df[trades_df['strategy'] == strat]
        total_trades = len(strat_trades)
        # For PnL, we'd need more logic, but let's just use the count for now to show they exist.
        
        cursor.execute("""
            INSERT OR REPLACE INTO bot_status (strategy, status, started_at, total_trades, total_pnl, wallet_balance)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            strat,
            'STOPPED',
            datetime.utcnow().isoformat(),
            total_trades,
            0.0,
            20000.0 # Placeholder, will be updated by engine on start
        ))

    conn_old.close()
    conn_new.commit()
    conn_new.close()
    print("\n✅ Migration COMPLETE.")

if __name__ == "__main__":
    migrate()
