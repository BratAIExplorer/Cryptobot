"""
Bot management API endpoints
Status, control, configuration for trading bots
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import subprocess
import psutil
from datetime import datetime

from database import get_db
from models import User, BotConfig, ActivityLog
from schemas import (
    BotConfigResponse, BotConfigCreate, BotConfigUpdate,
    BotStatus, SuccessResponse
)
from auth import get_current_user

router = APIRouter(prefix="/bots", tags=["Bot Management"])

# ============================================================================
# Bot Status (Real-time from running process)
# ============================================================================

def get_bot_process() -> Optional[psutil.Process]:
    """
    Find running bot process

    Returns:
        psutil.Process if bot is running, None otherwise
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'run_bot.py' in ' '.join(cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

@router.get("/status", response_model=BotStatus)
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """
    Get real-time bot status

    Returns bot process information, uptime, and health
    """
    proc = get_bot_process()

    if not proc:
        return BotStatus(
            is_running=False,
            pid=None,
            uptime_seconds=None,
            mode="unknown",
            strategies_active=0,
            last_heartbeat=None
        )

    try:
        create_time = proc.create_time()
        uptime = int(datetime.now().timestamp() - create_time)

        # Try to detect mode from log file
        mode = "paper"  # Default
        log_path = "../../bot.log"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()
                if "mode='live'" in log_content or "mode=live" in log_content:
                    mode = "live"

        return BotStatus(
            is_running=True,
            pid=proc.pid,
            uptime_seconds=uptime,
            mode=mode,
            strategies_active=3,  # TODO: Parse from log or config
            last_heartbeat=datetime.now()
        )

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return BotStatus(
            is_running=False,
            pid=None,
            uptime_seconds=None,
            mode="unknown",
            strategies_active=0,
            last_heartbeat=None
        )

# ============================================================================
# Bot Control (Start/Stop/Restart)
# ============================================================================

@router.post("/start", response_model=SuccessResponse)
async def start_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start trading bot

    Requires user or admin role
    """
    # Check if already running
    if get_bot_process():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is already running"
        )

    try:
        # Change to bot directory
        bot_dir = os.path.abspath("../..")
        start_script = os.path.join(bot_dir, "start_bot.sh")

        if not os.path.exists(start_script):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Start script not found: {start_script}"
            )

        # Execute start script
        subprocess.Popen(
            ["/bin/bash", start_script],
            cwd=bot_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait a moment for process to start
        import time
        time.sleep(2)

        # Verify it started
        proc = get_bot_process()
        if not proc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bot failed to start"
            )

        # Log action
        log = ActivityLog(
            user_id=current_user.id,
            action="start_bot",
            resource_type="bot",
            details={"pid": proc.pid}
        )
        db.add(log)
        db.commit()

        return SuccessResponse(
            success=True,
            message=f"Bot started successfully (PID: {proc.pid})"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )

@router.post("/stop", response_model=SuccessResponse)
async def stop_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop trading bot

    Requires user or admin role
    Gracefully terminates the bot process
    """
    proc = get_bot_process()

    if not proc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is not running"
        )

    try:
        pid = proc.pid

        # Graceful termination
        proc.terminate()

        # Wait up to 10 seconds for graceful shutdown
        try:
            proc.wait(timeout=10)
        except psutil.TimeoutExpired:
            # Force kill if not responding
            proc.kill()

        # Log action
        log = ActivityLog(
            user_id=current_user.id,
            action="stop_bot",
            resource_type="bot",
            details={"pid": pid}
        )
        db.add(log)
        db.commit()

        return SuccessResponse(
            success=True,
            message=f"Bot stopped successfully (PID: {pid})"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}"
        )

@router.post("/restart", response_model=SuccessResponse)
async def restart_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restart trading bot

    Stops and starts the bot
    """
    # Stop if running
    proc = get_bot_process()
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except psutil.TimeoutExpired:
            proc.kill()

    # Start bot
    try:
        bot_dir = os.path.abspath("../..")
        start_script = os.path.join(bot_dir, "start_bot.sh")

        subprocess.Popen(
            ["/bin/bash", start_script],
            cwd=bot_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        import time
        time.sleep(2)

        new_proc = get_bot_process()
        if not new_proc:
            raise Exception("Bot failed to start after restart")

        # Log action
        log = ActivityLog(
            user_id=current_user.id,
            action="restart_bot",
            resource_type="bot",
            details={"pid": new_proc.pid}
        )
        db.add(log)
        db.commit()

        return SuccessResponse(
            success=True,
            message=f"Bot restarted successfully (PID: {new_proc.pid})"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart bot: {str(e)}"
        )

# ============================================================================
# Bot Configuration Management
# ============================================================================

@router.get("/configs", response_model=List[BotConfigResponse])
async def list_bot_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's bot configurations

    Returns all bot configs owned by current user
    Admins can see all configs
    """
    if current_user.role == "admin":
        configs = db.query(BotConfig).all()
    else:
        configs = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).all()

    return configs

@router.post("/configs", response_model=BotConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_bot_config(
    config: BotConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new bot configuration

    Allows users to define custom trading bots
    """
    db_config = BotConfig(
        user_id=current_user.id,
        bot_name=config.bot_name,
        bot_type=config.bot_type,
        config=config.config,
        is_active=False,  # Start inactive
        is_paper_mode=config.is_paper_mode
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action="create_bot_config",
        resource_type="bot_config",
        resource_id=db_config.id,
        details={"bot_name": config.bot_name, "bot_type": config.bot_type}
    )
    db.add(log)
    db.commit()

    return db_config

@router.get("/configs/{config_id}", response_model=BotConfigResponse)
async def get_bot_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot configuration by ID"""
    config = db.query(BotConfig).filter(BotConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )

    # Check authorization
    if config.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this configuration"
        )

    return config

@router.put("/configs/{config_id}", response_model=BotConfigResponse)
async def update_bot_config(
    config_id: int,
    config_update: BotConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update bot configuration"""
    config = db.query(BotConfig).filter(BotConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )

    # Check authorization
    if config.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this configuration"
        )

    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action="update_bot_config",
        resource_type="bot_config",
        resource_id=config_id,
        details={"fields_updated": list(update_data.keys())}
    )
    db.add(log)
    db.commit()

    return config

@router.delete("/configs/{config_id}", response_model=SuccessResponse)
async def delete_bot_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete bot configuration"""
    config = db.query(BotConfig).filter(BotConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot configuration not found"
        )

    # Check authorization
    if config.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this configuration"
        )

    # Don't allow deleting active configs
    if config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active bot configuration. Deactivate it first."
        )

    db.delete(config)
    db.commit()

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action="delete_bot_config",
        resource_type="bot_config",
        resource_id=config_id
    )
    db.add(log)
    db.commit()

    return SuccessResponse(
        success=True,
        message=f"Bot configuration '{config.bot_name}' deleted successfully"
    )
