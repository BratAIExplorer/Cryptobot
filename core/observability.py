from datetime import datetime, timedelta
import pandas as pd
import json
import logging
from .logger import TradeLogger
from .risk_module import RiskManager
from .resilience import ExchangeResilienceManager

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Observability Engine:
    Periodically snapshots the state of all safety modules (Risk, Resilience, Circuit Breaker)
    and pushes it to the 'system_health' database table for Dashboard visibility.
    """
    
    def __init__(self, trade_logger: TradeLogger, risk_manager: RiskManager, resilience_manager: ExchangeResilienceManager):
        self.logger = trade_logger
        self.risk_manager = risk_manager
        self.resilience_manager = resilience_manager
        self.last_snapshot = datetime.min
        self.snapshot_interval_seconds = 60 # Default update rate
        
    def snapshot(self):
        """
        Capture current health state of all components.
        Should be called inside the main engine loop.
        """
        # Throttle updates
        if (datetime.now() - self.last_snapshot).seconds < self.snapshot_interval_seconds:
            return

        self.last_snapshot = datetime.now()
        
        # 1. Capture Risk Module Health
        self._snapshot_risk()
        
        # 2. Capture Resilience (Exchange) Health
        self._snapshot_resilience()
        
        # 3. Capture Circuit Breaker Health
        self._snapshot_circuit_breaker()
        
        # 4. Capture General System Status (Loop is alive)
        self.logger.update_system_health(
            component="Engine Heartbeat",
            status="HEALTHY",
            message=f"Running normally. Last update: {datetime.now().strftime('%H:%M:%S')}",
            metrics={"uptime": "N/A"} # Could add start time tracking later
        )

    def _snapshot_risk(self):
        """Check Risk Manager limits and cooldowns."""
        # Check Daily Loss
        allowed_loss, loss_msg = self.risk_manager.check_daily_loss_limit()
        
        # Check Cooldown
        allowed_cool, cool_msg = self.risk_manager.check_cooldown()
        
        status = "HEALTHY"
        messages = []
        
        if not allowed_loss:
            status = "BLOCKED"
            messages.append("Daily Loss Limit Hit")
        
        if not allowed_cool:
            if status == "HEALTHY": status = "WARNING"
            messages.append("Cooldown Active")
            
        # Get metrics
        current_loss_pct = ((self.risk_manager.daily_start_value - self.risk_manager.portfolio_value) 
                           / self.risk_manager.daily_start_value * 100) if self.risk_manager.daily_start_value > 0 else 0
        
        self.logger.update_system_health(
            component="Risk Manager",
            status=status,
            message=" | ".join(messages) if messages else "All systems nominal",
            metrics={
                "daily_loss_pct": float(current_loss_pct),
                "limit_pct": float(self.risk_manager.limits.max_daily_loss_pct),
                "consecutive_losses": self.risk_manager.consecutive_losses
            }
        )

    def _snapshot_resilience(self):
        """Check Exchange Connectivity."""
        from .resilience import ExchangeStatus
        
        health = self.resilience_manager.health
        status_map = {
            ExchangeStatus.HEALTHY: "HEALTHY",
            ExchangeStatus.DEGRADED: "WARNING",
            ExchangeStatus.STALE: "BLOCKED",
            ExchangeStatus.DISCONNECTED: "BLOCKED"
        }
        
        db_status = status_map.get(health.status, "UNKNOWN")
        
        self.logger.update_system_health(
            component="Exchange Connectivity",
            status=db_status,
            message=f"Status: {health.status.value.upper()}",
            metrics={
                "latency_ms": float(health.average_latency_ms),
                "failures": health.consecutive_failures
            }
        )

    def _snapshot_circuit_breaker(self):
        """Check Circuit Breaker state."""
        cb_status = self.logger.get_circuit_breaker_status()
        
        is_open = cb_status['is_open']
        status = "BLOCKED" if is_open else "HEALTHY"
        msg = "Circuit Open (Paused)" if is_open else "Circuit Closed (Normal)"
        
        self.logger.update_system_health(
            component="Circuit Breaker",
            status=status,
            message=msg,
            metrics={
                "trips": cb_status['total_trips'],
                "errors": cb_status['consecutive_errors']
            }
        )
