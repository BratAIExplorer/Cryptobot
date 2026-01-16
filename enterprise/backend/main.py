"""
CryptoBot Enterprise Platform - Main FastAPI Application

ISOLATED from main bot - runs independently on port 8000
Provides REST API for web-based bot management
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import database and models
from database import init_db, get_db, engine, Base
from models import User
from auth import get_password_hash

# Import API routers
from api import auth, users, bots, trades

# ============================================================================
# Startup/Shutdown
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    print("🚀 Starting CryptoBot Enterprise Platform...")

    # Initialize database
    print("📊 Initializing PostgreSQL database...")
    Base.metadata.create_all(bind=engine)

    # Create default admin user if not exists
    from sqlalchemy.orm import Session
    db = next(get_db())
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@cryptobot.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "change_me_immediately")

        existing_admin = db.query(User).filter(User.email == admin_email).first()

        if not existing_admin:
            admin_user = User(
                email=admin_email,
                username="admin",
                full_name="Administrator",
                hashed_password=get_password_hash(admin_password),
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Created admin user: {admin_email}")
            print(f"⚠️  IMPORTANT: Change default password immediately!")
        else:
            print(f"✅ Admin user exists: {admin_email}")

    finally:
        db.close()

    # Check bot database accessibility
    from utils.bot_reader import bot_reader
    exists, message = bot_reader.check_database_exists()
    if exists:
        print(f"✅ Bot database connected: {message}")
    else:
        print(f"⚠️  Bot database not found: {message}")
        print(f"   This is normal if the bot hasn't run yet.")

    print("✅ Enterprise Platform ready!")
    print(f"📡 API running on http://{os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}")
    print(f"📚 API docs at http://localhost:{os.getenv('API_PORT', '8000')}/docs")

    yield

    # Shutdown
    print("🛑 Shutting down Enterprise Platform...")

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="CryptoBot Enterprise Platform",
    description="""
    Web-based management platform for CryptoBot trading system.

    ## Features
    - 🔐 User authentication and authorization
    - 🤖 Bot status monitoring and control
    - 📊 Trading data and analytics
    - ⚙️ Bot configuration management
    - 📱 Mobile-responsive (designed for Next.js frontend)

    ## Isolation
    This platform runs INDEPENDENTLY from the trading bot:
    - Separate PostgreSQL database for user management
    - Read-only access to bot's SQLite trading database
    - Does NOT modify bot code or behavior
    - Can be started/stopped without affecting bot

    ## Access
    - Default admin: admin@cryptobot.local / change_me_immediately
    - Change default password immediately after first login
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS Middleware
# ============================================================================

# Get CORS origins from environment
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8501"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Global Exception Handler
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions and return JSON
    """
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("ENVIRONMENT") == "development" else None
        }
    )

# ============================================================================
# API Routes
# ============================================================================

# Health check
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "CryptoBot Enterprise Platform",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from utils.bot_reader import bot_reader

    # Check database
    db_exists, db_message = bot_reader.check_database_exists()

    return {
        "status": "healthy",
        "database": {
            "accessible": db_exists,
            "message": db_message
        },
        "api": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    }

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(bots.router, prefix="/api")
app.include_router(trades.router, prefix="/api")

# ============================================================================
# Run Server (Development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print("=" * 60)
    print("🤖 CryptoBot Enterprise Platform - Development Server")
    print("=" * 60)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Host: {host}:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info"
    )
