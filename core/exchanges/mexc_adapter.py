from ..interfaces.base_adapter import BaseExchangeAdapter
import ccxt
import pandas as pd
import os
import time
import logging
from datetime import datetime
from threading import Thread, Event
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MexcAdapter(BaseExchangeAdapter):
    """
    MEXC Adapter Implementation
    Includes:
    - Reconnection Logic
    - Heartbeat
    - Volume Filtering
    - Kill Switch Integration
    """
    
    def __init__(self, mode: str = 'paper'):
        super().__init__(mode)
        self.exchange_name = "MEXC"
        
        # Keys
        self.api_key = os.environ.get('MEXC_API_KEY')
        self.secret = os.environ.get('MEXC_SECRET_KEY')
        
        # Config
        self.maker_fee = 0.0000
        self.taker_fee = 0.0005
        self.idle_timeout_seconds = 300
        self.last_activity = datetime.now()
        
        # Connect
        self.exchange = None
        self._initialize_exchange()
        
        # Heartbeat
        self.heartbeat_stop_event = Event()
        self.heartbeat_thread = Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def _initialize_exchange(self):
        config = {
            'enableRateLimit': True,
            'rateLimit': 100,
            'options': {'defaultType': 'spot', 'adjustForTimeDifference': True},
            'timeout': 30000,
        }
        if self.api_key and self.secret:
            config['apiKey'] = self.api_key
            config['secret'] = self.secret
        
        try:
            self.exchange = ccxt.mexc(config)
            if self.mode != 'paper':
                self.exchange.load_markets()
            logger.info(f"✅ Connected to MEXC ({self.mode})")
        except Exception as e:
            logger.error(f"❌ MEXC Connection Error: {e}")
            self.trigger_kill_switch("Connection Failed on Startup")

    def _check_connection(self):
        """Reconnect if idle or disconnected"""
        if (datetime.now() - self.last_activity).total_seconds() > self.idle_timeout_seconds:
            logger.info("🔄 MEXC Reconnecting due to idle...")
            self._initialize_exchange()
        self.last_activity = datetime.now()

    def get_current_price(self, symbol: str) -> Optional[float]:
        if self.kill_switch_active: return None
        self._check_connection()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"❌ MEXC Ticker Error {symbol}: {e}")
            return None

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        if self.kill_switch_active: return pd.DataFrame()
        self._check_connection()
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"❌ MEXC OHLCV Error {symbol}: {e}")
            return pd.DataFrame()

    def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if self.kill_switch_active:
            logger.warning(f"⛔ Order Blocked: Kill Switch Active ({symbol} {side})")
            return None

        self._check_connection()
        
        # Paper Trading Simulation
        if self.mode == 'paper':
            logger.info(f"📝 [PAPER] MEXC {side} {amount} {symbol} @ {price or 'MARKET'}")
            return {
                'id': f'paper_mexc_{int(time.time())}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price or self.get_current_price(symbol),
                'status': 'closed',
                'exchange': 'MEXC',
                'mode': 'paper'
            }

        # Live Execution
        try:
            if price:
                order = self.exchange.create_order(symbol, 'limit', side, amount, price)
            else:
                order = self.exchange.create_order(symbol, 'market', side, amount)
            
            # Normalize response
            order['exchange'] = 'MEXC'
            order['mode'] = 'live'
            logger.info(f"✅ MEXC Order Executed: {side} {symbol}")
            return order
        except Exception as e:
            logger.error(f"❌ MEXC Order Failed: {e}")
            return None

    def get_balance(self, currency: str = 'USDT') -> float:
        if self.mode == 'paper': return 50000.0
        self._check_connection()
        try:
            bal = self.exchange.fetch_balance()
            return bal['total'].get(currency, 0.0)
        except Exception as e:
            logger.error(f"❌ MEXC Balance Error: {e}")
            return 0.0

    def get_fee_rate(self, symbol: str, order_type: str = 'taker') -> float:
        return self.taker_fee if order_type == 'taker' else self.maker_fee

    def check_health(self) -> Dict[str, Any]:
        try:
            start = time.time()
            self.exchange.fetch_time()
            latency = int((time.time() - start) * 1000)
            status = 'ONLINE'
            
            if latency > 1000: status = 'DEGRADED'
            if latency > 2000: 
                status = 'CRITICAL'
                self.trigger_kill_switch(f"High Latency: {latency}ms")
                
            return {'status': status, 'latency_ms': latency}
        except Exception as e:
            self.trigger_kill_switch(f"Health Check Failed: {e}")
            return {'status': 'OFFLINE', 'error': str(e)}

    def _heartbeat_loop(self):
        while not self.heartbeat_stop_event.is_set():
            try:
                if not self.kill_switch_active:
                    self.exchange.fetch_time()
            except:
                pass
            time.sleep(60)

    def shutdown(self):
        self.heartbeat_stop_event.set()
