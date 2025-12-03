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
        
        # Trades table
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
                position_id INTEGER
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
        
        # Migration: Add wallet_balance column if it doesn't exist (for existing DBs)
        try:
            c.execute('SELECT wallet_balance FROM bot_status LIMIT 1')
        except sqlite3.OperationalError:
            print("[DB] Migrating: Adding wallet_balance column to bot_status")
            c.execute('ALTER TABLE bot_status ADD COLUMN wallet_balance REAL DEFAULT 20000.0')
        
        conn.commit()
        conn.close()

    def log_trade(self, strategy, symbol, side, price, amount, fee=0.0, rsi=None, market_condition="", position_id=None):
        """Log a trade to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (timestamp, strategy, symbol, side, price, amount, cost, fee, rsi, market_condition, position_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), strategy, symbol, side, price, amount, price*amount, fee, rsi, market_condition, position_id))
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

    def get_total_exposure(self, symbol=None):
        """Get total USD invested in a symbol or all symbols"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if symbol:
            c.execute('SELECT SUM(cost) FROM positions WHERE symbol = ? AND status = "OPEN"', (symbol,))
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
    
    def get_wallet_balance(self, strategy, initial_balance=20000.0):
        """Calculate current wallet balance for a bot"""
        # Starting balance - open positions + realized P&L
        open_exposure = self.get_total_exposure_by_strategy(strategy)
        realized_pnl = self.get_pnl_summary(strategy)
        return initial_balance - open_exposure + realized_pnl
    
    def get_total_exposure_by_strategy(self, strategy):
        """Get total USD invested by a specific strategy"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT SUM(cost) FROM positions WHERE strategy = ? AND status = "OPEN"', (strategy,))
        result = c.fetchone()[0]
        conn.close()
        return result if result else 0.0

