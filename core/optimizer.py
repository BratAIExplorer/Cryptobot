"""
CryptoIntel Hub - Hyperparameter Optimizer
Brute-force optimization engine for trading strategies.
"""
import pandas as pd
import numpy as np
import itertools
from concurrent.futures import ThreadPoolExecutor
import requests
import time

# Import Fast Engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtesting.numpy_engine import FastBacktester, calculate_rsi

class HyperOptimizer:
    def __init__(self, symbols, interval='15m', limit=1000):
        self.symbols = symbols
        self.interval = interval
        self.limit = limit
        self.data_cache = {} # {symbol: df}
        
    def fetch_data(self):
        """Fetch data for all symbols (Threaded)"""
        print(f"📥 Fetching data for {len(self.symbols)} symbols...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(self._fetch_single, self.symbols))
            
        print(f"✅ Data fetched for {len(self.data_cache)} symbols.")
        
    def _fetch_single(self, symbol):
        """Fetch single symbol data from Binance"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {'symbol': symbol.replace('/', ''), 'interval': self.interval, 'limit': self.limit}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'v', 'ct', 'qav', 'nt', 'tbv', 'tqv', 'ig'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col].astype(float)
                self.data_cache[symbol] = df
            else:
                print(f"⚠️ No data for {symbol}")
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")

    def optimize_rsi(self, rsi_periods, rsi_limits):
        """
        Run Grid Search for RSI Strategy.
        
        Args:
            rsi_periods (list): [7, 10, 14, 21]
            rsi_limits (list): [20, 25, 30, 35, 40]
            
        Returns:
            DataFrame of results
        """
        if not self.data_cache:
            self.fetch_data()
            
        results = []
        
        print("\n🚀 Starting Optimization...")
        start_time = time.time()
        
        total_combos = len(self.symbols) * len(rsi_periods) * len(rsi_limits)
        processed = 0
        
        # Grid Search
        # We iterate: Symbol -> Period -> Limit
        # Optimization: Calculate RSI(Period) once per symbol/period
        
        for symbol, df in self.data_cache.items():
            # Init Engine
            engine = FastBacktester(df)
            
            for period in rsi_periods:
                # Pre-calc Indicator
                rsi_values = calculate_rsi(df['close'].values, period=period)
                engine.add_indicator('rsi', rsi_values)
                
                for limit in rsi_limits:
                    # Run Simulation
                    # Fixed TP/SL for now (3% / 5%) to isolate RSI parameters
                    # Future: Optimize TP/SL too
                    res = engine.run_rsi_strategy(rsi_limit=limit, tp_pct=0.03, sl_pct=0.05)
                    
                    results.append({
                        'Symbol': symbol,
                        'Period': period,
                        'Limit': limit,
                        'Profit': res['total_profit'],
                        'Trades': res['trade_count'],
                        'WinRate': res['win_rate'],
                        'Score': res['total_profit'] * (res['win_rate'] / 50) # Score weighted by consistency
                    })
                    processed += 1
                    
        elapsed = time.time() - start_time
        print(f"✅ Processed {processed} combinations in {elapsed:.2f} seconds.")
        
        return pd.DataFrame(results).sort_values(by='Score', ascending=False)

if __name__ == "__main__":
    # Test Run
    opt = HyperOptimizer(['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT'])
    
    # Define Grid
    periods = range(5, 25, 2) # 5, 7, 9... 23
    limits = range(15, 45, 5) # 15, 20... 40
    
    df_res = opt.optimize_rsi(periods, limits)
    
    print("\n🏆 TOP 10 PARAMETER SETS")
    print(df_res.head(10).to_string(index=False))
    
    # Best Overall
    best = df_res.iloc[0]
    print(f"\n🌟 BEST CONFIG: RSI Period {best['Period']}, Limit {best['Limit']}")
