import sqlite3
import pandas as pd
from datetime import datetime
import os

class TradeLogger:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use absolute path to prevent split-brain issues
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(root_dir, 'data', 'trades.db')
            
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
        
        # Positions table (FIFO tracking with RSI analytics)
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
                profit REAL,
                entry_rsi REAL,
                exit_rsi REAL
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
        
        # Circuit Breaker table (persistent state)
        c.execute('''
            CREATE TABLE IF NOT EXISTS circuit_breaker (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_open BOOLEAN DEFAULT 0,
                consecutive_errors INTEGER DEFAULT 0,
                last_error_time DATETIME,
                last_reset_time DATETIME,
                total_trips INTEGER DEFAULT 0
            )
        ''')
        
        # Initialize circuit breaker if not exists
        # Initialize circuit breaker if not exists
        c.execute('INSERT OR IGNORE INTO circuit_breaker (id, is_open, consecutive_errors, total_trips) VALUES (1, 0, 0, 0)')
        
        # System Health table (Observability)
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_health (
                component TEXT PRIMARY KEY,
                status TEXT,
                message TEXT,
                last_updated DATETIME,
                metrics_json TEXT
            )
        ''')
        
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
        
        required_tables = ['trades', 'positions', 'bot_status', 'circuit_breaker', 'system_health']
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

    def open_position(self, symbol, strategy, buy_price, amount, entry_rsi=None):
        """Open a new position (FIFO) with optional entry RSI tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO positions (symbol, strategy, buy_price, buy_timestamp, amount, cost, status, entry_rsi)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?)
        ''', (symbol, strategy, buy_price, datetime.now(), amount, buy_price * amount, entry_rsi))
        position_id = c.lastrowid
        conn.commit()
        conn.close()
        rsi_str = f" (RSI: {entry_rsi:.2f})" if entry_rsi else ""
        print(f"[POSITION] Opened position #{position_id}: {amount} {symbol} @ {buy_price}{rsi_str}")
        return position_id

    def close_position(self, position_id, sell_price, exit_rsi=None):
        """Close a position (FIFO) with optional exit RSI tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get position details
        c.execute('SELECT buy_price, amount, cost FROM positions WHERE id = ?', (position_id,))
        row = c.fetchone()
        
        # Safety check: Handle case where position doesn't exist or already closed
        if not row:
            conn.close()
            print(f"[SKIP] Position #{position_id} already closed or not in database")
            return None
        
        buy_price, amount, cost = row
        
        # Calculate profit
        sell_value = sell_price * amount
        profit = sell_value - cost
        profit_pct = (profit / cost) * 100
        
        # Update position
        c.execute('''
            UPDATE positions 
            SET status = 'CLOSED', sell_price = ?, sell_timestamp = ?, profit = ?, exit_rsi = ?
            WHERE id = ?
        ''', (sell_price, datetime.now(), profit, exit_rsi, position_id))
        
        conn.commit()
        conn.close()
        rsi_str = f" (Exit RSI: {exit_rsi:.2f})" if exit_rsi else ""
        print(f"[POSITION] Closed position #{position_id}: Profit ${profit:.2f} ({profit_pct:.2f}%){rsi_str}")
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
    
    # ==================== CIRCUIT BREAKER METHODS ====================
    
    def get_circuit_breaker_status(self):
        """Get current circuit breaker state from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT is_open, consecutive_errors, last_error_time, total_trips FROM circuit_breaker WHERE id = 1')
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'is_open': bool(row[0]),
                'consecutive_errors': row[1],
                'last_error_time': row[2],
                'total_trips': row[3]
            }
        return {'is_open': False, 'consecutive_errors': 0, 'last_error_time': None, 'total_trips': 0}
    
    def increment_circuit_breaker_errors(self):
        """Increment error counter and potentially open circuit breaker"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE circuit_breaker 
            SET consecutive_errors = consecutive_errors + 1,
                last_error_time = ?
            WHERE id = 1
        ''', (datetime.now(),))
        
        # Check if threshold exceeded (10 errors)
        c.execute('SELECT consecutive_errors FROM circuit_breaker WHERE id = 1')
        errors = c.fetchone()[0]
        
        if errors >= 10:
            c.execute('''
                UPDATE circuit_breaker 
                SET is_open = 1,
                    total_trips = total_trips + 1
                WHERE id = 1
            ''')
        
        conn.commit()
        conn.close()
        return errors
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker after successful trade or cooldown"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE circuit_breaker 
            SET is_open = 0,
                consecutive_errors = 0,
                last_reset_time = ?
            WHERE id = 1
        ''', (datetime.now(),))
        conn.commit()
        conn.close()
    
    def check_circuit_breaker_auto_recovery(self, cooldown_minutes=30):
        """Check if circuit breaker should auto-recover after cooldown period"""
        status = self.get_circuit_breaker_status()
        
        if not status['is_open']:
            return False  # Already closed
        
        if not status['last_error_time']:
            return False  # No error time recorded
        
        # Parse last error time
        try:
            from datetime import datetime, timedelta
            last_error = datetime.fromisoformat(status['last_error_time'])
            cooldown_elapsed = datetime.now() - last_error
            
            if cooldown_elapsed > timedelta(minutes=cooldown_minutes):
                print(f"[CIRCUIT BREAKER] Auto-recovery: {cooldown_minutes}min cooldown elapsed")
                self.reset_circuit_breaker()
                return True
        except:
            pass
        
        return False
    
    # ==================== SKIPPED TRADES LOGGING ====================
    
    def log_skipped_trade(self, strategy, symbol, side, price, intended_amount, skip_reason, 
                          current_exposure=None, max_exposure=None, available_balance=None, details=None):
        """Log a trade that was skipped due to limits or insufficient funds"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if table exists (for backwards compatibility)
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skipped_trades'")
        if not c.fetchone():
            conn.close()
            return  # Table doesn't exist, skip logging quietly
        
        c.execute('''
            INSERT INTO skipped_trades 
            (timestamp, strategy, symbol, side, price, intended_amount, skip_reason, details, 
             current_exposure, max_exposure, available_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), strategy, symbol, side, price, intended_amount, skip_reason, 
              details, current_exposure, max_exposure, available_balance))
        
        conn.commit()
        conn.close()
        print(f"[SKIP-LOG] {skip_reason}: {side} {symbol} @ ${price:.4f}")


    # ==================== OBSERVABILITY METHODS ====================

    def update_system_health(self, component, status, message, metrics=None):
        """Update health status for a system component"""
        import json
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        metrics_json = json.dumps(metrics) if metrics else "{}"
        
        c.execute('''
            INSERT OR REPLACE INTO system_health (component, status, message, last_updated, metrics_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (component, status, message, datetime.now(), metrics_json))
        
        conn.commit()
        conn.close()

    def get_system_health(self):
        """Get latest health status for all components"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM system_health", conn)
        conn.close()
        return df

    def export_compliance_reports(self, output_dir=None):
        """
        Generate compliance reports (Tax & Audit)
        Returns: Tuple of (tax_report_path, audit_log_path)
        """
        if output_dir is None:
            output_dir = os.path.dirname(self.db_path)
            
        date_str = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        
        # 1. Tax Report (Closed Positions with PnL)
        try:
            positions_df = pd.read_sql_query('''
                SELECT id, symbol, strategy, buy_timestamp, buy_price, 
                       sell_timestamp, sell_price, amount, cost, profit, status 
                FROM positions 
                WHERE status = 'CLOSED'
            ''', conn)
            
            tax_path = os.path.join(output_dir, f'Lumina_Tax_Report_{date_str}.csv')
            positions_df.to_csv(tax_path, index=False)
            print(f"[Export] Tax report saved: {tax_path}")
        except Exception as e:
            print(f"[Export] Error generating tax report: {e}")
            tax_path = None

        # 2. Audit Log (All Raw Trades)
        try:
            trades_df = pd.read_sql_query("SELECT * FROM trades", conn)
            audit_path = os.path.join(output_dir, f'Lumina_Audit_Log_{date_str}.csv')
            trades_df.to_csv(audit_path, index=False)
            print(f"[Export] Audit log saved: {audit_path}")
        except Exception as e:
            print(f"[Export] Error generating audit log: {e}")
            audit_path = None
            
        conn.close()
        return tax_path, audit_path

