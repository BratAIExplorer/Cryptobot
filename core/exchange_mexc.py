import ccxt
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from threading import Thread, Event
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MEXCExchange:
    """
    MEXC Exchange Interface with Production-Grade Features:
    - Auto-reconnect on idle timeout
    - Heartbeat mechanism
    - Volume filtering for low-liquidity pairs
    - Rate limit handling specific to MEXC
    """
    
    def __init__(self, mode='paper'):
        self.mode = mode
        self.exchange_id = 'mexc'
       
        # MEXC-Specific Configuration
        self.maker_fee = 0.0000   # 0% maker fee
        self.taker_fee = 0.0005   # 0.05% taker fee (0.025% with 500+ MX tokens)
        
        # Connection Management
        self.last_activity = datetime.now()
        self.idle_timeout_seconds = 300  # 5 minutes (MEXC disconnects idle connections)
        self.heartbeat_interval = 60  # Send heartbeat every 60 seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Volume Filtering (prevent trading shitcoins)
        self.min_24h_volume_usd = 100000  # $100k minimum daily volume
        self.max_spread_pct = 0.03  # 3% max spread tolerated
        
        # Load API keys from environment
        api_key = os.environ.get('MEXC_API_KEY')
        secret = os.environ.get('MEXC_SECRET_KEY')
        
        config = {
            'enableRateLimit': True,
            'rateLimit': 100,  # MEXC: 100ms between requests (vs Binance 50ms)
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,  # Handle clock sync issues
            },
            'timeout': 30000,  # 30 second timeout
        }
        
        if api_key and secret:
            config['apiKey'] = api_key
            config['secret'] = secret
            logger.info("✅ Authenticated with MEXC API")
        else:
            logger.warning("⚠️ Running in Public/Read-Only Mode (No Keys Found)")
        
        # Initialize exchange
        self.exchange = None
        self._initialize_exchange(config)
        
        # Start heartbeat thread
        self.heartbeat_stop_event = Event()
        self.heartbeat_thread = Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("✅ Heartbeat thread started")
    
    def _initialize_exchange(self, config):
        """Initialize or reinitialize MEXC exchange connection"""
        try:
            self.exchange = ccxt.mexc(config)
            self.exchange.load_markets()
            logger.info(f"✅ Connected to {self.exchange_id}")
            self.reconnect_attempts = 0
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to MEXC: {e}")
            return False
    
    def _check_and_reconnect(self):
        """Check for idle timeout and reconnect if necessary"""
        idle_duration = (datetime.now() - self.last_activity).total_seconds()
        
        if idle_duration > self.idle_timeout_seconds:
            logger.warning(f"⚠️ Idle for {idle_duration:.0f}s, reconnecting to prevent timeout...")
            return self._reconnect()
        
        return True
    
    def _reconnect(self):
        """Attempt to reconnect to MEXC"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ Max reconnect attempts ({self.max_reconnect_attempts}) reached. Manual intervention required.")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"🔄 Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        time.sleep(2 ** self.reconnect_attempts)  # Exponential backoff
        
        config = self.exchange.describe() if self.exchange else {}
        return self._initialize_exchange(config)
    
    def _heartbeat_loop(self):
        """Background thread that sends periodic heartbeats"""
        while not self.heartbeat_stop_event.is_set():
            try:
                # Send a lightweight request to keep connection alive
                if self.exchange:
                    _ = self.exchange.fetch_time()  # Lightweight API call
                    logger.debug(f"💓 Heartbeat sent (idle: {(datetime.now() - self.last_activity).total_seconds():.0f}s)")
            except Exception as e:
                logger.warning(f"⚠️ Heartbeat failed: {e}")
                self._reconnect()
            
            time.sleep(self.heartbeat_interval)
    
    def _update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def _check_pair_volume(self, symbol):
        """
        Check if trading pair has sufficient volume and acceptable spread
        Returns: (is_tradeable, reason)
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # Check 24h volume
            volume_usd = ticker.get('quoteVolume', 0)
            if volume_usd < self.min_24h_volume_usd:
                return False, f"Low volume: ${volume_usd:,.0f} < ${self.min_24h_volume_usd:,.0f}"
            
            # Check spread
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            if bid > 0:
                spread_pct = (ask - bid) / bid
                if spread_pct > self.max_spread_pct:
                    return False, f"Wide spread: {spread_pct*100:.2f}% > {self.max_spread_pct*100:.2f}%"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Error checking pair: {e}"
    
    def fetch_ticker(self, symbol):
        """Fetch current price for a symbol with reconnect logic"""
        self._check_and_reconnect()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            self._update_activity()
            return ticker
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching ticker for {symbol}: {e}")
            if self._reconnect():
                return self.exchange.fetch_ticker(symbol)  # Retry once
            return None
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch historical data with reconnect logic"""
        self._check_and_reconnect()
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            self._update_activity()
            return df
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
            if self._reconnect():
                return self.fetch_ohlcv(symbol, timeframe, limit)  # Retry once
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_fee_rate(self, symbol, order_type='taker'):
        """Get trading fee rate (MEXC-specific)"""
        if order_type == 'maker':
            return self.maker_fee
        else:
            return self.taker_fee
    
    def create_order(self, symbol, side, amount, price=None):
        """
        Execute a live order on MEXC (with volume check and reconnect logic)
        """
        self._check_and_reconnect()
        
        # Pre-flight check: Verify pair has sufficient volume
        is_tradeable, reason = self._check_pair_volume(symbol)
        if not is_tradeable:
            logger.error(f"❌ BLOCKED: Cannot trade {symbol} - {reason}")
            return None
        
        try:
            if price:
                # Limit Order
                order = self.exchange.create_order(symbol, 'limit', side, amount, price)
            else:
                # Market Order
                order = self.exchange.create_order(symbol, 'market', side, amount)
            
            self._update_activity()
            logger.info(f"✅ Order executed: {side} {amount} {symbol} @ {price or 'market'}")
            return order
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ INSUFFICIENT FUNDS: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ INVALID ORDER: {e}")
            return None
        except ccxt.NetworkError as e:
            logger.error(f"❌ NETWORK ERROR: {e}")
            if self._reconnect():
                # Do NOT retry order execution automatically (risk double-fill)
                logger.warning("⚠️ Reconnected but not retrying order. Check exchange UI manually.")
            return None
        except Exception as e:
            logger.error(f"❌ EXECUTION ERROR: {e}")
            return None
    
    def get_balance(self, currency='USDT'):
        """Get live wallet balance with reconnect logic"""
        self._check_and_reconnect()
        
        try:
            balance = self.exchange.fetch_balance()
            self._update_activity()
            return balance['total'].get(currency, 0.0)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            if self._reconnect():
                return self.get_balance(currency)  # Retry once
            return 0.0
    
    def get_order_book(self, symbol, limit=10):
        """Fetch order book depth for slippage estimation"""
        self._check_and_reconnect()
        
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            self._update_activity()
            return order_book
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    def estimate_slippage(self, symbol, side, amount):
        """
        Estimate slippage for a given order size
        Returns: (estimated_fill_price, slippage_pct)
        """
        try:
            order_book = self.get_order_book(symbol, limit=50)
            ticker = self.fetch_ticker(symbol)
            mid_price = ticker['last']
            
            levels = order_book['asks'] if side == 'buy' else order_book['bids']
            
            remaining = amount
            total_cost = 0
            
            for price, qty in levels:
                if remaining <= 0:
                    break
                filled = min(remaining, qty)
                total_cost += filled * price
                remaining -= filled
            
            if remaining > 0:
                # Order too large for order book
                return None, 999.0  # Signal massive slippage
            
            avg_fill_price = total_cost / amount
            slippage_pct = abs((avg_fill_price - mid_price) / mid_price) * 100
            
            return avg_fill_price, slippage_pct
            
        except Exception as e:
            logger.error(f"Error estimating slippage: {e}")
            return None, 0.0
    
    def shutdown(self):
        """Graceful shutdown of heartbeat thread"""
        logger.info("🛑 Shutting down MEXC exchange interface...")
        self.heartbeat_stop_event.set()
        if self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        logger.info("✅ Heartbeat thread stopped")


# Backward-compatible wrapper for existing code
class ExchangeInterface:
    """
    Wrapper that maintains compatibility with existing codebase
    while using MEXC backend
    """
    def __init__(self, mode='paper', exchange_type='mexc'):
        if exchange_type == 'mexc':
            self.exchange = MEXCExchange(mode=mode)
        else:
            # Fallback to Binance for comparison
            from core.exchange import ExchangeInterface as BinanceExchange
            self.exchange = BinanceExchange(mode=mode)
        
        # Delegate all method calls to the underlying exchange
        self.fetch_ticker = self.exchange.fetch_ticker
        self.fetch_ohlcv = self.exchange.fetch_ohlcv
        self.get_fee_rate = self.exchange.get_fee_rate
        self.create_order = self.exchange.create_order
        self.get_balance = self.exchange.get_balance
        
        # MEXC-specific methods
        if hasattr(self.exchange, 'estimate_slippage'):
            self.estimate_slippage = self.exchange.estimate_slippage
        if hasattr(self.exchange, 'shutdown'):
            self.shutdown = self.exchange.shutdown
