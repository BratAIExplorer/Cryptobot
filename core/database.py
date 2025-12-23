from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
import uuid

# Define base
Base = declarative_base()

class Position(Base):
    __tablename__ = 'positions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String(50))  # e.g., "BuyTheDip_Bot"
    symbol = Column(String(20))   # e.g., "BTC/USDT"
    entry_date = Column(DateTime, default=datetime.utcnow)
    entry_price = Column(Float)
    entry_price_expected = Column(Float, nullable=True) # For slippage tracking
    position_size_usd = Column(Float)
    amount = Column(Float) # Quantity of coin
    
    # Real-time / updated fields
    current_price = Column(Float, nullable=True)
    exit_price_expected = Column(Float, nullable=True) # For slippage tracking
    current_value_usd = Column(Float, nullable=True)
    unrealized_pnl_pct = Column(Float, nullable=True)
    unrealized_pnl_usd = Column(Float, nullable=True)
    
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, PARTIAL
    
    # Strategy specific
    strategy = Column(String(50)) # Legacy compatibility
    entry_rsi = Column(Float, nullable=True)
    exchange = Column(String(20), default="MEXC") # e.g., "MEXC", "LUNO"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alerts = relationship("Alert", back_populates="position", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="position", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="position")

class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    position_id = Column(String(36), ForeignKey('positions.id'))
    
    alert_type = Column(String(50)) # TIME_REVIEW, EMERGENCY, WARNING, OPPORTUNITY
    priority = Column(String(20))   # CRITICAL, EMERGENCY, WARNING, ROUTINE
    checkpoint_days = Column(Integer, nullable=True) # 100, 120, 150...
    
    message = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="PENDING") # PENDING, ACKNOWLEDGED, EXPIRED
    
    position = relationship("Position", back_populates="alerts")
    decisions = relationship("Decision", back_populates="alert")

class Decision(Base):
    __tablename__ = 'decisions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    position_id = Column(String(36), ForeignKey('positions.id'))
    alert_id = Column(String(36), ForeignKey('alerts.id'), nullable=True)
    
    decision_type = Column(String(50)) # SELL_100, SELL_50, HOLD, SNOOZE, DCA
    price_at_decision = Column(Float)
    rationale = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED, EXECUTED
    
    decided_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    execution_price = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("Position", back_populates="decisions")
    alert = relationship("Alert", back_populates="decisions")
    outcomes = relationship("DecisionOutcome", back_populates="decision")

class DecisionOutcome(Base):
    __tablename__ = 'decision_outcomes'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String(36), ForeignKey('decisions.id'))
    
    days_after = Column(Integer) # 7, 30, 60, 90
    price_at_check = Column(Float)
    pnl_if_held = Column(Float, nullable=True)
    pnl_if_sold = Column(Float, nullable=True)
    actual_pnl = Column(Float)
    
    outcome_quality = Column(String(20)) # EXCELLENT, GOOD, NEUTRAL, POOR, REGRET
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    decision = relationship("Decision", back_populates="outcomes")

class VetoEvent(Base):
    __tablename__ = 'veto_events'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_type = Column(String(50)) # BTC_CRASH, BAD_NEWS, FALLING_KNIFE
    severity_level = Column(Integer) # 1, 2, 3
    
    coins_affected = Column(JSON) # List of coins
    reason = Column(Text)
    
    triggered_at = Column(DateTime, default=datetime.utcnow)
    lifted_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

class Trade(Base):
    """
    Legacy compatible Trade table to store raw execution logs.
    """
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True) # Keep Integer for legacy compat
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = Column(String(50))
    symbol = Column(String(20))
    side = Column(String(10)) # BUY, SELL
    price = Column(Float)
    expected_price = Column(Float, nullable=True)
    slippage_pct = Column(Float, nullable=True)
    amount = Column(Float)
    cost = Column(Float)
    fee = Column(Float, default=0.0)
    
    rsi = Column(Float, nullable=True)
    market_condition = Column(String(50), nullable=True)
    exchange = Column(String(20), default="MEXC")
    
    position_id = Column(String(36), ForeignKey('positions.id'), nullable=True)
    
    position = relationship("Position", back_populates="trades")

class BotStatus(Base):
    __tablename__ = 'bot_status'
    
    strategy = Column(String(100), primary_key=True)
    status = Column(String(50))
    started_at = Column(DateTime)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    total_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    wallet_balance = Column(Float, default=20000.0)

class CircuitBreaker(Base):
    __tablename__ = 'circuit_breaker'
    
    id = Column(Integer, primary_key=True, default=1)
    is_open = Column(Boolean, default=False)
    consecutive_errors = Column(Integer, default=0)
    last_error_time = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    last_reset_time = Column(DateTime, nullable=True)
    total_trips = Column(Integer, default=0)

class SystemHealth(Base):
    __tablename__ = 'system_health'
    
    component = Column(String(50), primary_key=True)
    status = Column(String(20))
    message = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)
    metrics_json = Column(Text, nullable=True)

class ConfluenceScore(Base):
    __tablename__ = 'confluence_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(20))
    
    technical_score = Column(Float)
    onchain_score = Column(Float)
    macro_score = Column(Float)
    fundamental_score = Column(Float)
    exchange = Column(String(20), default="MEXC")
    
    total_score = Column(Float) # The weighted total
    raw_score = Column(Float)   # Pre-regime/scaling
    v1_score = Column(Float, nullable=True) # For calibration
    
    regime_state = Column(String(50))
    regime_multiplier = Column(Float)
    
    recommendation = Column(String(50))
    position_size = Column(String(50))
    stop_loss_pct = Column(Float)
    details = Column(Text, nullable=True) # JSON details

class MarketRegime(Base):
    __tablename__ = 'market_regimes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    regime_state = Column(String(50))
    confidence = Column(Float)
    
    btc_price = Column(Float)
    btc_ma50 = Column(Float)
    btc_ma200 = Column(Float)
    volatility_percentile = Column(Float)
    higher_highs = Column(Boolean)
    lower_lows = Column(Boolean)
    volume_trend = Column(String(20))
    recent_drawdown_pct = Column(Float)

class PortfolioSnapshot(Base):
    """Tracks account equity over time for Drawdown Velocity checks"""
    __tablename__ = 'portfolio_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    total_equity_usd = Column(Float)
    cash_balance_usd = Column(Float)
    active_positions_value_usd = Column(Float)
    unrealized_pnl_usd = Column(Float)
    
    # Track metadata
    risk_multiplier = Column(Float, default=1.0) # From current regime
    active_positions_count = Column(Integer)



# --- Database Manager ---

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
             # Default to data/trades.db in project root
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(root_dir, 'data', 'trades_v3.db') # New DB file for V3
        else:
            self.db_path = db_path
            
        # SQLite connection string
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print(f"[DB] Initialized V3 Database at {self.db_path}")

    def get_session(self):
        """Get a new session"""
        return self.Session()
