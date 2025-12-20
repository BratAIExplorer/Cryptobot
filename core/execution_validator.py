"""
Execution Reality Layer
Validates trade feasibility before execution (slippage, liquidity, API health)
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConstraints:
    """Reality-based execution constraints"""
    max_slippage_pct: float = 0.3          # Max acceptable slippage
    min_order_book_depth_usd: float = 50000  # Min liquidity required
    max_api_latency_ms: int = 5000          # Max API response time
    max_spread_pct: float = 0.5             # Max bid-ask spread
    max_order_book_usage_pct: float = 30    # Use max 30% of order book depth


class ExecutionValidator:
    """
    Pre-trade execution feasibility validator.
    
    Checks:
    1. API Health: Is exchange responsive?
    2. Liquidity: Can we fill the order without massive slippage?
    3. Spread: Is bid-ask spread reasonable?
    4. Market conditions: Recent exchange outages? News events?
    """
    
    def __init__(self, exchange_client=None, constraints: Optional[ExecutionConstraints] = None):
        self.exchange = exchange_client
        self.constraints = constraints or ExecutionConstraints()
        self.api_health_cache = {}
        self.last_health_check = {}
        
    def validate_execution(
        self, 
        symbol: str, 
        side: str,  # 'BUY' or 'SELL'
        theoretical_price: float,
        order_size_usd: float
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Master execution validation.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            theoretical_price: Expected price from backtest/signals
            order_size_usd: Order size in USD
            
        Returns:
            Tuple of (is_allowed, rejection_reason, execution_metrics)
        """
        metrics = {}
        
        # Check 1: API Health
        api_healthy, api_reason = self._check_api_health(symbol)
        metrics['api_healthy'] = api_healthy
        if not api_healthy:
            return False, f"API Health Check Failed: {api_reason}", metrics
        
        # Check 2: Order Book Depth (requires exchange client)
        if self.exchange:
            liquidity_ok, liq_reason, depth_metrics = self._check_order_book_depth(
                symbol, side, order_size_usd
            )
            metrics.update(depth_metrics)
            if not liquidity_ok:
                return False, f"Liquidity Check Failed: {liq_reason}", metrics
        
        # Check 3: Spread Check
        if self.exchange:
            spread_ok, spread_reason, spread_metrics = self._check_spread(symbol)
            metrics.update(spread_metrics)
            if not spread_ok:
                return False, f"Spread Check Failed: {spread_reason}", metrics
        
        # Check 4: Expected Slippage Estimation
        expected_slippage = self._estimate_slippage(order_size_usd, metrics.get('order_book_depth_usd', 100000))
        metrics['expected_slippage_pct'] = expected_slippage
        
        if expected_slippage > self.constraints.max_slippage_pct:
            return False, f"Expected slippage {expected_slippage:.2f}% exceeds limit {self.constraints.max_slippage_pct}%", metrics
        
        return True, None, metrics
    
    def _check_api_health(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if exchange API is responsive.
        
        Uses caching to avoid hammering API with health checks.
        """
        # Check cache (valid for 60 seconds)
        cache_key = f"{symbol}_health"
        if cache_key in self.last_health_check:
            last_check_time = self.last_health_check[cache_key]
            if datetime.now() - last_check_time < timedelta(seconds=60):
                # Use cached result
                return self.api_health_cache.get(cache_key, (True, None))
        
        # Perform new health check
        if not self.exchange:
            # No exchange client, assume healthy
            return True, None
        
        try:
            start_time = time.time()
            
            # Simple ping: fetch ticker
            ticker = self.exchange.fetch_ticker(symbol)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Check latency
            if latency_ms > self.constraints.max_api_latency_ms:
                result = (False, f"API latency {latency_ms:.0f}ms exceeds {self.constraints.max_api_latency_ms}ms")
            else:
                result = (True, None)
            
            # Cache result
            self.api_health_cache[cache_key] = result
            self.last_health_check[cache_key] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"API health check failed for {symbol}: {e}")
            return False, f"API Error: {str(e)}"
    
    def _check_order_book_depth(
        self, 
        symbol: str, 
        side: str, 
        order_size_usd: float
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if order book has sufficient liquidity.
        
        Returns:
            Tuple of (is_sufficient, reason, metrics)
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=20)
            
            # Determine which side of book to check
            book_side = order_book['asks'] if side == 'BUY' else order_book['bids']
            
            # Calculate total depth in USD (sum of price * quantity)
            total_depth_usd = sum([price * qty for price, qty in book_side])
            
            metrics = {
                'order_book_depth_usd': total_depth_usd,
                'order_size_pct': (order_size_usd / total_depth_usd * 100) if total_depth_usd > 0 else 0
            }
            
            # Check if depth is sufficient
            if total_depth_usd < self.constraints.min_order_book_depth_usd:
                return False, f"Insufficient liquidity: ${total_depth_usd:.0f} < ${self.constraints.min_order_book_depth_usd}", metrics
            
            # Check if our order is too large relative to book
            if order_size_usd > total_depth_usd * (self.constraints.max_order_book_usage_pct / 100):
                return False, f"Order too large: {metrics['order_size_pct']:.1f}% of book", metrics
            
            return True, None, metrics
            
        except Exception as e:
            logger.error(f"Order book check failed for {symbol}: {e}")
            return False, f"Order book fetch error: {str(e)}", {}
    
    def _check_spread(self, symbol: str) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if bid-ask spread is reasonable.
        
        Wide spreads indicate low liquidity or volatile conditions.
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            
            if bid == 0 or ask == 0:
                return False, "Missing bid/ask data", {}
            
            spread_pct = ((ask - bid) / bid) * 100
            
            metrics = {
                'bid': bid,
                'ask': ask,
                'spread_pct': spread_pct
            }
            
            if spread_pct > self.constraints.max_spread_pct:
                return False, f"Spread {spread_pct:.2f}% exceeds {self.constraints.max_spread_pct}%", metrics
            
            return True, None, metrics
            
        except Exception as e:
            logger.error(f"Spread check failed for {symbol}: {e}")
            return False, f"Spread check error: {str(e)}", {}
    
    def _estimate_slippage(self, order_size_usd: float, book_depth_usd: float) -> float:
        """
        Estimate expected slippage based on order size vs book depth.
        
        Formula:
        - Small orders (<5% of book): 0.1% slippage
        - Medium orders (5-15% of book): 0.3% slippage
        - Large orders (15-30% of book): 0.5% slippage
        - Huge orders (>30% of book): 1.0%+ slippage
        
        Returns:
            Estimated slippage percentage
        """
        if book_depth_usd == 0:
            return 1.0  # Conservative estimate if no data
        
        order_pct = (order_size_usd / book_depth_usd) * 100
        
        if order_pct < 5:
            return 0.1
        elif order_pct < 15:
            return 0.3
        elif order_pct < 30:
            return 0.5
        else:
            return 1.0
    
    def apply_slippage_to_price(self, price: float, side: str, slippage_pct: float = 0.3) -> float:
        """
        Adjust theoretical price for slippage.
        
        Args:
            price: Theoretical fill price
            side: 'BUY' or 'SELL'
            slippage_pct: Expected slippage percentage
            
        Returns:
            Adjusted price accounting for slippage
        """
        slippage_multiplier = 1 + (slippage_pct / 100)
        
        if side == 'BUY':
            # Buying is more expensive due to slippage
            return price * slippage_multiplier
        else:
            # Selling gets less due to slippage
            return price / slippage_multiplier


# Convenience function for backtesting
def apply_backtest_penalties(
    theoretical_pnl: float, 
    trade_count: int,
    avg_slippage_pct: float = 0.3,
    fee_pct: float = 0.1
) -> float:
    """
    Apply realistic execution penalties to backtest results.
    
    Args:
        theoretical_pnl: Profit/loss from perfect fills
        trade_count: Number of trades executed
        avg_slippage_pct: Average slippage per trade
        fee_pct: Trading fee percentage per trade
        
    Returns:
        Adjusted PnL after execution costs
    """
    # Each trade has both entry and exit
    total_cost_pct = (avg_slippage_pct + fee_pct) * 2 * trade_count
    
    # Reduce PnL by costs (conservative estimate)
    adjusted_pnl = theoretical_pnl * (1 - (total_cost_pct / 100))
    
    return adjusted_pnl
