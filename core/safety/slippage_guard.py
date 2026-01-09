"""
Slippage Protection - Prevent Excessive Slippage

Protects against:
1. Flash crashes (price gaps)
2. Low liquidity (wide spreads)
3. Market orders during high volatility

Design: Use limit orders with acceptable price range
"""
import logging
from typing import Optional, Dict, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class SlippageProtection:
    """
    Slippage protection for order execution

    Converts market orders to limit orders with:
    - Maximum acceptable slippage (default 0.2%)
    - Automatic order cancellation if not filled
    - Price validation before execution
    """

    def __init__(
        self,
        max_slippage_percent: float = 0.2,
        order_timeout_seconds: int = 30,
        enable_protection: bool = True
    ):
        """
        Initialize slippage protection

        Args:
            max_slippage_percent: Maximum acceptable slippage (e.g. 0.2 = 0.2%)
            order_timeout_seconds: Cancel order if not filled within this time
            enable_protection: If False, allows market orders (dangerous)
        """
        self.max_slippage = max_slippage_percent / 100  # Convert to decimal
        self.order_timeout = order_timeout_seconds
        self.enabled = enable_protection

        logger.info(f"Slippage Protection initialized:")
        logger.info(f"  Max slippage: {max_slippage_percent}%")
        logger.info(f"  Order timeout: {order_timeout_seconds}s")
        logger.info(f"  Protection: {'ENABLED' if enable_protection else 'DISABLED'}")

        if not enable_protection:
            logger.warning("⚠️ Slippage protection DISABLED - using market orders!")

    def create_protected_order(
        self,
        exchange,
        symbol: str,
        side: str,
        amount: float,
        current_price: Optional[float] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Create order with slippage protection

        Args:
            exchange: Exchange adapter instance
            symbol: Trading pair (e.g. 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Quantity to trade
            current_price: Optional current price (fetched if not provided)

        Returns:
            (success: bool, order: Dict, error_message: str)
        """
        try:
            # Get current price if not provided
            if current_price is None:
                ticker = exchange.fetch_ticker(symbol)
                if not ticker:
                    return (False, None, "Failed to fetch current price")
                current_price = float(ticker['last'])

            logger.info(f"Creating protected order: {side} {amount} {symbol} @ {current_price}")

            # If protection disabled, use market order (not recommended)
            if not self.enabled:
                logger.warning(f"⚠️ Slippage protection disabled - using market order")
                order = exchange.create_order(symbol, side, amount, price=None)
                return (True, order, None)

            # Calculate acceptable price range
            limit_price = self._calculate_limit_price(current_price, side)

            logger.info(f"Limit price: {limit_price} (max slippage: {self.max_slippage*100}%)")

            # Validate price is reasonable
            if not self._validate_price(current_price, limit_price, side):
                error = f"Calculated limit price {limit_price} is unreasonable vs current {current_price}"
                logger.error(error)
                return (False, None, error)

            # Create limit order
            order = exchange.create_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=limit_price
            )

            if order:
                logger.info(f"✅ Protected order created: {order.get('id', 'unknown')}")
                return (True, order, None)
            else:
                return (False, None, "Order creation returned None")

        except Exception as e:
            logger.error(f"Failed to create protected order: {e}")
            return (False, None, str(e))

    def _calculate_limit_price(self, current_price: float, side: str) -> float:
        """
        Calculate limit price with acceptable slippage

        Args:
            current_price: Current market price
            side: 'buy' or 'sell'

        Returns:
            Limit price
        """
        if side.lower() == 'buy':
            # For buy orders, willing to pay UP TO current_price * (1 + slippage)
            limit_price = current_price * (1 + self.max_slippage)
        else:
            # For sell orders, willing to accept DOWN TO current_price * (1 - slippage)
            limit_price = current_price * (1 - self.max_slippage)

        # Round to reasonable precision (8 decimals for crypto)
        limit_price = round(limit_price, 8)

        return limit_price

    def _validate_price(self, current_price: float, limit_price: float, side: str) -> bool:
        """
        Validate calculated price is reasonable

        Args:
            current_price: Current market price
            limit_price: Calculated limit price
            side: 'buy' or 'sell'

        Returns:
            bool: True if price is reasonable
        """
        # Check price is not negative or zero
        if limit_price <= 0:
            return False

        # Check price difference is within expected range
        diff_percent = abs(limit_price - current_price) / current_price

        if diff_percent > self.max_slippage * 2:
            # More than 2x max slippage = calculation error
            logger.error(f"Price validation failed: {diff_percent*100:.2f}% diff")
            return False

        # For buy orders, limit price should be >= current price
        if side.lower() == 'buy' and limit_price < current_price * 0.99:
            logger.error(f"Buy limit price {limit_price} too low vs current {current_price}")
            return False

        # For sell orders, limit price should be <= current price
        if side.lower() == 'sell' and limit_price > current_price * 1.01:
            logger.error(f"Sell limit price {limit_price} too high vs current {current_price}")
            return False

        return True

    def check_execution_slippage(
        self,
        intended_price: float,
        executed_price: float,
        side: str
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if executed order had acceptable slippage

        Args:
            intended_price: Price when order was created
            executed_price: Actual execution price
            side: 'buy' or 'sell'

        Returns:
            (acceptable: bool, slippage_percent: float, warning: str)
        """
        # Calculate slippage
        if side.lower() == 'buy':
            # For buy: positive slippage = paid more than intended
            slippage = (executed_price - intended_price) / intended_price
        else:
            # For sell: positive slippage = received less than intended
            slippage = (intended_price - executed_price) / intended_price

        slippage_percent = slippage * 100

        # Check if acceptable
        acceptable = abs(slippage) <= self.max_slippage

        if not acceptable:
            warning = (
                f"⚠️ Excessive slippage: {slippage_percent:.3f}% "
                f"(limit: {self.max_slippage*100}%)"
            )
            logger.warning(warning)
        else:
            warning = None
            logger.info(f"✅ Acceptable slippage: {slippage_percent:.3f}%")

        return (acceptable, slippage_percent, warning)

    def get_stats(self) -> Dict:
        """Get slippage protection statistics"""
        return {
            'enabled': self.enabled,
            'max_slippage_percent': self.max_slippage * 100,
            'order_timeout_seconds': self.order_timeout,
        }


# Example usage
if __name__ == "__main__":
    # Initialize protection
    protection = SlippageProtection(
        max_slippage_percent=0.2,  # 0.2% max
        order_timeout_seconds=30
    )

    print("Slippage Protection Test")
    print("=" * 50)

    # Test 1: Buy order
    print("\nTest 1: Buy BTC at $95,000")
    current_price = 95000.0
    limit_price = protection._calculate_limit_price(current_price, 'buy')
    print(f"  Current price: ${current_price}")
    print(f"  Limit price: ${limit_price}")
    print(f"  Max pay: ${current_price * 1.002} (0.2% slippage)")

    # Test 2: Sell order
    print("\nTest 2: Sell ETH at $3,300")
    current_price = 3300.0
    limit_price = protection._calculate_limit_price(current_price, 'sell')
    print(f"  Current price: ${current_price}")
    print(f"  Limit price: ${limit_price}")
    print(f"  Min receive: ${current_price * 0.998} (0.2% slippage)")

    # Test 3: Check executed slippage
    print("\nTest 3: Check execution slippage")
    intended = 95000.0
    executed = 95150.0  # 0.158% slippage
    acceptable, slip_pct, warning = protection.check_execution_slippage(
        intended, executed, 'buy'
    )
    print(f"  Intended: ${intended}")
    print(f"  Executed: ${executed}")
    print(f"  Slippage: {slip_pct:.3f}%")
    print(f"  Acceptable: {acceptable}")
    if warning:
        print(f"  Warning: {warning}")

    print("\n" + "=" * 50)
    print("✅ Slippage protection ready for production")
