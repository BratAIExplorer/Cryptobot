"""
Database configuration for Enterprise Platform
ISOLATED from main bot - uses separate PostgreSQL database
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Default to SQLite for zero-config portability (change to PostgreSQL in production if needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./enterprise.db")

# Create engine 
# NOTE: check_same_thread=False is required for SQLite in FastAPI
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI routes
    Provides database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables
    Called on application startup
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Enterprise database initialized")
