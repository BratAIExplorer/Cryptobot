"""
verification test for MEXC New Coin Detection
"""
import os
import sys
import json
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from core.engine import TradingEngine

def test_new_coin_logic():
    print("🧪 Testing New Coin Detection Logic...")
    
    # Initialize engine in paper mode
    engine = TradingEngine(mode='paper', exchange='MEXC')
    
    # Mock symbols
    mock_known = ["BTC/USDT", "ETH/USDT"]
    mock_curr = [{"symbol": "BTC/USDT", "active": True}, 
                 {"symbol": "ETH/USDT", "active": True}, 
                 {"symbol": "NEWCOIN/USDT", "active": True}]
    
    # Setup paths
    test_json = os.path.join(root_dir, "data", "test_known_symbols.json")
    engine.known_symbols_path = test_json
    
    try:
        # Create test known symbols file
        with open(test_json, 'w') as f:
            json.dump(mock_known, f)
            
        # Mock exchange.fetch_markets
        engine.exchange.fetch_markets = MagicMock(return_value=mock_curr)
        # Mock fetch_ohlcv for BTC
        engine.exchange.fetch_ohlcv = MagicMock(return_value=pd.DataFrame({'close': [100]}))
        
        # Override timing check in _run_market_monitor for testing
        with patch('core.engine.datetime') as mock_date:
            mock_date.now.return_value = datetime(2025, 12, 23, 10, 30, 0)
            engine._run_market_monitor()
            
        print("✅ Detection cycle completed (check console output for 'Detected 1 new listings')")
        
        # Verify persistence
        with open(test_json, 'r') as f:
            updated = json.load(f)
            print(f"Updated known symbols: {updated}")
            if "NEWCOIN/USDT" in updated:
                print("✅ Symbol persisted correctly.")
            else:
                print("❌ Symbol NOT persisted.")
                
    finally:
        if os.path.exists(test_json):
            os.remove(test_json)

if __name__ == "__main__":
    test_new_coin_logic()
