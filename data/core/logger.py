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
                market_condition TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_trade(self, strategy, symbol, side, price, amount, fee=0.0, rsi=None, market_condition=""):
        """Log a trade to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (timestamp, strategy, symbol, side, price, amount, cost, fee, rsi, market_condition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), strategy, symbol, side, price, amount, price*amount, fee, rsi, market_condition))
        conn.commit()
        conn.close()
        print(f"[LOG] Trade logged: {side} {symbol} @ {price}")

    def get_trades(self):
        """Fetch all trades"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
        conn.close()
        return df
