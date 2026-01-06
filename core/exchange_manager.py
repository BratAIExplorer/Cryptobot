import logging
from typing import Dict, Any, Optional, List
from .exchanges.exchange_factory import ExchangeFactory
from .interfaces.base_adapter import BaseExchangeAdapter

logger = logging.getLogger(__name__)

class ExchangeManager:
    """
    Manager for multiple exchange adapters.
    Responsibilities:
    - Lifecycle Management (Init, Start Monitors, Shutdown)
    - Registry (Store/Retrieve Adapters)
    - Health Aggregation (Global System Status)
    """
    
    def __init__(self, mode: str = 'paper', enabled_exchanges: List[str] = None):
        self.mode = mode
        self.adapters: Dict[str, BaseExchangeAdapter] = {}
        self.enabled_exchanges = enabled_exchanges or ['BINANCE'] # Default
        
        self._initialize_adapters()

    def _initialize_adapters(self):
        """Initialize all enabled adapters using the Factory."""
        for name in self.enabled_exchanges:
            try:
                logger.info(f"🔌 Initializing {name} adapter...")
                adapter = ExchangeFactory.create_adapter(name, self.mode)
                
                # Check if creation returned None (not implemented)
                if adapter is None:
                    logger.warning(f"⚠️  Adapter for {name} returned None. Skipping.")
                    continue
                    
                self.adapters[name.upper()] = adapter
                
                # Auto-start health monitor if available
                # (BaseExchangeAdapter now does this in init, but we ensure consistent Start here if needed)
                if hasattr(adapter, 'health_monitor'):
                    if not adapter.health_monitor.is_running:
                        adapter.health_monitor.start()

                logger.info(f"✅ {name} Adapter Ready")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")

    def get_adapter(self, exchange_name: str) -> Optional[BaseExchangeAdapter]:
        """Retrieve an initialized adapter by name."""
        return self.adapters.get(exchange_name.upper())

    def get_all_adapters(self) -> List[BaseExchangeAdapter]:
        return list(self.adapters.values())

    def check_global_health(self) -> Dict[str, Any]:
        """
        Aggregate health status of all exchanges.
        Returns: { 'status': 'ONLINE'|'PARTIAL'|'OFFLINE', 'details': {...} }
        """
        status_map = {}
        total = len(self.adapters)
        online = 0
        critical = 0
        
        for name, adapter in self.adapters.items():
            health = adapter.check_health()
            status_map[name] = health
            
            if health.get('status') == 'ONLINE':
                online += 1
            elif health.get('status') == 'CRITICAL' or health.get('status') == 'OFFLINE':
                critical += 1
        
        if total == 0:
            global_status = 'OFFLINE'
        elif critical == total:
            global_status = 'OFFLINE' # All down
        elif critical > 0:
            global_status = 'PARTIAL_OUTAGE'
        else:
            global_status = 'ONLINE'
            
        return {
            'status': global_status,
            'summary': f"{online}/{total} Online",
            'details': status_map
        }

    def shutdown(self):
        """Gracefully shutdown all adapters."""
        logger.info("🛑 Shutting down Exchange Manager...")
        for name, adapter in self.adapters.items():
            try:
                adapter.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")
