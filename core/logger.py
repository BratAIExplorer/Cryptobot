import pandas as pd
from datetime import datetime
import json
import os
import uuid

# Import new V3 Database models
from core.database import Database, Position, Trade, BotStatus, CircuitBreaker, SystemHealth, Decision, ConfluenceScore, PortfolioSnapshot

class TradeLogger:
    def __init__(self, db_path=None, mode='paper'):
        """
        Initialize TradeLogger with database connection.
        Args:
            db_path: Explicit path to DB file (optional)
            mode: 'live' or 'paper' to determine default DB filename
        """
        # Determine DB based on mode if path not explicit
        if db_path is None:
            db_filename = 'trades_v3_live.db' if mode == 'live' else 'trades_v3_paper.db'
            # We let the Database class construct the full path, but we need to pass the filename differently or path.
            # Database class assumes full path or constructs 'trades_v3.db'.
            # Let's construct full path here to be explicit.
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(root_dir, 'data', db_filename)

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

    def log_trade(self, strategy, symbol, side, price, amount, expected_price=None, fee=0.0, rsi=None, market_condition="", position_id=None, exchange='MEXC', engine_version='2.0', strategy_version='1.0'):
        """Log a trade execution"""
        session = self.db.get_session()
        try:
            slippage_pct = 0.0
            if expected_price and expected_price > 0:
                slippage_pct = ((price - expected_price) / expected_price) * 100
                if side == 'SELL':
                    slippage_pct = -slippage_pct # Positive = Good for SELL

            trade = Trade(
                timestamp=datetime.utcnow(),
                strategy=strategy,
                symbol=symbol,
                side=side,
                price=price,
                expected_price=expected_price,
                slippage_pct=slippage_pct,
                amount=amount,
                cost=price * amount,
                fee=fee,
                rsi=rsi,
                market_condition=market_condition,
                position_id=position_id,
                exchange=exchange
            )
            session.add(trade)
            session.commit()
            slip_str = f" (Slippage: {slippage_pct:.3f}%)" if expected_price else ""
            print(f"[LOG] Trade logged: {side} {symbol} @ {price}{slip_str}")
        except Exception as e:
            print(f"[DB] Error logging trade: {e}")
            session.rollback()
        finally:
            session.close()

    def open_position(self, symbol, strategy, buy_price, amount, expected_price=None, entry_rsi=None, exchange='MEXC'):
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
                entry_price_expected=expected_price,
                amount=amount,
                position_size_usd=buy_price * amount,
                current_price=buy_price,
                current_value_usd=buy_price * amount, # Init value
                unrealized_pnl_pct=0.0,
                unrealized_pnl_usd=0.0,
                status='OPEN',
                entry_rsi=entry_rsi,
                exchange=exchange
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

    def close_position(self, position_id, sell_price, expected_price=None, exit_rsi=None):
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
            
            # Update expected price for slippage
            pos.exit_price_expected = expected_price

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
        return initial_balance - exposure + realized

    # --- DECISION MAKING (HUMAN IN LOOP) ---
    def create_decision(self, position_id, decision_type, rationale, price):
        session = self.db.get_session()
        try:
            # Check if pending exists
            existing = session.query(Decision).filter_by(position_id=position_id, status='PENDING').first()
            if existing: return
            
            new_decision = Decision(
                position_id=position_id,
                decision_type=decision_type,
                rationale=rationale,
                price_at_decision=price,
                status='PENDING'
            )
            session.add(new_decision)
            session.commit()
        except Exception as e:
            print(f"[DB] Error creating decision: {e}")
        finally:
            session.close()

    def get_pending_decision(self, position_id):
        session = self.db.get_session()
        try:
            return session.query(Decision).filter_by(position_id=position_id, status='PENDING').first()
        except:
            return None
        finally:
            session.close()

    def update_decision_status(self, decision_id, new_status):
        session = self.db.get_session()
        try:
            d = session.query(Decision).filter_by(id=decision_id).first()
            if d:
                d.status = new_status
                d.executed_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            print(f"[DB] Error updating decision: {e}")
        finally:
            session.close()

    # --- END CLASS ---

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

    # --- CONFLUENCE V2 & REGIME METHODS ---

    def log_market_regime(self, state, confidence, metrics):
        """Log regime detection results"""
        session = self.db.get_session()
        try:
            regime = MarketRegime(
                timestamp=datetime.utcnow(),
                regime_state=str(state),
                confidence=confidence,
                btc_price=metrics.get('btc_price', 0),
                btc_ma50=metrics.get('btc_ma50', 0),
                btc_ma200=metrics.get('btc_ma200', 0),
                volatility_percentile=metrics.get('volatility_percentile', 0),
                higher_highs=metrics.get('higher_highs', False),
                lower_lows=metrics.get('lower_lows', False),
                volume_trend=metrics.get('volume_trend', 'UNKNOWN'),
                recent_drawdown_pct=metrics.get('recent_drawdown_pct', 0)
            )
            session.add(regime)
            session.commit()
        except Exception as e:
            print(f"[DB] Error logging regime: {e}")
            session.rollback()
        finally:
            session.close()

    def log_confluence_score(self, result: dict):
        """Log full confluence score result"""
        session = self.db.get_session()
        try:
            from core.database import ConfluenceScore
            scores = result.get('scores', {})
            regime = result.get('regime', {})
            rec = result.get('recommendation', {})
            
            # Extract values from nested dictionaries if necessary
            def get_score(val):
                if isinstance(val, dict): return val.get('score', 0)
                return val if val is not None else 0

            score_entry = ConfluenceScore(
                timestamp=datetime.utcnow(),
                symbol=result.get('symbol'),
                technical_score=float(get_score(scores.get('technical', 0))),
                onchain_score=float(get_score(scores.get('onchain', 0))),
                macro_score=float(get_score(scores.get('macro', 0))),
                fundamental_score=float(get_score(scores.get('fundamental', 0))),
                total_score=float(scores.get('final_total', 0)),
                raw_score=float(scores.get('raw_total', 0)),
                v1_score=float(scores.get('v1_total', 0)),
                regime_state=regime.get('state', 'UNKNOWN'),
                regime_multiplier=float(regime.get('multiplier', 1.0)),
                recommendation=rec.get('rating', 'UNKNOWN'),
                position_size=rec.get('position_size', 'NONE'),
                stop_loss_pct=float(rec.get('stop_loss_pct', 0)),
                details=json.dumps(result),
                exchange=result.get('exchange', 'MEXC')
            )
            session.add(score_entry)
            session.commit()
        except Exception as e:
            print(f"[DB] Error logging confluence: {e}")
            session.rollback()
        finally:
            session.close()

    def log_portfolio_snapshot(self, equity: float, cash: float, pos_value: float, unrealized_pnl: float, risk_mult: float = 1.0, pos_count: int = 0):
        """Record portfolio status for drawdown velocity tracking"""
        session = self.db.get_session()
        try:
            snap = PortfolioSnapshot(
                timestamp=datetime.utcnow(),
                total_equity_usd=equity,
                cash_balance_usd=cash,
                active_positions_value_usd=pos_value,
                unrealized_pnl_usd=unrealized_pnl,
                risk_multiplier=risk_mult,
                active_positions_count=pos_count
            )
            session.add(snap)
            session.commit()
        except Exception as e:
            print(f"[DB] Error logging portfolio snapshot: {e}")
            session.rollback()
        finally:
            session.close()

    def get_latest_confluence_scores(self, symbol=None, limit=10):
        """Get latest confluence scores for V2 monitoring"""
        session = self.db.get_session()
        try:
            from core.database import ConfluenceScore
            query = session.query(ConfluenceScore)
            if symbol:
                query = query.filter(ConfluenceScore.symbol == symbol)
            query = query.order_by(ConfluenceScore.timestamp.desc()).limit(limit)
            return pd.read_sql(query.statement, session.bind)
        except Exception as e:
            print(f"[DB] Error fetching confluence scores: {e}")
            return pd.DataFrame()
        finally:
            session.close()

    def get_recent_market_regimes(self, limit=24):
        """Get recent market regime history"""
        session = self.db.get_session()
        try:
            from core.database import MarketRegime
            query = session.query(MarketRegime).order_by(MarketRegime.timestamp.desc()).limit(limit)
            df = pd.read_sql(query.statement, session.bind)
            
            if not df.empty and 'regime_state' in df.columns:
                df = df.rename(columns={'regime_state': 'regime'})
                multipliers = {
                    'BULL_CONFIRMED': 1.25, 'TRANSITION_BULLISH': 0.60, 
                    'UNDEFINED': 0.20, 'TRANSITION_BEARISH': 0.25, 
                    'BEAR_CONFIRMED': 0.0, 'CRISIS': 0.0
                }
                df['risk_multiplier'] = df['regime'].apply(lambda x: multipliers.get(x, 0.2))
            return df
        except Exception as e:
            print(f"[DB] Error fetching market regimes: {e}")
            return pd.DataFrame()
        finally:
            session.close()
