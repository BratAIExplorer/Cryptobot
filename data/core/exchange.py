import ccxt
import pandas as pd
import time

class ExchangeInterface:
    def __init__(self, mode='paper'):
        # mode is ignored for now - we always use Binance public API
        self.exchange_id = 'binance'
        self.exchange = ccxt.binance({
            'enableRateLimit': True,  # Required by CCXT
        })
        
        # Load markets
        try:
            self.exchange.load_markets()
            print(f"Connected to {self.exchange_id}")
        except Exception as e:
            print(f"Error connecting to exchange: {e}")

    def fetch_ticker(self, symbol):
        """Fetch current price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return None

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch historical data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def get_fee_rate(self, symbol):
        """Get trading fee rate"""
        # Default to 0.1% if not found
        return 0.001 
