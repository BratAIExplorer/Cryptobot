#!/usr/bin/env python3
"""
MEXC Historical Data Downloader
Downloads 12 months of OHLCV data for backtesting

CRITICAL: All MEXC data is stored separately from Binance data
- Storage: data/mexc_history/
- Database: trades_mexc_backtest.db (separate from Binance)
- Metadata: All trades tagged with exchange='MEXC'
"""
import ccxt
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import sys

class MEXCHistoryDownloader:
    """Download historical OHLCV data from MEXC"""
    
    def __init__(self, output_dir='data/mexc_history'):
        self.exchange = ccxt.mexc({
            'enableRateLimit': True,
            'rateLimit': 100,  # MEXC rate limit
        })
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def download_symbol(self, symbol, timeframe='1h', months=12):
        """
        Download OHLCV data for a single symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
            months: Number of months to download
        """
        print(f"\n{'='*80}")
        print(f"Downloading {symbol} - {timeframe} - Last {months} months")
        print(f"{'='*80}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Convert to milliseconds
        since = int(start_date.timestamp() * 1000)
        
        all_candles = []
        
        try:
            while since < int(end_date.timestamp() * 1000):
                # Fetch batch
                candles = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe=timeframe, 
                    since=since,
                    limit=1000  # Max per request
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update timestamp
                since = candles[-1][0] + 1
                
                print(f"  Downloaded {len(all_candles)} candles... (up to {datetime.fromtimestamp(candles[-1][0]/1000)})")
                
                # Rate limit
                time.sleep(self.exchange.rateLimit / 1000)
        
        except Exception as e:
            print(f"  ❌ Error downloading {symbol}: {e}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['timestamp'].dt.date
        
        # Save to CSV
        filename = f"{symbol.replace('/', '_')}_{timeframe}_{months}m.csv"
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        
        print(f"  ✅ Saved: {filepath}")
        print(f"  📊 Total candles: {len(df)}")
        print(f"  📅 Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
        
        return df
    
    def download_all(self, symbols, timeframe='1h', months=12):
        """Download data for multiple symbols"""
        results = {}
        
        print(f"\n🚀 Starting MEXC Historical Data Download")
        print(f"   Symbols: {len(symbols)}")
        print(f"   Timeframe: {timeframe}")
        print(f"   Period: {months} months")
        print(f"   Output: {self.output_dir}/")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] {symbol}")
            df = self.download_symbol(symbol, timeframe, months)
            if df is not None:
                results[symbol] = df
        
        print(f"\n{'='*80}")
        print(f"✅ DOWNLOAD COMPLETE")
        print(f"   Success: {len(results)}/{len(symbols)} symbols")
        print(f"   Location: {self.output_dir}/")
        print(f"{'='*80}")
        
        return results

if __name__ == "__main__":
    # Default symbol list (can be customized)
    DEFAULT_SYMBOLS = [
        'BTC/USDT',
        'ETH/USDT',
        'SOL/USDT',
        'DOGE/USDT',
        'XRP/USDT',
        'AVAX/USDT',
        'DOT/USDT',
        'MATIC/USDT',
        'LINK/USDT',
        'ADA/USDT',
        'LTC/USDT',
        'BCH/USDT',
        'UNI/USDT',
        'APT/USDT',
        'ATOM/USDT',
        'NEAR/USDT',
        'ICP/USDT',
        'ETC/USDT',
        'PEPE/USDT',
        'SHIB/USDT',
    ]
    
    # Parse command line args
    timeframe = '1h'  # Default
    months = 12       # Default
    
    if len(sys.argv) > 1:
        timeframe = sys.argv[1]
    if len(sys.argv) > 2:
        months = int(sys.argv[2])
    
    # Download
    downloader = MEXCHistoryDownloader()
    results = downloader.download_all(DEFAULT_SYMBOLS, timeframe=timeframe, months=months)
    
    # Summary
    total_candles = sum(len(df) for df in results.values())
    total_size_mb = sum(df.memory_usage(deep=True).sum() / 1024 / 1024 for df in results.values())
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Candles: {total_candles:,}")
    print(f"   Total Size: {total_size_mb:.2f} MB")
    print(f"   Ready for backtest!")
