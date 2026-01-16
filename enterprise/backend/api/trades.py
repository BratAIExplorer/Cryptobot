"""
Trading data API endpoints
Read-only access to bot's trading database
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from models import User
from schemas import TradeData, PortfolioSummary, SuccessResponse
from auth import get_current_user
from utils.bot_reader import bot_reader

router = APIRouter(prefix="/trades", tags=["Trading Data"])

# ============================================================================
# Database Health Check
# ============================================================================

@router.get("/health", response_model=SuccessResponse)
async def check_database_health(current_user: User = Depends(get_current_user)):
    """
    Check if bot database is accessible

    Returns status and trade count
    """
    exists, message = bot_reader.check_database_exists()

    if not exists:
        raise HTTPException(
            status_code=503,
            detail=f"Bot database not accessible: {message}"
        )

    return SuccessResponse(
        success=True,
        message=message
    )

# ============================================================================
# Trade History
# ============================================================================

@router.get("/", response_model=List[TradeData])
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get trade history

    - **limit**: Number of trades to return (1-1000, default 100)
    - **offset**: Number of trades to skip (pagination)
    - **strategy**: Filter by strategy name
    - **symbol**: Filter by trading pair
    - **start_date**: Filter by start date (ISO format)
    - **end_date**: Filter by end date (ISO format)
    """
    try:
        trades = bot_reader.get_trades(
            limit=limit,
            offset=offset,
            strategy=strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        return [
            TradeData(
                id=t['id'],
                timestamp=datetime.fromisoformat(t['timestamp']),
                symbol=t['symbol'],
                side=t['side'],
                price=float(t['price']),
                amount=float(t['amount']),
                cost=float(t['cost']),
                fee=float(t['fee']) if t.get('fee') else None,
                strategy=t['strategy'],
                pnl=float(t['pnl']) if t.get('pnl') else None
            )
            for t in trades
        ]

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Bot database not found. Make sure the bot has executed at least one trade."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading trades: {str(e)}"
        )

@router.get("/count")
async def get_trade_count(
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get total trade count

    - **strategy**: Filter by strategy name
    - **symbol**: Filter by trading pair
    """
    try:
        count = bot_reader.get_trade_count(strategy=strategy, symbol=symbol)
        return {"count": count}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error counting trades: {str(e)}"
        )

@router.get("/recent", response_model=List[TradeData])
async def get_recent_trades(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user)
):
    """
    Get trades from last N hours

    - **hours**: Number of hours to look back (1-168, default 24)
    """
    try:
        trades = bot_reader.get_recent_trades(hours=hours)

        return [
            TradeData(
                id=t['id'],
                timestamp=datetime.fromisoformat(t['timestamp']),
                symbol=t['symbol'],
                side=t['side'],
                price=float(t['price']),
                amount=float(t['amount']),
                cost=float(t['cost']),
                fee=float(t['fee']) if t.get('fee') else None,
                strategy=t['strategy'],
                pnl=float(t['pnl']) if t.get('pnl') else None
            )
            for t in trades
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading recent trades: {str(e)}"
        )

# ============================================================================
# Portfolio Analytics
# ============================================================================

@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio_summary(current_user: User = Depends(get_current_user)):
    """
    Get portfolio summary

    Returns total P&L, trade count, win rate, and strategy breakdown
    """
    try:
        summary = bot_reader.get_portfolio_summary()

        return PortfolioSummary(
            total_value_usd=0.0,  # TODO: Calculate from balance
            total_pnl=summary['total_pnl'],
            total_trades=summary['total_trades'],
            win_rate=summary['win_rate'],
            active_positions=summary['active_positions'],
            strategies=summary['strategies']
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating portfolio summary: {str(e)}"
        )

@router.get("/performance")
async def get_strategy_performance(current_user: User = Depends(get_current_user)):
    """
    Get performance metrics per strategy

    Returns detailed breakdown of each strategy's performance
    """
    try:
        performance = bot_reader.get_strategy_performance()
        return {"strategies": performance}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating strategy performance: {str(e)}"
        )
