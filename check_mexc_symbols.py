import ccxt
import pandas as pd

def check_mexc_symbols():
    print("Checking MEXC symbols...")
    mexc = ccxt.mexc()
    markets = mexc.load_markets()
    symbols = list(markets.keys())
    
    targets = ['MATIC/USDT', 'POL/USDT', 'EOS/USDT', 'THETA/USDT', 'VET/USDT', 'SAND/USDT', 'MANA/USDT']
    for t in targets:
        match = [s for s in symbols if t in s]
        print(f"Target {t}: {'Found' if match else 'NOT FOUND'} (Matches: {match})")
        
    # Check for fragments
    for t in ['MATIC', 'POL', 'EOS', 'THETA']:
        matches = [s for s in symbols if t in s and '/USDT' in s]
        print(f"Fragment {t}: {matches[:3]}")

if __name__ == "__main__":
    check_mexc_symbols()
