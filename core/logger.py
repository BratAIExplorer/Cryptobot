import pandas as pd
from datetime import datetime
import json
import os
import uuid

# Import new V3 Database models
from core.database import Database, Position, Trade, BotStatus, CircuitBreaker, SystemHealth

class TradeLogger:
    def __init__(self, db_path=None):
        # Initialize V3 Database Manager
        self.db = Database(db_path)
        self.db.init_db()  # Ensures tables exist
        self.db_path = self.db.db_path # For compatibility if accessed directly

        # Ensure Circuit Breaker row exists
        self._init_circuit_breaker()

    def _init_circuit_breaker(self):
        """Ensure the single row for circuit breaker exists"""
        session = self.db.get_session()
        try:
            cb = session.query(CircuitBreaker).filter_by(id=1).first()
            if not cb:
                new_cb = CircuitBreaker(id=1, is_open=False, consecutive_errors=0, total_trips=0)
                session.add(new_cb)
                session.commit()
        except Exception as e:
            print(f"[DB] Error init circuit breaker: {e}")
        finally:
            session.close()

    # --- TRADING METHODS ---

    def log_trade(self, strategy, symbol, side, price, amount, fee=0.0, rsi=None, market_condition="", position_id=None, engine_version='2.0', strategy_version='1.0'):
        """Log a trade execution"""
        session = self.db.get_session()
        try:
            trade = Trade(
                timestamp=datetime.utcnow(),
                strategy=strategy,
                symbol=symbol,
                side=side,
                price=price,
                amount=amount,
                cost=price * amount,
                fee=fee,
                rsi=rsi,
                market_condition=market_condition,
                position_id=position_id
            )
            session.add(trade)
            session.commit()
            print(f"[LOG] Trade logged: {side} {symbol} @ {price}")
        except Exception as e:
            print(f"[DB] Error logging trade: {e}")
            session.rollback()
        finally:
            session.close()

    def open_position(self, symbol, strategy, buy_price, amount, entry_rsi=None):
        """Open a new position"""
        session = self.db.get_session()
        new_id = str(uuid.uuid4())
        try:
            pos = Position(
                id=new_id,
                bot_id=strategy, # Mapping strategy name to bot_id for now
                strategy=strategy,
                symbol=symbol,
                entry_date=datetime.utcnow(),
                entry_price=buy_price,
                amount=amount,
                position_size_usd=buy_price * amount,
                current_price=buy_price,
                current_value_usd=buy_price * amount, # Init value
                unrealized_pnl_pct=0.0,
                unrealized_pnl_usd=0.0,
                status='OPEN',
                entry_rsi=entry_rsi
            )
            session.add(pos)
            session.commit()
            rsi_str = f" (RSI: {entry_rsi:.2f})" if entry_rsi else ""
            print(f"[POSITION] Opened position #{new_id[:8]}: {amount} {symbol} @ {buy_price}{rsi_str}")
            return new_id
        except Exception as e:
            print(f"[DB] Error opening position: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def close_position(self, position_id, sell_price, exit_rsi=None):
        """Close a position"""
        session = self.db.get_session()
        try:
            # SQLAlchemy query
            pos = session.query(Position).filter_by(id=position_id).first()
            
            if not pos:
                print(f"[SKIP] Position #{position_id} not found")
                return None
            
            if pos.status == 'CLOSED':
                print(f"[SKIP] Position #{position_id} already closed")
                return None

            # Calc profit
            cost = pos.position_size_usd
            sell_value = sell_price * pos.amount
            profit = sell_value - cost
            profit_pct = (profit / cost) * 100 if cost > 0 else 0

            # Update DB object
            pos.status = 'CLOSED'
            pos.current_price = sell_price # Final price
            pos.current_value_usd = sell_value
            pos.unrealized_pnl_usd = profit # Final PnL is "Realized" but we store in pnl column for history
            pos.unrealized_pnl_pct = profit_pct
            
            # We don't have sell_price/timestamp cols in Position model anymore as per V3 spec?
            # Creating a 'Decision' or 'Trade' usually tracks the exit. 
            # But the spec V3 Position table has `unrealized_pnl` but implies we rely on Trades for history.
            # However, for convenience, let's update the updated_at at least.
            pos.updated_at = datetime.utcnow()
            
            session.commit()
            
            rsi_str = f" (Exit RSI: {exit_rsi:.2f})" if exit_rsi else ""
            print(f"[POSITION] Closed position #{position_id[:8]}: Profit ${profit:.2f} ({profit_pct:.2f}%){rsi_str}")
            return profit
            
        except Exception as e:
            print(f"[DB] Error closing position: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_open_positions(self, symbol=None):
        """Get all open positions as DataFrame"""
        try:
            # Use pandas read_sql with the sqlalchemy engine
            query = "SELECT * FROM positions WHERE status = 'OPEN'"
            if symbol:
                query += f" AND symbol = '{symbol}'"
            query += " ORDER BY entry_date ASC" # FIFO
            
            df = pd.read_sql_query(query, self.db.engine)
            
            # Compat: Rename columns to match old interface if needed, or update consumers.
            # Old: buy_price, buy_timestamp, cost
            # New: entry_price, entry_date, position_size_usd
            # We'll map them for backward compatibility
            if not df.empty:
                df['buy_price'] = df['entry_price']
                df['buy_timestamp'] = df['entry_date']
                df['cost'] = df['position_size_usd']
                
            return df
        except Exception as e:
            print(f"[DB] Error fetching open positions: {e}")
            return pd.DataFrame()

    def get_total_exposure(self, symbol=None, strategy=None):
        """Get total USD invested"""
        session = self.db.get_session()
        try:
            query = session.query(Position).filter(Position.status == 'OPEN')
            if symbol:
                query = query.filter(Position.symbol == symbol)
            if strategy:
                query = query.filter(Position.strategy == strategy)
                
            positions = query.all()
            total = sum(p.position_size_usd for p in positions)
            return total
        except Exception as e:
            print(f"[DB] Error calculating exposure: {e}")
            return 0.0
        finally:
            session.close()
            
    def get_total_exposure_by_strategy(self, strategy):
        return self.get_total_exposure(strategy=strategy)

    def get_trades(self):
        """Fetch all trades"""
        try:
            df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", self.db.engine)
            return df
        except Exception as e:
            print(f"[DB] Error fetching trades: {e}")
            return pd.DataFrame()

    def get_pnl_summary(self, strategy=None):
        """Calculate total Realized P&L"""
        # In V3, we sum the 'unrealized_pnl_usd' of CLOSED positions? 
        # Or better, we define realized PnL as sum of profit from closed positions.
        # But wait, my V3 model removed explicit 'profit' column in favor of pnl fields.
        # I'll use the trades table or position pnl column.
        session = self.db.get_session()
        try:
            # Sum pnl of closed positions
            query = session.query(Position).filter(Position.status == 'CLOSED')
            if strategy:
                query = query.filter(Position.strategy == strategy)
            
            # Assuming unrealized_pnl_usd holds the final profit for closed positions
            closed_positions = query.all()
            total = sum((p.unrealized_pnl_usd or 0.0) for p in closed_positions)
            return total
        except Exception as e:
            print(f"[DB] Error calculating PnL: {e}")
            return 0.0
        finally:
            session.close()
            
    def get_wallet_balance(self, strategy, initial_balance=50000.0):
        # Starting balance - open exposure + realized PnL
        exposure = self.get_total_exposure_by_strategy(strategy)
        realized = self.get_pnl_summary(strategy)
        return max(initial_balance, 50000.0) - exposure + realized

    # --- BOT STATUS ---

    def update_bot_status(self, strategy, status, total_trades=0, total_pnl=0.0, wallet_balance=20000.0):
        session = self.db.get_session()
        try:
            # Check exist
            bs = session.query(BotStatus).filter_by(strategy=strategy).first()
            if not bs:
                bs = BotStatus(strategy=strategy, started_at=datetime.utcnow())
                session.add(bs)
            
            bs.status = status
            bs.last_heartbeat = datetime.utcnow()
            bs.total_trades = total_trades
            bs.total_pnl = total_pnl
            bs.wallet_balance = wallet_balance
            
            session.commit()
        except Exception as e:
            print(f"[DB] Error updating bot status: {e}")
        finally:
            session.close()

    def get_bot_status(self, strategy=None):
        try:
            query = "SELECT * FROM bot_status"
            if strategy:
                query += f" WHERE strategy = '{strategy}'"
            return pd.read_sql_query(query, self.db.engine)
        except Exception as e:
            print(f"[DB] Error fetching bot status: {e}")
            return None

    # --- CIRCUIT BREAKER ---

    def get_circuit_breaker_status(self):
        session = self.db.get_session()
        try:
            cb = session.query(CircuitBreaker).filter_by(id=1).first()
            if cb:
                return {
                    'is_open': cb.is_open,
                    'consecutive_errors': cb.consecutive_errors,
                    'last_error_time': str(cb.last_error_time) if cb.last_error_time else None,
                    'total_trips': cb.total_trips
                }
            return {'is_open': False, 'consecutive_errors': 0, 'last_error_time': None, 'total_trips': 0}
        finally:
            session.close()

    def increment_circuit_breaker_errors(self):
        session = self.db.get_session()
        try:
            cb = session.query(CircuitBreaker).filter_by(id=1).first()
            if cb:
                cb.consecutive_errors += 1
                cb.last_error_time = datetime.utcnow()
                
                if cb.consecutive_errors >= 10:
                    cb.is_open = True
                    cb.total_trips += 1
                
                session.commit()
                return cb.consecutive_errors
            return 0
        finally:
            session.close()

    def reset_circuit_breaker(self):
        session = self.db.get_session()
        try:
            cb = session.query(CircuitBreaker).filter_by(id=1).first()
            if cb:
                cb.is_open = False
                cb.consecutive_errors = 0
                cb.last_reset_time = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def check_circuit_breaker_auto_recovery(self, cooldown_minutes=30):
        status = self.get_circuit_breaker_status()
        if not status['is_open'] or not status['last_error_time']:
            return False
            
        try:
            last_error = datetime.fromisoformat(str(status['last_error_time']))
            diff = datetime.utcnow() - last_error
            if diff.total_seconds() > (cooldown_minutes * 60):
                print(f"[CIRCUIT BREAKER] Auto-recovery triggered")
                self.reset_circuit_breaker()
                return True
        except Exception as e:
            print(f"[CB] Error checking recovery: {e}")
        return False

    # --- SKIPPED TRADES ---
    # Not creating a model for SkippedTrades yet as it wasn't in V3 spec core tables list,
    # but we can implement it if needed. For now, we'll keep the method signature but print only.
    def log_skipped_trade(self, strategy, symbol, side, price, intended_amount, skip_reason, 
                          current_exposure=None, max_exposure=None, available_balance=None, details=None):
        # We could add a SkippedTrade model later
        print(f"[SKIP-LOG] {skip_reason}: {side} {symbol} @ ${price:.4f}")

    # --- SYSTEM HEALTH ---

    def update_system_health(self, component, status, message, metrics=None):
        session = self.db.get_session()
        try:
            sh = session.query(SystemHealth).filter_by(component=component).first()
            if not sh:
                sh = SystemHealth(component=component)
                session.add(sh)
            
            sh.status = status
            sh.message = message
            sh.last_updated = datetime.utcnow()
            sh.metrics_json = json.dumps(metrics) if metrics else "{}"
            session.commit()
        except Exception as e:
            print(f"[DB] Error updating health: {e}")
        finally:
            session.close()

    def get_system_health(self):
        try:
            return pd.read_sql_query("SELECT * FROM system_health", self.db.engine)
        except:
            return pd.DataFrame()

    def export_compliance_reports(self, output_dir=None):
        # Using pandas to dump tables to CSV
        if output_dir is None:
            output_dir = os.path.dirname(self.db_path)
            
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Tax Report (Closed Positions)
        try:
            df = pd.read_sql_query("SELECT * FROM positions WHERE status='CLOSED'", self.db.engine)
            tax_path = os.path.join(output_dir, f'Lumina_Tax_Report_{date_str}.csv')
            df.to_csv(tax_path, index=False)
            print(f"[Export] Tax report saved: {tax_path}")
        except Exception as e:
            print(f"[Export] Error: {e}")
            tax_path = None
            
        # 2. Audit Log (All Trades)
        try:
            df = pd.read_sql_query("SELECT * FROM trades", self.db.engine)
            audit_path = os.path.join(output_dir, f'Lumina_Audit_Log_{date_str}.csv')
            df.to_csv(audit_path, index=False)
            print(f"[Export] Audit log saved: {audit_path}")
        except Exception as e:
            print(f"[Export] Error: {e}")
            audit_path = None
            
        return tax_path, audit_path
