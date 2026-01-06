"""
Enhanced Base Strategy with Adapter Abstraction
Provides clean separation between strategy logic and exchange implementation

This enhanced base class allows strategies to work with ANY exchange adapter
without modification, enabling true exchange portability.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Enhanced base class for all trading strategies
    Completely decoupled from exchange implementation details

    Features:
    - Exchange-agnostic design
    - Automatic kill switch respect
    - Adapter abstraction
    - Consistent interface across all strategies
    """

    def __init__(self, config: Dict, adapter=None):
        """
        Initialize strategy

        Args:
            config: Strategy configuration dictionary
            adapter: BaseExchangeAdapter instance (optional, can be set later)
        """
        self.config = config
        self.adapter = adapter  # BaseExchangeAdapter instance
        self.name = config.get('name', 'UnnamedStrategy')
        self.symbols = config.get('symbols', [])

        logger.info(f"[Strategy] Initialized: {self.name}")

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal based on market data

        Args:
            df: OHLCV DataFrame with columns: timestamp, open, high, low, close, volume
            **kwargs: Additional parameters (symbol, current_price, etc.)

        Returns:
            Signal dictionary if trade signal generated, None otherwise:
            {
                'side': 'BUY' | 'SELL',
                'symbol': str,
                'amount': float,
                'price': Optional[float],  # None for market orders
                'reason': str,  # Human-readable explanation
                'confidence': Optional[float],  # 0-100 confidence score
                'metadata': Optional[Dict]  # Additional strategy-specific data
            }

        Example:
            >>> signal = strategy.generate_signal(df, symbol='BTC/USDT')
            >>> print(signal)
            {
                'side': 'BUY',
                'symbol': 'BTC/USDT',
                'amount': 100.0,
                'price': None,  # Market order
                'reason': 'Grid level reached at $90,000',
                'confidence': 85
            }
        """
        pass

    # ========================================
    # Adapter Interface Methods
    # ========================================

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for symbol via adapter

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Current price or None if unavailable
        """
        if self.adapter:
            try:
                return self.adapter.get_current_price(symbol)
            except Exception as e:
                logger.error(f"[{self.name}] Failed to get price for {symbol}: {e}")
                return None

        logger.warning(f"[{self.name}] No adapter set, cannot get price")
        return None

    def get_ohlcv(self, symbol: str, timeframe='1h', limit=100) -> pd.DataFrame:
        """
        Get OHLCV (candlestick) data via adapter

        Args:
            symbol: Trading pair
            timeframe: Candle timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: Number of candles to retrieve

        Returns:
            DataFrame with OHLCV data or empty DataFrame if unavailable
        """
        if self.adapter:
            try:
                return self.adapter.fetch_ohlcv(symbol, timeframe, limit)
            except Exception as e:
                logger.error(f"[{self.name}] Failed to get OHLCV for {symbol}: {e}")
                return pd.DataFrame()

        logger.warning(f"[{self.name}] No adapter set, cannot get OHLCV")
        return pd.DataFrame()

    def get_balance(self, currency='USDT') -> float:
        """
        Get account balance via adapter

        Args:
            currency: Currency to check (default: USDT)

        Returns:
            Balance amount or 0.0 if unavailable
        """
        if self.adapter:
            try:
                return self.adapter.get_balance(currency)
            except Exception as e:
                logger.error(f"[{self.name}] Failed to get balance: {e}")
                return 0.0

        logger.warning(f"[{self.name}] No adapter set, cannot get balance")
        return 0.0

    def get_fee_rate(self, symbol: str, order_type='taker') -> float:
        """
        Get exchange fee rate via adapter

        Args:
            symbol: Trading pair
            order_type: 'maker' or 'taker'

        Returns:
            Fee rate as decimal (e.g., 0.001 for 0.1%)
        """
        if self.adapter:
            try:
                return self.adapter.get_fee_rate(symbol, order_type)
            except Exception as e:
                logger.error(f"[{self.name}] Failed to get fee rate: {e}")
                return 0.001  # Default 0.1%

        return 0.001  # Default if no adapter

    # ========================================
    # Safety and Control Methods
    # ========================================

    def can_trade(self) -> bool:
        """
        Check if trading is currently allowed

        Respects:
        - Adapter kill switch
        - Exchange connectivity

        Returns:
            True if trading allowed, False otherwise
        """
        if not self.adapter:
            logger.warning(f"[{self.name}] No adapter set, trading not allowed")
            return False

        if self.adapter.kill_switch_active:
            logger.warning(f"[{self.name}] Kill switch active, trading blocked")
            return False

        return True

    def set_adapter(self, adapter):
        """
        Set or change the exchange adapter

        Args:
            adapter: BaseExchangeAdapter instance

        Example:
            >>> from core.exchanges.mexc_adapter import MexcAdapter
            >>> strategy.set_adapter(MexcAdapter('paper'))
        """
        self.adapter = adapter
        logger.info(
            f"[{self.name}] Adapter set: {adapter.exchange_name if adapter else 'None'}"
        )

    # ========================================
    # Utility Methods
    # ========================================

    def log(self, message: str, level='info'):
        """
        Log message with strategy name prefix

        Args:
            message: Message to log
            level: Log level ('info', 'warning', 'error', 'debug')
        """
        full_message = f"[{self.name}] {message}"

        if level == 'info':
            logger.info(full_message)
        elif level == 'warning':
            logger.warning(full_message)
        elif level == 'error':
            logger.error(full_message)
        elif level == 'debug':
            logger.debug(full_message)

    def get_config_value(self, key: str, default=None):
        """
        Get configuration value with fallback

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def validate_signal(self, signal: Dict) -> bool:
        """
        Validate signal dictionary format

        Args:
            signal: Signal dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        if not signal:
            return False

        required_keys = ['side', 'symbol', 'amount']

        for key in required_keys:
            if key not in signal:
                self.log(f"Invalid signal: missing '{key}'", 'error')
                return False

        # Validate side
        if signal['side'] not in ['BUY', 'SELL']:
            self.log(f"Invalid signal: side must be BUY or SELL, got '{signal['side']}'", 'error')
            return False

        # Validate amount
        if signal['amount'] <= 0:
            self.log(f"Invalid signal: amount must be > 0, got {signal['amount']}", 'error')
            return False

        return True

    def __repr__(self):
        """String representation"""
        adapter_name = self.adapter.exchange_name if self.adapter else 'No Adapter'
        return f"<{self.__class__.__name__} '{self.name}' on {adapter_name}>"


# Example usage
if __name__ == "__main__":
    # Example strategy implementation
    class SimpleMAStrategy(BaseStrategy):
        """Example: Moving Average Crossover Strategy"""

        def generate_signal(self, df: pd.DataFrame, **kwargs) -> Optional[Dict[str, Any]]:
            if len(df) < 50:
                return None  # Not enough data

            # Calculate moving averages
            df['ma20'] = df['close'].rolling(20).mean()
            df['ma50'] = df['close'].rolling(50).mean()

            # Get current values
            current_ma20 = df['ma20'].iloc[-1]
            current_ma50 = df['ma50'].iloc[-1]
            previous_ma20 = df['ma20'].iloc[-2]
            previous_ma50 = df['ma50'].iloc[-2]

            symbol = kwargs.get('symbol')
            current_price = self.get_current_price(symbol)

            # Bullish crossover
            if previous_ma20 <= previous_ma50 and current_ma20 > current_ma50:
                return {
                    'side': 'BUY',
                    'symbol': symbol,
                    'amount': 100.0,
                    'price': None,  # Market order
                    'reason': 'MA20 crossed above MA50 (Golden Cross)',
                    'confidence': 75
                }

            # Bearish crossover
            elif previous_ma20 >= previous_ma50 and current_ma20 < current_ma50:
                return {
                    'side': 'SELL',
                    'symbol': symbol,
                    'amount': 100.0,
                    'price': None,
                    'reason': 'MA20 crossed below MA50 (Death Cross)',
                    'confidence': 75
                }

            return None

    # Demo
    print("Enhanced Base Strategy Demo")
    print("=" * 60)

    # Create strategy
    config = {'name': 'MA Crossover Demo', 'symbols': ['BTC/USDT']}
    strategy = SimpleMAStrategy(config)

    print(f"Strategy: {strategy}")
    print(f"Can trade: {strategy.can_trade()}")  # False (no adapter)

    # Simulate adapter
    from core.exchanges.mexc_adapter import MexcAdapter
    adapter = MexcAdapter('paper')
    strategy.set_adapter(adapter)

    print(f"Can trade now: {strategy.can_trade()}")  # True
    print(f"Exchange: {strategy.adapter.exchange_name}")
