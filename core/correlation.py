"""
CryptoIntel Hub - Correlation Manager
Calculates correlation matrix between assets to prevent concentrated risk.
"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from typing import List, Dict, Tuple

class CorrelationManager:
    def __init__(self, update_interval_hours=24):
        self.correlation_matrix = pd.DataFrame()
        self.last_update = datetime.min
        self.update_interval = update_interval_hours
        self.data_cache = {}
        # Hard limit: If correlation > 0.85, we consider them "The Same Asset"
        self.CORRELATION_THRESHOLD = 0.85 

    def _fetch_price_history(self, symbol: str, limit=100) -> pd.Series:
        """Fetch daily closing prices for correlation calc"""
        try:
            # Using Binance Public API (No auth needed for market data)
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol.replace('/', ''),
                'interval': '1d',
                'limit': limit
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if not isinstance(data, list):
                return pd.Series()
                
            # Parse: [time, open, high, low, close, ...]
            # We only need Close for correlation
            closes = [float(x[4]) for x in data]
            return pd.Series(closes)
            
        except Exception as e:
            print(f"[Correlation] Error fetching {symbol}: {e}")
            return pd.Series()

    def update_correlations(self, active_symbols: List[str]):
        """
        Re-calculate the correlation matrix for all active symbols.
        Should be called periodically (e.g., daily).
        """
        # Only update if stale
        time_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        if time_since_update < self.update_interval and not self.correlation_matrix.empty:
            return

        print(f"🔄 Updating Correlation Matrix for {len(active_symbols)} symbols...")
        price_data = {}
        
        # Always include BTC as a baseline
        all_symbols = set(active_symbols)
        all_symbols.add('BTC/USDT') 
        
        for sym in all_symbols:
            series = self._fetch_price_history(sym)
            if not series.empty:
                # Store by clean symbol name
                price_data[sym] = series
        
        # Create DataFrame
        df = pd.DataFrame(price_data)
        
        if df.empty:
            print("⚠️ Correlation update failed: No data")
            return

        # Calculate Matrix (Pearson)
        self.correlation_matrix = df.corr(method='pearson')
        self.last_update = datetime.now()
        print(f"✅ Correlation Matrix Updated ({len(df.columns)}x{len(df.columns)})")

    def check_correlation_risk(self, new_symbol: str, current_positions: List[str]) -> Tuple[bool, str]:
        """
        Check if new_symbol is too correlated with anything we ALREADY hold.
        
        Returns:
            (is_risky, reason)
        """
        if self.correlation_matrix.empty:
            # Fail safe: If no data, allow trade but warn
            self.update_correlations(current_positions + [new_symbol])
            if self.correlation_matrix.empty:
                return False, "No correlation data available (Fail Open)"

        if new_symbol not in self.correlation_matrix.columns:
            # Try to fetch just this one if missing
            self.update_correlations(current_positions + [new_symbol])
            if new_symbol not in self.correlation_matrix.columns:
                 return False, f"Symbol {new_symbol} not in correlation matrix"

        # Check against every held position
        for held_symbol in current_positions:
            if held_symbol == new_symbol:
                continue # Ignore self
                
            if held_symbol in self.correlation_matrix.columns:
                corr = self.correlation_matrix.loc[new_symbol, held_symbol]
                
                if corr > self.CORRELATION_THRESHOLD:
                    return True, f"Highly correlated ({corr:.2f}) with held position {held_symbol}"

        return False, "Correlation check passed"

    def get_correlation(self, sym_a, sym_b):
        """Get correlation between two specific assets"""
        if sym_a in self.correlation_matrix.columns and sym_b in self.correlation_matrix.columns:
            return self.correlation_matrix.loc[sym_a, sym_b]
        return 0.0

if __name__ == "__main__":
    # Quick Test
    cm = CorrelationManager()
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'USDT/USDT'] # USDT should be 0 or Error
    
    cm.update_correlations(symbols)
    print("\n--- Correlation Matrix ---")
    print(cm.correlation_matrix)
    
    # Test Check
    risky, reason = cm.check_correlation_risk('ETH/USDT', ['BTC/USDT'])
    print(f"\nBuying ETH while holding BTC? Risky: {risky} ({reason})")
    
    risky, reason = cm.check_correlation_risk('XRP/USDT', ['BTC/USDT'])
    print(f"Buying XRP while holding BTC? Risky: {risky} ({reason})")
