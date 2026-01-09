"""
Position Reconciliation - Database vs Exchange Validation

Detects when local database doesn't match exchange reality:
- Missing positions (API failure during order)
- Extra positions (database not updated)
- Wrong quantities (partial fills not recorded)

Design: HALT TRADING on ANY mismatch (fail-safe)
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ReconciliationError(Exception):
    """Raised when positions don't match"""
    pass


class PositionReconciler:
    """
    Reconciles database positions with exchange API

    Runs every 5 minutes (configurable)
    Detects and reports any mismatches
    Halts trading on critical mismatch
    """

    def __init__(
        self,
        exchange_adapter,
        logger_instance,
        tolerance_usd: float = 1.0,
        check_interval_seconds: int = 300
    ):
        """
        Initialize reconciler

        Args:
            exchange_adapter: Exchange API adapter (Binance, etc)
            logger_instance: TradeLogger for database access
            tolerance_usd: Acceptable difference in USD (for rounding)
            check_interval_seconds: How often to reconcile (default 5min)
        """
        self.exchange = exchange_adapter
        self.db_logger = logger_instance
        self.tolerance = tolerance_usd
        self.check_interval = check_interval_seconds

        self.last_check_time = None
        self.mismatch_count = 0
        self.total_checks = 0

        logger.info(f"Position Reconciler initialized:")
        logger.info(f"  Tolerance: ${tolerance_usd}")
        logger.info(f"  Check interval: {check_interval_seconds}s")

    def reconcile(self) -> Tuple[bool, Optional[Dict]]:
        """
        Reconcile database vs exchange positions

        Returns:
            (is_matched: bool, details: Dict)

        Raises:
            ReconciliationError: If critical mismatch detected
        """
        self.total_checks += 1
        self.last_check_time = datetime.now()

        logger.info(f"🔍 Starting reconciliation check #{self.total_checks}")

        try:
            # Get positions from database
            db_positions = self._get_db_positions()

            # Get positions from exchange API
            api_positions = self._get_api_positions()

            # Compare
            is_matched, details = self._compare_positions(db_positions, api_positions)

            if is_matched:
                logger.info("✅ Reconciliation passed: Positions match")
                return (True, details)
            else:
                self.mismatch_count += 1
                logger.error(f"❌ Reconciliation FAILED: Mismatch detected (#{self.mismatch_count})")
                logger.error(f"Details: {details}")

                # Critical: Raise error to halt trading
                raise ReconciliationError(
                    f"Position mismatch detected: {details.get('summary', 'Unknown error')}"
                )

        except ReconciliationError:
            # Re-raise reconciliation errors
            raise
        except Exception as e:
            # Log other errors but don't halt trading (could be API timeout)
            logger.error(f"Reconciliation check failed: {e}")
            return (False, {'error': str(e), 'critical': False})

    def _get_db_positions(self) -> Dict[str, Dict]:
        """
        Get open positions from database

        Returns:
            Dict[symbol: position_data]
        """
        positions = {}

        try:
            db_positions = self.db_logger.get_open_positions()

            for pos in db_positions.to_dict('records') if hasattr(db_positions, 'to_dict') else []:
                symbol = pos.get('symbol')
                if symbol:
                    positions[symbol] = {
                        'quantity': float(pos.get('amount', 0)),
                        'entry_price': float(pos.get('entry_price', 0)),
                        'cost_basis': float(pos.get('cost_basis', 0)),
                        'entry_date': pos.get('entry_date'),
                        'strategy': pos.get('strategy'),
                    }

            logger.info(f"Database: {len(positions)} open positions")
            return positions

        except Exception as e:
            logger.error(f"Failed to get database positions: {e}")
            return {}

    def _get_api_positions(self) -> Dict[str, Dict]:
        """
        Get actual positions from exchange API

        Returns:
            Dict[symbol: position_data]
        """
        positions = {}

        try:
            # Get account balance
            balance = self.exchange.fetch_balance()

            # Extract non-zero positions
            for currency, amount in balance.get('total', {}).items():
                if currency == 'USDT':
                    continue  # Skip quote currency

                amount = float(amount)
                if amount > 0.00001:  # Ignore dust
                    symbol = f"{currency}/USDT"  # Assume USDT pairs

                    # Get current price
                    ticker = self.exchange.fetch_ticker(symbol)
                    current_price = ticker['last'] if ticker else 0

                    positions[symbol] = {
                        'quantity': amount,
                        'current_price': current_price,
                        'value_usd': amount * current_price,
                    }

            logger.info(f"Exchange API: {len(positions)} open positions")
            return positions

        except Exception as e:
            logger.error(f"Failed to get exchange positions: {e}")
            return {}

    def _compare_positions(
        self,
        db_positions: Dict,
        api_positions: Dict
    ) -> Tuple[bool, Dict]:
        """
        Compare database vs API positions

        Returns:
            (is_matched: bool, details: Dict)
        """
        mismatches = []

        # Check for positions in DB but not in API (missing on exchange)
        for symbol in db_positions:
            if symbol not in api_positions:
                mismatches.append({
                    'type': 'missing_on_exchange',
                    'symbol': symbol,
                    'db_quantity': db_positions[symbol]['quantity'],
                    'api_quantity': 0,
                })

        # Check for positions in API but not in DB (not recorded)
        for symbol in api_positions:
            if symbol not in db_positions:
                mismatches.append({
                    'type': 'missing_in_database',
                    'symbol': symbol,
                    'db_quantity': 0,
                    'api_quantity': api_positions[symbol]['quantity'],
                })

        # Check for quantity mismatches
        for symbol in set(db_positions.keys()) & set(api_positions.keys()):
            db_qty = db_positions[symbol]['quantity']
            api_qty = api_positions[symbol]['quantity']

            # Calculate difference in USD value
            current_price = api_positions[symbol].get('current_price', 0)
            diff_usd = abs(db_qty - api_qty) * current_price

            if diff_usd > self.tolerance:
                mismatches.append({
                    'type': 'quantity_mismatch',
                    'symbol': symbol,
                    'db_quantity': db_qty,
                    'api_quantity': api_qty,
                    'diff_usd': diff_usd,
                })

        # Determine if matched
        is_matched = len(mismatches) == 0

        details = {
            'timestamp': datetime.now().isoformat(),
            'db_position_count': len(db_positions),
            'api_position_count': len(api_positions),
            'mismatch_count': len(mismatches),
            'mismatches': mismatches,
            'summary': self._generate_summary(mismatches) if mismatches else 'All positions match',
        }

        return (is_matched, details)

    def _generate_summary(self, mismatches: List[Dict]) -> str:
        """Generate human-readable summary of mismatches"""
        summary_parts = []

        missing_exchange = [m for m in mismatches if m['type'] == 'missing_on_exchange']
        missing_db = [m for m in mismatches if m['type'] == 'missing_in_database']
        qty_mismatch = [m for m in mismatches if m['type'] == 'quantity_mismatch']

        if missing_exchange:
            symbols = [m['symbol'] for m in missing_exchange]
            summary_parts.append(f"{len(missing_exchange)} positions in DB but not on exchange: {', '.join(symbols)}")

        if missing_db:
            symbols = [m['symbol'] for m in missing_db]
            summary_parts.append(f"{len(missing_db)} positions on exchange but not in DB: {', '.join(symbols)}")

        if qty_mismatch:
            symbols = [f"{m['symbol']} (diff: ${m['diff_usd']:.2f})" for m in qty_mismatch]
            summary_parts.append(f"{len(qty_mismatch)} quantity mismatches: {', '.join(symbols)}")

        return '; '.join(summary_parts)

    def get_status(self) -> Dict:
        """Get reconciliation status"""
        return {
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'total_checks': self.total_checks,
            'mismatch_count': self.mismatch_count,
            'match_rate': ((self.total_checks - self.mismatch_count) / self.total_checks * 100)
                          if self.total_checks > 0 else 0,
        }


# Example usage (requires actual exchange and logger instances)
if __name__ == "__main__":
    print("Position Reconciler")
    print("=" * 50)
    print("This module requires live exchange and database connections.")
    print("Run via TradingEngine integration for full functionality.")
    print()
    print("Features:")
    print("  ✓ Detects missing positions")
    print("  ✓ Detects extra positions")
    print("  ✓ Detects quantity mismatches")
    print("  ✓ Automatic trading halt on mismatch")
    print("  ✓ Configurable tolerance")
    print("  ✓ Status reporting")
