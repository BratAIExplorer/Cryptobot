"""
SQLAlchemy models for Enterprise Platform
SEPARATE database from bot - PostgreSQL for user/config management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User accounts for web platform"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    # Role-based access control
    role = Column(String, default="user")  # admin, user, viewer

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    bots = relationship("BotConfig", back_populates="owner")
    sessions = relationship("UserSession", back_populates="user")
    activity = relationship("ActivityLog", back_populates="user")

class BotConfig(Base):
    """Bot configurations managed by users"""
    __tablename__ = "bot_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Bot identification
    bot_name = Column(String, nullable=False)
    bot_type = Column(String, nullable=False)  # grid, buy_dip, sma_trend, momentum

    # Configuration (JSON storage for flexibility)
    config = Column(JSON, nullable=False)
    # Example: {"symbol": "BTC/USDT", "budget": 250, "trade_size": 25, ...}

    # Status
    is_active = Column(Boolean, default=False)
    is_paper_mode = Column(Boolean, default=True)
    reinvest_profits = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_trade_at = Column(DateTime(timezone=True))

    # Relationships
    owner = relationship("User", back_populates="bots")

class UserSession(Base):
    """Track user login sessions"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session details
    token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")

class ActivityLog(Base):
    """Audit log for user actions"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Activity details
    action = Column(String, nullable=False)  # login, create_bot, start_bot, stop_bot, etc.
    resource_type = Column(String)  # user, bot, trade
    resource_id = Column(Integer)

    # Context
    details = Column(JSON)  # Additional context as JSON
    ip_address = Column(String)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="activity")
