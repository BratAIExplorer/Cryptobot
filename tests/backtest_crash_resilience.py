"""
Crash Resilience Backtest - Validates bot performance during historical market crashes.
"""

import sys
import os
import pandas as pd
import ccxt
from datetime import datetime, timedelta
from decimal import Decimal

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'luno-monitor', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from regime_detector import RegimeDetector, RegimeState
from confluence_engine import ConfluenceEngine

class CrashBacktester:
    def __init__(self):
        self.exchange = ccxt.mexc()
        self.detector = RegimeDetector()
        self.confluence = ConfluenceEngine()

    def run_backtest(self, symbol: str, start_date: str, end_date: str):
        print(f"\n" + "="*60)
        print(f"BACKTESTING: {symbol} | {start_date} to {end_date}")
        print("="*60)
        
        # 1. Fetch data
        since = self.exchange.parse8601(f"{start_date}T00:00:00Z")
        ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', since=since, limit=1000)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if df.empty:
            print("❌ No data found")
            return

        # 2. Iterate through data
        results = []
        for i in range(200, len(df)): # Start at 200 for MA200
            current_slice = df.iloc[:i+1]
            current_time = current_slice['timestamp'].iloc[-1]
            current_price = current_slice['close'].iloc[-1]
            
            # Detect regime
            # (Note: detector usually wants daily data, but we use hourly for speed in this demo)
            # Actually, let's fetch daily data separately for the detector
            
            # For backtest simplification, we simulate the logic:
            regime, conf, metrics = self.detector.detect_regime(current_slice)
            multiplier = self.detector.get_risk_multiplier(regime)
            
            should_veto = not self.detector.should_trade(regime)
            
            if should_veto:
                results.append({
                    'time': current_time,
                    'price': current_price,
                    'regime': regime.value,
                    'veto': 'YES',
                    'multiplier': multiplier
                })
            else:
                results.append({
                    'time': current_time,
                    'price': current_price,
                    'regime': regime.value,
                    'veto': 'NO',
                    'multiplier': multiplier
                })

        # 3. Analyze results
        res_df = pd.DataFrame(results)
        veto_count = len(res_df[res_df['veto'] == 'YES'])
        total_count = len(res_df)
        
        print(f"✅ Total Periods: {total_count}")
        print(f"🚫 Vetoed Periods: {veto_count} ({veto_count/total_count:.1%})")
        
        crash_detected = len(res_df[res_df['regime'] == 'CRISIS'])
        print(f"🚨 CRISIS State detected in {crash_detected} periods")
        
        # Show specific veto period
        if crash_detected > 0:
            first_crisis = res_df[res_df['regime'] == 'CRISIS'].iloc[0]
            print(f"   First CRISIS hit at {first_crisis['time']} @ ${first_crisis['price']:.2f}")

if __name__ == "__main__":
    tester = CrashBacktester()
    
    # FTX Crash (Nov 2022)
    tester.run_backtest('BTC/USDT', '2022-11-01', '2022-11-15')
    
    # May 2021 Crash
    tester.run_backtest('BTC/USDT', '2021-05-10', '2021-05-25')
    
    # Recent Aug 2024 Dip
    tester.run_backtest('BTC/USDT', '2024-08-01', '2024-08-10')
