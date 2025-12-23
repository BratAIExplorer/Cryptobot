#!/usr/bin/env python3
"""
Unified Exchange Interface - Supports Multiple Exchanges
Automatically handles Binance, MEXC, and future exchanges
With automatic exchange tagging for data separation

CRITICAL: All trades are tagged with exchange name
- Binance trades: exchange='Binance'
- MEXC trades: exchange='MEXC'
"""
import ccxt
import pandas as pd
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedExchange:
    """
    Universal exchange interface supporting multiple exchanges
    Ensures data separation via automatic tagging
    """
    
    def __init__(self, exchange_name='MEXC', mode='paper'):
        """
        Initialize exchange connection
        
        Args:
            exchange_name: 'MEXC', 'Binance', etc.
            mode: 'paper' or 'live'
        """
        self.exchange_name = exchange_name.upper()
        self.mode = mode
        
        # Load API keys based on exchange
        if self.exchange_name == 'MEXC':
            api_key = os.getenv('MEXC_API_KEY')
            secret = os.getenv('MEXC_SECRET_KEY')
            self.exchange = ccxt.mexc({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'rateLimit': 100,  # MEXC: 100ms
                'options': {'defaultType': 'spot'},
            })
            self.maker_fee = 0.0000  # 0% maker
            self.taker_fee = 0.00025  # 0.025% with MX tokens
            
        elif self.exchange_name == 'BINANCE':
            api_key = os.getenv('BINANCE_API_KEY')
            secret = os.getenv('BINANCE_SECRET_KEY')
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'rateLimit': 50,  # Binance: 50ms
                'options': {'defaultType': 'spot'},
            })
            self.maker_fee = 0.001  # 0.1% maker
            self.taker_fee = 0.001  # 0.1% taker
            
        elif self.exchange_name == 'LUNO':
            api_key = os.getenv('LUNO_API_KEY_ID') or os.getenv('LUNO_API_KEY')
            secret = os.getenv('LUNO_API_KEY_SECRET') or os.getenv('LUNO_SECRET_KEY')
            self.exchange = ccxt.luno({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
            self.maker_fee = 0.0000  # Usually 0% for Luno markers
            self.taker_fee = 0.0001  # 0.1% taker (check local fees)
        
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        # Load markets
        try:
            self.exchange.load_markets()
            logger.info(f"✅ Connected to {self.exchange_name} in {mode.upper()} mode")
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.exchange_name}: {e}")
            raise
    
    def get_exchange_metadata(self):
        """Return exchange metadata for tagging trades"""
        return {
            'exchange': self.exchange_name,
            'mode': self.mode,
            'maker_fee': self.maker_fee,
            'taker_fee': self.taker_fee,
        }
    
    def fetch_ticker(self, symbol):
        """Fetch current price ticker"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"{self.exchange_name} - Error fetching ticker {symbol}: {e}")
            return None
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"{self.exchange_name} - Error fetching OHLCV {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """Get current price (simple wrapper)"""
        ticker = self.fetch_ticker(symbol)
        return ticker['last'] if ticker else None
    
    def get_fee_rate(self, order_type='taker'):
        """Get trading fee rate"""
        return self.taker_fee if order_type == 'taker' else self.maker_fee
    
    def create_order(self, symbol, side, amount, price=None):
        """
        Create order on exchange
        
        Returns: Order dict with exchange metadata attached
        """
        if self.mode == 'paper':
            logger.info(f"📝 PAPER MODE: {side} {amount} {symbol} @ {price or 'market'} on {self.exchange_name}")
            # In paper mode, return simulated order
            return {
                'id': f'paper_{self.exchange_name}_{symbol}_{int(pd.Timestamp.now().timestamp())}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price or self.get_current_price(symbol),
                'exchange': self.exchange_name,  # TAG
                'mode': self.mode,  # TAG
                'status': 'closed',
            }
        
        try:
            if price:
                order = self.exchange.create_limit_order(symbol, side.lower(), amount, price)
            else:
                order = self.exchange.create_market_order(symbol, side.lower(), amount)
            
            # Attach metadata
            order['exchange'] = self.exchange_name  # TAG
            order['mode'] = self.mode  # TAG
            
            logger.info(f"✅ {self.exchange_name} - {side} {amount} {symbol} @ {price or 'market'}")
            return order
            
        except Exception as e:
            logger.error(f"❌ {self.exchange_name} - Order failed: {e}")
            return None
    
    def get_balance(self, currency='USDT'):
        """Get account balance"""
        if self.mode == 'paper':
            return 50000.0
        try:
            # Only fetch live balance if we have keys and are not in paper mode
            if self.exchange.apiKey and self.exchange.secret:
                balance = self.exchange.fetch_balance()
                return balance['total'].get(currency, 0.0)
            return 0.0
        except Exception as e:
            logger.error(f"{self.exchange_name} - Error fetching balance: {e}")
            return 0.0
    
    def fetch_balance(self):
        """Fetch full balance object from exchange"""
        if self.mode == 'paper':
            return {'total': {'USDT': 50000.0}, 'free': {'USDT': 50000.0}}
        try:
            if self.exchange.apiKey and self.exchange.secret:
                return self.exchange.fetch_balance()
            return {'total': {}, 'free': {}}
        except Exception as e:
            logger.error(f"{self.exchange_name} - Error fetching full balance: {e}")
            return {'total': {}, 'free': {}}
    
    def fetch_markets(self):
        """Fetch available markets"""
        try:
            return self.exchange.fetch_markets()
        except Exception as e:
            logger.error(f"{self.exchange_name} - Error fetching markets: {e}")
            return []


# Backward compatibility wrapper
class ExchangeInterface:
    """Legacy wrapper - automatically uses MEXC now"""
    def __init__(self, mode='paper', exchange='MEXC'):
        self.exchange = UnifiedExchange(exchange_name=exchange, mode=mode)
        
        # Delegate methods
        self.fetch_ticker = self.exchange.fetch_ticker
        self.fetch_ohlcv = self.exchange.fetch_ohlcv
        self.get_current_price = self.exchange.get_current_price
        self.get_fee_rate = self.exchange.get_fee_rate
        self.create_order = self.exchange.create_order
        self.get_balance = self.exchange.get_balance
        self.fetch_balance = self.exchange.fetch_balance
        self.fetch_markets = self.exchange.fetch_markets
        self.get_exchange_metadata = self.exchange.get_exchange_metadata


if __name__ == "__main__":
    # Test MEXC connection
    print("Testing MEXC connection...")
    mexc = UnifiedExchange('MEXC', 'paper')
    print(f"Exchange: {mexc.exchange_name}")
    print(f"Balance: ${mexc.get_balance('USDT'):.2f}")
    print(f"Metadata: {mexc.get_exchange_metadata()}")
    
    # Test Binance (if keys exist)
    try:
        binance = UnifiedExchange('Binance', 'paper')
        print(f"\nBinance Balance: ${binance.get_balance('USDT'):.2f}")
    except:
        print("\nBinance keys not configured (OK)")
