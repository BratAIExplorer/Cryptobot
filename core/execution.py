from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Order lifecycle states."""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class OrderExecutionResult:
    """
    Result of order placement with safety checks.
    """
    success: bool
    status: OrderStatus
    filled_amount: Decimal
    average_fill_price: Decimal
    slippage_pct: Decimal
    message: str


class OrderExecutionManager:
    """
    Ensures safe order execution with slippage protection.
    Per ACAS rules: Limit orders by default, strict slippage tolerance.
    """
    
    MAX_SLIPPAGE_PCT = Decimal("0.5")  # 0.5% maximum
    FILL_TIMEOUT_SECONDS = 120
    PARTIAL_FILL_THRESHOLD = Decimal("0.5")  # 50%
    
    def __init__(self, symbol: str, expected_price: Decimal):
        self.symbol = symbol
        self.expected_price = expected_price
        self.order_placed_at = datetime.now()
        
    def calculate_slippage(self, actual_price: Decimal) -> Decimal:
        """
        Calculate price slippage.
        """
        # Avoid division by zero
        if self.expected_price == 0:
            return Decimal("0")
            
        slippage = ((actual_price - self.expected_price) 
                    / self.expected_price * Decimal("100"))
        return abs(slippage)
    
    def validate_execution(
        self,
        filled_amount: Decimal,
        total_amount: Decimal,
        actual_price: Decimal
    ) -> OrderExecutionResult:
        """
        Validate order execution quality.
        """
        # Calculate slippage
        slippage = self.calculate_slippage(actual_price)
        
        # Check timeout
        execution_time = (datetime.now() - self.order_placed_at).total_seconds()
        is_timeout = execution_time > self.FILL_TIMEOUT_SECONDS
        
        # Calculate fill percentage
        if total_amount == 0:
             fill_pct = Decimal("0")
        else:
             fill_pct = filled_amount / total_amount
        
        # Slippage check
        if slippage > self.MAX_SLIPPAGE_PCT:
            logger.error("EXCESSIVE SLIPPAGE: %.2f%% on %s (limit: %.2f%%)",
                        slippage, self.symbol, self.MAX_SLIPPAGE_PCT)
            return OrderExecutionResult(
                success=False,
                status=OrderStatus.FAILED,
                filled_amount=Decimal("0"),
                average_fill_price=actual_price,
                slippage_pct=slippage,
                message=f"Slippage {slippage:.2f}% exceeds limit {self.MAX_SLIPPAGE_PCT}%"
            )
        
        # Timeout + partial fill handling
        if is_timeout:
            if fill_pct < self.PARTIAL_FILL_THRESHOLD:
                # Less than 50% filled after timeout → Cancel
                logger.warning("Order timeout with <50%% fill. Cancelling %s", self.symbol)
                return OrderExecutionResult(
                    success=False,
                    status=OrderStatus.CANCELLED,
                    filled_amount=filled_amount,
                    average_fill_price=actual_price,
                    slippage_pct=slippage,
                    message=f"Only {fill_pct*100:.1f}% filled after {execution_time:.0f}s"
                )
            else:
                # More than 50% filled → Let it complete
                logger.info("Order timeout but >50%% filled. Allowing completion for %s",
                           self.symbol)
                return OrderExecutionResult(
                    success=True,
                    status=OrderStatus.PARTIAL,
                    filled_amount=filled_amount,
                    average_fill_price=actual_price,
                    slippage_pct=slippage,
                    message=f"Partial fill: {fill_pct*100:.1f}%"
                )
        
        # Successful execution
        if fill_pct == Decimal("1.0"):
            return OrderExecutionResult(
                success=True,
                status=OrderStatus.FILLED,
                filled_amount=filled_amount,
                average_fill_price=actual_price,
                slippage_pct=slippage,
                message=f"Order filled successfully with {slippage:.2f}% slippage"
            )
        else:
            return OrderExecutionResult(
                success=True,
                status=OrderStatus.PARTIAL,
                filled_amount=filled_amount,
                average_fill_price=actual_price,
                slippage_pct=slippage,
                message=f"Partial fill: {fill_pct*100:.1f}%"
            )
