"""
Safety Systems for Production Trading

Critical components:
- EmergencyKillSwitch: Automatic trading halt on loss limits
- CapitalLimits: Position size and exposure limits
- PositionReconciler: Database vs Exchange validation
- SlippageProtection: Prevent excessive slippage
- SafetyConfigLoader: 100% customizable configuration system

All systems designed for FAIL-SAFE operation.

Features:
- 100% customizable via YAML config
- Exchange-specific configurations
- Mode-specific (paper/live/monitor)
- Strategy-specific overrides
- Scaling presets (micro/small/medium/large)
- Robust fallbacks
- Scalable architecture
"""

from .kill_switch import EmergencyKillSwitch
from .capital_limits import CapitalLimits, LimitViolationError
from .reconciliation import PositionReconciler, ReconciliationError
from .slippage_guard import SlippageProtection
from .config_loader import SafetyConfigLoader, get_safety_config

__all__ = [
    'EmergencyKillSwitch',
    'CapitalLimits',
    'LimitViolationError',
    'PositionReconciler',
    'ReconciliationError',
    'SlippageProtection',
    'SafetyConfigLoader',
    'get_safety_config',
]
