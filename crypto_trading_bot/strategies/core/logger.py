import sqlite3
import pandas as pd
from datetime import datetime
import os

class TradeLogger:
    def __init__(self, db_path='data/trades.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Trades table (with versioning)
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                strategy TEXT,
                symbol TEXT,
                side TEXT,
                price REAL,
                amount REAL,
                cost REAL,
                fee REAL,
                rsi REAL,
                market_condition TEXT,
                position_id INTEGER,
                engine_version TEXT DEFAULT '2.0',
                strategy_version TEXT DEFAULT '1.0'
            )
        ''')
        
        # Positions table (FIFO tracking)
        c.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                strategy TEXT,
                buy_price REAL,
                buy_timestamp DATETIME,
                amount REAL,
                cost REAL,
                status TEXT,
                sell_price REAL,
                sell_timestamp DATETIME,
                profit REAL
            )
        ''')
        
        # Bot status table (for dashboard) - one row per bot/strategy
        c.execute('''
            CREATE TABLE IF NOT EXISTS bot_status (
                strategy TEXT PRIMARY KEY,
                status TEXT,
                started_at DATETIME,
                last_heartbeat DATETIME,
                total_trades INTEGER,
                total_pnl REAL,
                wallet_balance REAL
            )
        ''')
        
        # Migration: Ensure correct schema with strategy as PRIMARY KEY
        try:
            # Check if we need to migrate (if duplicates exist or old schema)
            c.execute("PRAGMA table_info(bot_status)")
            columns = {row[1] for row in c.fetchall()}
            
            if 'wallet_balance' not in columns:
                print("[DB] Migrating: Adding wallet_balance column")
                c.execute('ALTER TABLE bot_status ADD COLUMN wallet_balance REAL DEFAULT 20000.0')
            
            # Cleanup: Remove legacy "Standalone" bot if it exists
            c.execute("DELETE FROM bot_status WHERE strategy = 'Hyper-Scalper Bot (Standalone)'")
            
            # Fix Primary Key / Duplicates issue by recreating table
            # 1. Rename old table
            c.execute("ALTER TABLE bot_status RENAME TO bot_status_old")
            
            # 2. Create new table with correct schema
            c.execute('''
                CREATE TABLE bot_status (
                    strategy TEXT PRIMARY KEY,
                    status TEXT,
                    started_at DATETIME,
                    last_heartbeat DATETIME,
                    total_trades INTEGER,
                    total_pnl REAL,
                    wallet_balance REAL
                )
            ''')
            
            # 3. Copy data (keeping only latest entry per strategy)
            c.execute('''
                INSERT INTO bot_status (strategy, status, started_at, last_heartbeat, total_trades, total_pnl, wallet_balance)
                SELECT strategy, status, started_at, last_heartbeat, total_trades, total_pnl, wallet_balance
                FROM bot_status_old
                GROUP BY strategy
            ''')
            
            # 4. Drop old table
            c.execute("DROP TABLE bot_status_old")
            print("[DB] Migration: Fixed bot_status schema and removed duplicates")
            
        except Exception as e:
            # Migration may not be needed if schema is already correct
            print(f"[DB] Migration note: {e}")
        
        conn.commit()
        conn.close()
        
        # Verify schema after creation (Issue #1 & #7 fix)
        try:
            self.verify_schema()
            print("[DB] ✅ Schema verification passed")
        except Exception as e:
            print(f"[DB] ❌ CRITICAL: Schema verification failed: {e}")
            raise

    def verify_schema(self):
        """Verify all required tables exist with correct schema (Issue #1 fix)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        required_tables = ['trades', 'positions', 'bot_status']
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in c.fetchall()]
        
        missing = set(required_tables) - set(existing_tables)
        if missing:
            conn.close()
            raise Exception(f"Missing critical tables: {missing}. Run clean_slate.py to fix.")
        
        conn.close()
        return True
    
    def log_trade(self, strategy, symbol, side, price, amount, fee=0.0, rsi=None, market_condition="", position_id=None, engine_version='2.0', strategy_version='1.0'):
        """Log a trade to the database (with versioning)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (timestamp, strategy, symbol, side, price, amount, cost, fee, rsi, market_condition, position_id, engine_version, strategy_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), strategy, symbol, side, price, amount, price*amount, fee, rsi, market_condition, position_id, engine_version, strategy_version))
        conn.commit()
        conn.close()
        print(f"[LOG] Trade logged: {side} {symbol} @ {price}")

    def open_position(self, symbol, strategy, buy_price, amount):
        """Open a new position (FIFO)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO positions (symbol, strategy, buy_price, buy_timestamp, amount, cost, status)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
        ''', (symbol, strategy, buy_price, datetime.now(), amount, buy_price * amount))
        position_id = c.lastrowid
        conn.commit()
        conn.close()
        print(f"[POSITION] Opened position #{position_id}: {amount} {symbol} @ {buy_price}")
        return position_id

    def close_position(self, position_id, sell_price):
        """Close a position (FIFO)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get position details
        c.execute('SELECT buy_price, amount, cost FROM positions WHERE id = ?', (position_id,))
        row = c.fetchone()
        buy_price, amount, cost = row
        
        # Calculate profit
        sell_value = sell_price * amount
        profit = sell_value - cost
        profit_pct = (profit / cost) * 100
        
        # Update position
        c.execute('''
            UPDATE positions 
            SET status = 'CLOSED', sell_price = ?, sell_timestamp = ?, profit = ?
            WHERE id = ?
        ''', (sell_price, datetime.now(), profit, position_id))
        
        conn.commit()
        conn.close()
        print(f"[POSITION] Closed position #{position_id}: Profit ${profit:.2f} ({profit_pct:.2f}%)")
        return profit

    def get_open_positions(self, symbol=None):
        """Get all open positions (FIFO order)"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM positions WHERE status = 'OPEN'"
        if symbol:
            query += f" AND symbol = '{symbol}'"
        query += " ORDER BY buy_timestamp ASC"  # FIFO
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_total_exposure(self, symbol=None, strategy=None):
        """Get total USD invested in a symbol or all symbols (Issue #5 fix: per-strategy)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if symbol and strategy:
            c.execute('SELECT SUM(cost) FROM positions WHERE symbol = ? AND strategy = ? AND status = "OPEN"', (symbol, strategy))
        elif symbol:
            c.execute('SELECT SUM(cost) FROM positions WHERE symbol = ? AND status = "OPEN"', (symbol,))
        elif strategy:
            c.execute('SELECT SUM(cost) FROM positions WHERE strategy = ? AND status = "OPEN"', (strategy,))
        else:
            c.execute('SELECT SUM(cost) FROM positions WHERE status = "OPEN"')
        
        result = c.fetchone()[0]
        conn.close()
        return result if result else 0.0


    def get_trades(self):
        """Fetch all trades"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
        conn.close()
        return df

    def update_bot_status(self, strategy, status, total_trades=0, total_pnl=0.0, wallet_balance=20000.0):
        """Update bot status for dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if bot exists
        c.execute('SELECT started_at FROM bot_status WHERE strategy = ?', (strategy,))
        existing = c.fetchone()
        started_at = existing[0] if existing else datetime.now()
        
        c.execute('''
            INSERT OR REPLACE INTO bot_status (strategy, status, started_at, last_heartbeat, total_trades, total_pnl, wallet_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (strategy, status, started_at, datetime.now(), total_trades, total_pnl, wallet_balance))
        conn.commit()
        conn.close()

    def get_bot_status(self, strategy=None):
        """Get current bot status for one or all bots"""
        conn = sqlite3.connect(self.db_path)
        if strategy:
            df = pd.read_sql_query("SELECT * FROM bot_status WHERE strategy = ?", conn, params=(strategy,))
        else:
            df = pd.read_sql_query("SELECT * FROM bot_status", conn)
        conn.close()
        return df if not df.empty else None

    def get_pnl_summary(self, strategy=None):
        """Calculate total P&L for a specific bot or all bots"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if strategy:
            c.execute('SELECT SUM(profit) FROM positions WHERE status = "CLOSED" AND strategy = ?', (strategy,))
        else:
            c.execute('SELECT SUM(profit) FROM positions WHERE status = "CLOSED"')
        total_pnl = c.fetchone()[0]
        conn.close()
        return total_pnl if total_pnl else 0.0
    
    def get_wallet_balance(self, strategy, initial_balance=50000.0):
        """Calculate current wallet balance for a bot"""
        # Starting balance - open positions + realized P&L
        open_exposure = self.get_total_exposure_by_strategy(strategy)
        realized_pnl = self.get_pnl_summary(strategy)
        
        # Ensure we use the higher of passed balance or default 50k
        balance_base = max(initial_balance, 50000.0)
        
        return balance_base - open_exposure + realized_pnl
    
    def get_total_exposure_by_strategy(self, strategy):
        """Get total USD invested by a specific strategy"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT SUM(cost) FROM positions WHERE strategy = ? AND status = "OPEN"', (strategy,))
        result = c.fetchone()[0]
        conn.close()
        return result if result else 0.0

