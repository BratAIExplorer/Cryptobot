import time
import threading
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Any, Deque

logger = logging.getLogger(__name__)

class ExchangeHealthMonitor:
    """
    Advanced Health Monitor for Exchanges.
    Features:
    - Background polling
    - Moving average latency calculation
    - Circuit breaker logic (Kill Switch)
    """
    
    def __init__(self, adapter, window_size: int = 50, poll_interval: int = 60):
        self.adapter = adapter
        self.window_size = window_size
        self.poll_interval = poll_interval
        
        self.latency_history: Deque[int] = deque(maxlen=window_size)
        self.errors = 0
        self.consecutive_failures = 0
        self.is_running = False
        self.monitor_thread = None
        
        # Thresholds
        self.latency_warning_ms = 1000
        self.latency_critical_ms = 2000
        self.max_consecutive_failures = 3

    def start(self):
        """Start the monitoring thread."""
        if self.is_running:
            return
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"✅ Health Monitor started for {self.adapter.exchange_name}")

    def stop(self):
        """Stop the monitoring thread."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        while self.is_running:
            try:
                # Skip if kill switch already active via other means to avoid noise
                if self.adapter.kill_switch_active and self.consecutive_failures >= self.max_consecutive_failures:
                     time.sleep(self.poll_interval)
                     continue

                start = time.time()
                # Perform a lightweight check (e.g. fetch_time or ticker)
                # We assume adapter has a low-level check method or we use fetch_time
                if hasattr(self.adapter.exchange, 'fetch_time'):
                    self.adapter.exchange.fetch_time()
                else:
                    # Fallback check
                    self.adapter.get_current_price('BTC/USDT')

                latency = int((time.time() - start) * 1000)
                self.latency_history.append(latency)
                self.consecutive_failures = 0 # Reset on success
                
                # Check metrics
                avg_latency = sum(self.latency_history) / len(self.latency_history)
                
                if avg_latency > self.latency_critical_ms:
                    logger.error(f"🛑 {self.adapter.exchange_name} CRITICAL LATENCY: {avg_latency:.0f}ms")
                    self.adapter.trigger_kill_switch("High Latency (Rolling Avg)")
                elif avg_latency > self.latency_warning_ms:
                    logger.warning(f"⚠️ {self.adapter.exchange_name} DEGRADED: {avg_latency:.0f}ms")

            except Exception as e:
                self.consecutive_failures += 1
                logger.error(f"❌ {self.adapter.exchange_name} Health Check Failed ({self.consecutive_failures}/{self.max_consecutive_failures}): {e}")
                
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.adapter.trigger_kill_switch(f"Health Check Failure: {e}")

            time.sleep(self.poll_interval)

    def get_stats(self) -> Dict[str, Any]:
        avg_lat = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        return {
            'status': 'ONLINE' if not self.adapter.kill_switch_active else 'OFFLINE',
            'avg_latency': int(avg_lat),
            'samples': len(self.latency_history),
            'failures': self.consecutive_failures
        }
