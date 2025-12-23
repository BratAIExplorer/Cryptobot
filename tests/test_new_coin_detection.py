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
    
    # Setup paths
    test_json = os.path.join(root_dir, "data", "test_known_symbols.json")
    
    # Mock symbols
    mock_known = ["BTC/USDT", "ETH/USDT"]
    mock_curr = [{"symbol": "BTC/USDT", "active": True}, 
                 {"symbol": "ETH/USDT", "active": True}, 
                 {"symbol": "NEWCOIN/USDT", "active": True}]
    
    with patch('core.engine.UnifiedExchange') as mock_unified, \
         patch('core.engine.TradeLogger') as mock_logger, \
         patch('core.engine.FundamentalAnalyzer') as mock_fund, \
         patch('confluence_engine.ConfluenceEngine') as mock_c_engine, \
         patch('core.engine.datetime') as mock_date:
        
        # Setup mock date
        mock_date.now.return_value = datetime(2025, 12, 23, 10, 30, 0)
        
        # Setup mock dependencies
        mock_rm = MagicMock()
        mock_res = MagicMock()
        mock_rd = MagicMock()
        mock_vm = MagicMock()
        mock_fa = mock_fund.return_value
        
        # Setup mock exchange
        instance = mock_unified.return_value
        instance.fetch_markets.return_value = mock_curr
        instance.fetch_ohlcv.return_value = pd.DataFrame({'close': [100]})
        instance.exchange_name = 'MEXC'
        
        # Setup mock confluence engine result
        mock_ce_instance = mock_c_engine.return_value
        mock_ce_instance.get_automated_confluence_score.return_value = {
            'scores': {'fundamental': {'score': 0}, 'raw_total': 80, 'final_total': 0},
            'regime': {'multiplier': 1.0}
        }
        
        # Setup fundamental mock
        mock_fa.analyze_new_listing_fundamentals.return_value = {'volume_status': 'EXPLOSIVE'}
        mock_fa.get_fundamental_score.return_value = 15

        # Initialize engine with mocked dependencies
        engine = TradingEngine(
            mode='paper', 
            exchange='MEXC',
            risk_manager=mock_rm,
            resilience_manager=mock_res,
            regime_detector=mock_rd,
            veto_manager=mock_vm,
            fundamental_analyzer=mock_fa
        )
        engine.known_symbols_path = test_json
        
        # Create test known symbols file
        with open(test_json, 'w') as f:
            json.dump(mock_known, f)
            
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

if __name__ == "__main__":
    test_new_coin_logic()
