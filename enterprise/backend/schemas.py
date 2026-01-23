"""
Pydantic schemas for request/response validation
Separate from SQLAlchemy models for clean API layer
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# Authentication Schemas
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ============================================================================
# Bot Configuration Schemas
# ============================================================================

class BotConfigBase(BaseModel):
    bot_name: str
    bot_type: str  # grid, buy_dip, sma_trend, momentum
    config: Dict[str, Any]
    is_paper_mode: bool = True
    reinvest_profits: bool = True

class BotConfigCreate(BotConfigBase):
    pass

class BotConfigUpdate(BaseModel):
    bot_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_paper_mode: Optional[bool] = None
    reinvest_profits: Optional[bool] = None

class BotConfigResponse(BotConfigBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_trade_at: Optional[datetime] = None
    reinvest_profits: bool = True

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# Bot Status Schemas (read from existing bot)
# ============================================================================

class BotStatus(BaseModel):
    """Real-time status from running bot"""
    is_running: bool
    pid: Optional[int] = None
    uptime_seconds: Optional[int] = None
    mode: str  # paper or live
    strategies_active: int
    last_heartbeat: Optional[datetime] = None

class TradeData(BaseModel):
    """Trade from bot's SQLite database"""
    id: int
    timestamp: datetime
    symbol: str
    side: str
    price: float
    amount: float
    cost: float
    fee: Optional[float] = None
    strategy: str
    pnl: Optional[float] = None

class PortfolioSummary(BaseModel):
    """Portfolio overview"""
    total_value_usd: float
    total_pnl: float
    available_balance: float
    used_balance: float
    total_trades: int
    win_rate: float
    active_positions: int
    strategies: List[Dict[str, Any]]

# ============================================================================
# Activity Log Schemas
# ============================================================================

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# Response Wrappers
# ============================================================================

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
