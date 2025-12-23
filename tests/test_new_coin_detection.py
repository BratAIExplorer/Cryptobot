import os
import sys
import json
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# CRITICAL: Import AFTER patching or ensure class is patched in its defined module
from core.engine import TradingEngine

def test_new_coin_logic():
    print("🧪 Testing New Coin Detection Logic...")
    
    # Setup paths
    test_json = os.path.join(root_dir, "data", "test_known_symbols.json")
    
    # Mock symbols
    mock_curr = [{"symbol": "BTC/USDT", "active": True}, 
                 {"symbol": "ETH/USDT", "active": True}, 
                 {"symbol": "NEWCOIN/USDT", "active": True}]
    
    # Mocking exchange to avoid network
    with patch('core.exchange_unified.ccxt.mexc'), \
         patch('core.engine.TradeLogger'), \
         patch('core.engine.FundamentalAnalyzer') as mock_fund_class, \
         patch('confluence_engine.ConfluenceEngine') as mock_ce_class, \
         patch('core.engine.datetime') as mock_date:
        
        # Setup mock date
        mock_date.now.return_value = datetime(2025, 12, 23, 10, 30, 0)
        
        # Mocking managers
        mock_rm = MagicMock()
        mock_res = MagicMock()
        mock_rd = MagicMock()
        mock_vm = MagicMock()
        mock_fa = mock_fund_class.return_value
        
        # Setup fundamental mock behaviors
        mock_fa.analyze_new_listing_fundamentals.return_value = {'volume_status': 'EXPLOSIVE'}
        mock_fa.get_fundamental_score.return_value = 15
        
        # Mock Confluence Engine
        mock_ce = mock_ce_class.return_value
        mock_ce.get_automated_confluence_score.return_value = {
            'scores': {'fundamental': {'score': 0}, 'raw_total': 80, 'final_total': 80, 'final_recommendation': 'BUY'},
            'regime': {'multiplier': 1.0}
        }

        # Initialize engine (skip_load=True is now supported via implementation change but here we use injection)
        engine = TradingEngine(
            mode='paper', 
            exchange='MEXC',
            risk_manager=mock_rm,
            resilience_manager=mock_res,
            regime_detector=mock_rd,
            veto_manager=mock_vm,
            fundamental_analyzer=mock_fa
        )
        
        # Override exchange methods to return mock data
        engine.exchange.fetch_markets = MagicMock(return_value=mock_curr)
        engine.exchange.fetch_ohlcv = MagicMock(return_value=pd.DataFrame({'close': [100]}))
        engine.known_symbols_path = test_json
        
        # Create test known symbols file
        with open(test_json, 'w') as f:
            json.dump(["BTC/USDT", "ETH/USDT"], f)
            
        # Run monitor
        engine._run_market_monitor()
        
        print("✅ Detection cycle completed.")
        
        # Verify persistence
        if os.path.exists(test_json):
            with open(test_json, 'r') as f:
                updated = json.load(f)
                print(f"Updated known symbols: {updated}")
                if "NEWCOIN/USDT" in updated:
                    print("✅ Symbol persisted correctly.")
                else:
                    print("❌ Symbol NOT persisted.")
            os.remove(test_json)
        else:
            print("❌ Persistence file not found.")

if __name__ == "__main__":
    test_new_coin_logic()
