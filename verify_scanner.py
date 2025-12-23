import os
import sys
import pandas as pd
from datetime import datetime

# Add paths
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'luno-monitor'))
sys.path.append(os.path.join(root_dir, 'luno-monitor', 'src'))

from core.exchange import ExchangeInterface
from confluence_engine import ConfluenceEngine
from config_coins import DISCOVERY_WATCHLIST

def test_scanner():
    print("🚀 Starting Confluence Scanner Verification...")
    
    # Initialize exchange (Paper mode for safety)
    exchange = ExchangeInterface(mode='paper')
    
    # Initialize engine
    db_path = os.path.join(root_dir, 'data', 'trades_v3_paper.db')
    c_engine = ConfluenceEngine(db_path=db_path, exchange_client=exchange)
    
    # Fetch BTC data for macro
    print("Fetching BTC macro data...")
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=200)
    if isinstance(ohlcv, pd.DataFrame) and ohlcv.empty:
        print("⚠️ Failed to fetch BTC data. Macro scores will be defaults.")
        btc_df = pd.DataFrame()
    elif not ohlcv:
        print("⚠️ Failed to fetch BTC data. Macro scores will be defaults.")
        btc_df = pd.DataFrame()
    else:
        btc_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Test 3 coins from discovery list
    test_coins = DISCOVERY_WATCHLIST[:3]
    print(f"Scanning test coins: {test_coins}")
    
    for symbol in test_coins:
        print(f"\nScanning {symbol}...")
        try:
            result = c_engine.get_automated_confluence_score(symbol, btc_df=btc_df)
            c_engine.print_confluence_report(result)
        except Exception as e:
            print(f"❌ Failed for {symbol}: {e}")
            import traceback
            traceback.print_exc()
        
    print("\n✅ Scanner verification complete.")

if __name__ == "__main__":
    test_scanner()
