"""
CryptoIntel Hub - 24 Month Comprehensive Backtest
Fetches long-term historical data and simulates all default bot strategies.
"""
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime
import sys
import os

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtesting.numpy_engine import FastBacktester, calculate_rsi, calculate_sma

def fetch_historical_klines(symbol, interval, lookback_days=730): # 24 months
    """Fetch paginated data from Binance"""
    print(f"📥 Fetching {lookback_days} days of {interval} data for {symbol}...")
    
    limit = 1000
    all_data = []
    end_time = int(time.time() * 1000)
    start_time = end_time - (lookback_days * 24 * 60 * 60 * 1000)
    
    # 5 calls max to avoid waiting too long (approx 5000 candles)
    # For 1h data: 24 * 730 = 17520 candles. We need 18 calls.
    # We'll maximize to 15 calls.
    
    current_start = start_time
    
    for i in range(20): # Max 20 pages
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol.replace('/', ''),
            'interval': interval,
            'limit': limit,
            'startTime': current_start,
            'endTime': end_time
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if not isinstance(data, list) or len(data) == 0:
                break
                
            all_data.extend(data)
            
            # Update cursor
            last_close_time = data[-1][6]
            current_start = last_close_time + 1
            
            if current_start >= end_time:
                break
                
            time.sleep(0.1) # Rate limit politeness
            
        except Exception as e:
            print(f"Error fetching chunk: {e}")
            break
            
    if not all_data:
        return pd.DataFrame()
        
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'v', 'ct', 'qav', 'nt', 'tbv', 'tqv', 'ig'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
        
    print(f"✅ Loaded {len(df)} candles for {symbol}")
    return df

def run_suite():
    print("="*60)
    print("🚀 24-MONTH COIN SCREENER (Top 10 Analysis)")
    print("="*60)
    
    # Candidate Coins
    coins = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
        'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT'
    ]
    
    # Define Strategies
    # We test two main strategies on ALL coins to find the best fit
    strategies_template = [
        {'type': 'SMA', 'interval': '4h', 'params': {'fast': 20, 'slow': 50}, 'name_suffix': 'Trend'},
        {'type': 'DIP', 'interval': '1h', 'params': {'drop_pct': 0.08}, 'name_suffix': 'Dip'}
    ]
    
    results = []
    
    for symbol in coins:
        print(f"\n🔎 Analyzing {symbol}...")
        
        # 1. Fetch Data (Optimized: Fetch once per coin)
        # We need 1h data for DIP and 4h for SMA. 
        # To simplify, we fetch 1h and resample for SMA? 
        # Or just fetch both. Let's fetch 1h and we can probably run SMA on 1h for this test or fetch 4h.
        # Let's fetch 1h data (high res) and use it for Dip. 
        # For SMA Trend, let's also use 1h but maybe longer periods? Or just fetch 4h. 
        # Fetching twice is safer for accuracy.
        
        # Test Dip (1h)
        df_1h = fetch_historical_klines(symbol, '1h', lookback_days=730)
        if not df_1h.empty:
            engine = FastBacktester(df_1h)
            
            # Run Dip
            res_dip = engine.run_dip_strategy(drop_pct=0.08, fee_rate=0.00075) # BNB Fee
            results.append({
                'Symbol': symbol,
                'Strategy': 'Buy-the-Dip',
                'Profit': res_dip['total_profit'],
                'WinRate': res_dip['win_rate'],
                'Trades': res_dip['trade_count']
            })
            
        # Test Trend (4h)
        df_4h = fetch_historical_klines(symbol, '4h', lookback_days=730)
        if not df_4h.empty:
            engine = FastBacktester(df_4h)
            
            # SMA 20/50
            sma_fast = calculate_sma(df_4h['close'].values, period=20)
            sma_slow = calculate_sma(df_4h['close'].values, period=50)
            engine.add_indicator('sma_fast', sma_fast)
            engine.add_indicator('sma_slow', sma_slow)
            
            res_sma = engine.run_sma_strategy('sma_fast', 'sma_slow', fee_rate=0.00075) # BNB Fee
            results.append({
                'Symbol': symbol,
                'Strategy': 'SMA Trend',
                'Profit': res_sma['total_profit'],
                'WinRate': res_sma['win_rate'],
                'Trades': res_sma['trade_count']
            })

    # Validation Report
    print("\n" + "="*60)
    print("🏆 COIN PERFORMANCE RANKING (Net Profit on $1000)")
    print("="*60)
    res_df = pd.DataFrame(results)
    
    # Sort by Profit
    res_df = res_df.sort_values(by='Profit', ascending=False)
    
    print(res_df.to_string(index=False))
    
    print("\n" + "="*60)
    
if __name__ == "__main__":
    run_suite()
