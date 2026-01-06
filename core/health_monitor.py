"""
Exchange Health Monitor
Tracks latency, uptime, and triggers kill switches automatically

This module provides comprehensive health monitoring for exchange adapters,
ensuring system stability and automatic intervention on failures.
"""
import time
import logging
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Dict, List, Optional
from .interfaces.base_adapter import BaseExchangeAdapter

logger = logging.getLogger(__name__)

class ExchangeHealthMonitor:
    """
    Monitors exchange adapter health and triggers interventions

    Features:
    - Latency tracking with rolling averages
    - Uptime monitoring
    - Auto kill-switch triggering on repeated failures
    - Health degradation alerts
    - Automatic recovery tracking
    """

    def __init__(self, adapter: BaseExchangeAdapter, notifier=None):
        """
        Initialize health monitor for an exchange adapter

        Args:
            adapter: BaseExchangeAdapter instance to monitor
            notifier: Optional TelegramNotifier for alerts
        """
        self.adapter = adapter
        self.notifier = notifier

        # Health Metrics
        self.latency_history = []
        self.max_latency_samples = 50  # Keep last 50 samples
        self.health_check_interval = 60  # Check every minute

        # Thresholds
        self.latency_threshold_warning = 1000  # 1 second (warning)
        self.latency_threshold_critical = 2000  # 2 seconds (critical)
        self.consecutive_failures_limit = 3  # Trigger kill switch after 3 failures

        # State
        self.consecutive_failures = 0
        self.last_health_check = None
        self.health_status = 'UNKNOWN'  # HEALTHY, DEGRADED, CRITICAL, OFFLINE
        self.last_alert_time = {}  # Throttle alerts

        # Statistics
        self.total_checks = 0
        self.total_failures = 0
        self.uptime_start = datetime.now()

        # Monitoring thread
        self.stop_event = Event()
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info(f"✅ Health Monitor started for {adapter.exchange_name}")

    def _monitoring_loop(self):
        """Background health monitoring loop"""
        while not self.stop_event.is_set():
            try:
                health_result = self._perform_health_check()
                self._process_health_result(health_result)
            except Exception as e:
                logger.error(f"[HealthMonitor] Check failed for {self.adapter.exchange_name}: {e}")
                self.total_failures += 1

            # Sleep until next check
            time.sleep(self.health_check_interval)

    def _perform_health_check(self) -> Dict:
        """
        Execute health check on adapter

        Returns:
            Dict with status, latency_ms, timestamp, success, error (if any)
        """
        start_time = time.time()
        self.total_checks += 1

        try:
            # Call adapter's health check method
            health_data = self.adapter.check_health()
            latency_ms = health_data.get('latency_ms', 0)

            # Record latency
            self.latency_history.append(latency_ms)
            if len(self.latency_history) > self.max_latency_samples:
                self.latency_history.pop(0)

            self.last_health_check = datetime.now()

            return {
                'status': health_data.get('status', 'UNKNOWN'),
                'latency_ms': latency_ms,
                'timestamp': datetime.now(),
                'success': True,
                'adapter_status': health_data
            }

        except Exception as e:
            logger.warning(f"[HealthMonitor] {self.adapter.exchange_name} health check failed: {e}")
            return {
                'status': 'OFFLINE',
                'latency_ms': 9999,  # High latency indicates failure
                'timestamp': datetime.now(),
                'success': False,
                'error': str(e)
            }

    def _process_health_result(self, result: Dict):
        """
        Analyze health check result and take appropriate action

        Args:
            result: Health check result dictionary
        """
        latency = result['latency_ms']
        previous_status = self.health_status

        # Determine health status
        if not result['success']:
            self.health_status = 'OFFLINE'
            self.consecutive_failures += 1
            self.total_failures += 1
        elif latency > self.latency_threshold_critical:
            self.health_status = 'CRITICAL'
            self.consecutive_failures += 1
        elif latency > self.latency_threshold_warning:
            self.health_status = 'DEGRADED'
            self.consecutive_failures = 0  # Reset on degraded (not critical)
        else:
            self.health_status = 'HEALTHY'
            self.consecutive_failures = 0

        # Take action based on health status
        if self.health_status == 'OFFLINE' or self.health_status == 'CRITICAL':
            if self.consecutive_failures >= self.consecutive_failures_limit:
                self._trigger_emergency_stop(result)
        elif self.health_status == 'DEGRADED':
            self._send_degradation_alert(result)

        # Log status changes
        if previous_status != self.health_status:
            logger.info(
                f"[HealthMonitor] {self.adapter.exchange_name} status changed: "
                f"{previous_status} → {self.health_status}"
            )

    def _trigger_emergency_stop(self, result: Dict):
        """
        Trigger kill switch on critical failure

        Args:
            result: Health check result that triggered emergency
        """
        reason = (
            f"Health check failed {self.consecutive_failures} consecutive times. "
            f"Last latency: {result['latency_ms']}ms. "
            f"Status: {result.get('status', 'UNKNOWN')}"
        )

        # Trigger kill switch on adapter
        self.adapter.trigger_kill_switch(reason)

        logger.error(f"🚨 EMERGENCY STOP: {self.adapter.exchange_name} - {reason}")

        # Send notification
        if self.notifier and self._should_send_alert('emergency'):
            try:
                self.notifier.send_message(
                    f"🚨 **KILL SWITCH ACTIVATED**\n\n"
                    f"**Exchange:** {self.adapter.exchange_name}\n"
                    f"**Reason:** {reason}\n"
                    f"**Consecutive Failures:** {self.consecutive_failures}\n"
                    f"**Action Required:** Manual intervention needed to reset kill switch\n\n"
                    f"🔧 Reset command: `adapter.reset_kill_switch()`"
                )
                self.last_alert_time['emergency'] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send emergency alert: {e}")

    def _send_degradation_alert(self, result: Dict):
        """
        Send alert on degraded performance

        Args:
            result: Health check result showing degradation
        """
        # Throttle degradation alerts (max once every 5 minutes)
        if not self._should_send_alert('degraded', cooldown_minutes=5):
            return

        if self.notifier:
            try:
                avg_latency = self.get_average_latency()
                self.notifier.send_message(
                    f"⚠️ **Performance Degradation Alert**\n\n"
                    f"**Exchange:** {self.adapter.exchange_name}\n"
                    f"**Status:** {self.health_status}\n"
                    f"**Current Latency:** {result['latency_ms']}ms\n"
                    f"**Average Latency:** {avg_latency:.0f}ms\n"
                    f"**Threshold:** {self.latency_threshold_warning}ms\n\n"
                    f"ℹ️ Monitoring continues. Kill switch will activate if critical threshold reached."
                )
                self.last_alert_time['degraded'] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send degradation alert: {e}")

    def _should_send_alert(self, alert_type: str, cooldown_minutes: int = 10) -> bool:
        """
        Check if alert should be sent (throttling)

        Args:
            alert_type: Type of alert ('emergency', 'degraded', 'recovery')
            cooldown_minutes: Minimum minutes between alerts of this type

        Returns:
            True if alert should be sent
        """
        last_alert = self.last_alert_time.get(alert_type)
        if not last_alert:
            return True

        time_since_alert = (datetime.now() - last_alert).total_seconds() / 60
        return time_since_alert >= cooldown_minutes

    def get_average_latency(self) -> float:
        """
        Calculate average latency from recent samples

        Returns:
            Average latency in milliseconds
        """
        if not self.latency_history:
            return 0.0

        return sum(self.latency_history) / len(self.latency_history)

    def get_health_metrics(self) -> Dict:
        """
        Get comprehensive health metrics

        Returns:
            Dictionary with current health status and metrics
        """
        if not self.latency_history:
            return {
                'exchange': self.adapter.exchange_name,
                'status': 'NO_DATA',
                'message': 'No health checks performed yet'
            }

        avg_latency = self.get_average_latency()
        max_latency = max(self.latency_history)
        min_latency = min(self.latency_history)

        # Calculate uptime percentage
        uptime_hours = (datetime.now() - self.uptime_start).total_seconds() / 3600
        failure_rate = (self.total_failures / self.total_checks * 100) if self.total_checks > 0 else 0
        uptime_pct = 100 - failure_rate

        return {
            'exchange': self.adapter.exchange_name,
            'status': self.health_status,
            'kill_switch_active': self.adapter.kill_switch_active,

            # Latency Metrics
            'avg_latency_ms': round(avg_latency, 2),
            'max_latency_ms': max_latency,
            'min_latency_ms': min_latency,
            'latency_samples': len(self.latency_history),

            # Reliability Metrics
            'total_checks': self.total_checks,
            'total_failures': self.total_failures,
            'consecutive_failures': self.consecutive_failures,
            'uptime_percentage': round(uptime_pct, 2),
            'uptime_hours': round(uptime_hours, 2),

            # Status
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'monitoring_active': self.monitor_thread.is_alive()
        }

    def reset_kill_switch(self):
        """
        Reset kill switch and clear failure counters
        Should only be called after manual intervention
        """
        self.adapter.reset_kill_switch()
        self.consecutive_failures = 0
        self.health_status = 'UNKNOWN'  # Will be updated on next check

        logger.info(f"✅ Kill switch reset for {self.adapter.exchange_name}")

        if self.notifier:
            self.notifier.send_message(
                f"✅ **Kill Switch Reset**\n\n"
                f"**Exchange:** {self.adapter.exchange_name}\n"
                f"**Status:** Monitoring resumed\n"
                f"**Next Check:** {self.health_check_interval} seconds"
            )

    def shutdown(self):
        """Stop monitoring and cleanup"""
        logger.info(f"🛑 Shutting down health monitor for {self.adapter.exchange_name}")

        self.stop_event.set()
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)

        # Final metrics
        metrics = self.get_health_metrics()
        logger.info(
            f"[HealthMonitor] Final metrics for {self.adapter.exchange_name}: "
            f"Uptime: {metrics['uptime_percentage']}%, "
            f"Avg Latency: {metrics['avg_latency_ms']}ms, "
            f"Total Checks: {metrics['total_checks']}"
        )

    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'stop_event'):
                self.shutdown()
        except:
            pass
