from ..interfaces.base_adapter import BaseExchangeAdapter
import ccxt
import pandas as pd
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BinanceAdapter(BaseExchangeAdapter):
    """
    Binance Adapter Implementation
    """
    
    def __init__(self, mode: str = 'paper'):
        super().__init__(mode)
        self.exchange_name = "BINANCE"
        
        self.api_key = os.environ.get('BINANCE_API_KEY')
        self.secret = os.environ.get('BINANCE_SECRET_KEY')
        
        self.maker_fee = 0.001
        self.taker_fee = 0.001
        
        self._initialize_exchange()

    def _initialize_exchange(self):
        config = {
            'enableRateLimit': True,
            'rateLimit': 50,
            'options': {'defaultType': 'spot'},
            'timeout': 30000,
        }
        if self.api_key and self.secret:
            config['apiKey'] = self.api_key
            config['secret'] = self.secret
        
        try:
            self.exchange = ccxt.binance(config)
            if self.mode != 'paper':
                self.exchange.load_markets()
            logger.info(f"✅ Connected to Binance ({self.mode})")
        except Exception as e:
            logger.error(f"❌ Binance Connection Error: {e}")
            self.trigger_kill_switch("Connection Failed on Startup")

    def get_current_price(self, symbol: str) -> Optional[float]:
        if self.kill_switch_active: return None
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"❌ Binance Ticker Error {symbol}: {e}")
            return None

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        if self.kill_switch_active: return pd.DataFrame()
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"❌ Binance OHLCV Error {symbol}: {e}")
            return pd.DataFrame()

    def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if self.kill_switch_active:
            logger.warning(f"⛔ Order Blocked: Kill Switch Active ({symbol} {side})")
            return None

        if self.mode == 'paper':
            logger.info(f"📝 [PAPER] Binance {side} {amount} {symbol} @ {price or 'MARKET'}")
            return {
                'id': f'paper_binance_{int(time.time())}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price or self.get_current_price(symbol),
                'status': 'closed',
                'exchange': 'BINANCE',
                'mode': 'paper'
            }

        try:
            if price:
                order = self.exchange.create_order(symbol, 'limit', side, amount, price)
            else:
                order = self.exchange.create_order(symbol, 'market', side, amount)
            
            order['exchange'] = 'BINANCE'
            order['mode'] = 'live'
            logger.info(f"✅ Binance Order Executed: {side} {symbol}")
            return order
        except Exception as e:
            logger.error(f"❌ Binance Order Failed: {e}")
            return None

    def get_balance(self, currency: str = 'USDT') -> float:
        if self.mode == 'paper': return 50000.0
        try:
            bal = self.exchange.fetch_balance()
            return bal['total'].get(currency, 0.0)
        except Exception as e:
            logger.error(f"❌ Binance Balance Error: {e}")
            return 0.0

    def fetch_balance(self) -> Dict[str, Any]:
        """Fetch full balance dictionary (for engine portfolio snapshots)"""
        if self.mode == 'paper':
            return {'total': {'USDT': 50000.0}, 'free': {'USDT': 50000.0}}
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"❌ Binance fetch_balance Error: {e}")
            return {'total': {}, 'free': {}}

    def fetch_markets(self):
        """Fetch available markets (for detector and watchlist)"""
        if self.mode == 'paper':
            # Return empty for paper mode - detector doesn't need this
            return []
        try:
            return self.exchange.fetch_markets()
        except Exception as e:
            logger.error(f"❌ Binance fetch_markets Error: {e}")
            return []

    def get_fee_rate(self, symbol: str, order_type: str = 'taker') -> float:
        return self.taker_fee

    def check_health(self) -> Dict[str, Any]:
        try:
            start = time.time()
            self.exchange.fetch_time()
            latency = int((time.time() - start) * 1000)
            status = 'ONLINE'
            
            if latency > 1000: status = 'DEGRADED'
            if latency > 5000: 
                status = 'CRITICAL'
                self.trigger_kill_switch(f"High Latency: {latency}ms")
                
            return {'status': status, 'latency_ms': latency}
        except Exception as e:
            self.trigger_kill_switch(f"Health Check Failed: {e}")
            return {'status': 'OFFLINE', 'error': str(e)}

    def shutdown(self):
        pass
