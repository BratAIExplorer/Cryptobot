"""
Safety Systems for Production Trading

Critical components:
- EmergencyKillSwitch: Automatic trading halt on loss limits
- CapitalLimits: Position size and exposure limits
- PositionReconciler: Database vs Exchange validation
- SlippageProtection: Prevent excessive slippage

All systems designed for FAIL-SAFE operation.
"""

from .kill_switch import EmergencyKillSwitch
from .capital_limits import CapitalLimits, LimitViolationError
from .reconciliation import PositionReconciler, ReconciliationError
from .slippage_guard import SlippageProtection

__all__ = [
    'EmergencyKillSwitch',
    'CapitalLimits',
    'LimitViolationError',
    'PositionReconciler',
    'ReconciliationError',
    'SlippageProtection',
]
