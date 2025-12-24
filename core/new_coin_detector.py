"""
New Coin Detector - Pillar C: Hybrid Watchlist
Detects new USDT listings on MEXC exchange
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Set

class NewCoinDetector:
    def __init__(self, exchange, logger):
        """
        Initialize detector
        
        Args:
            exchange: UnifiedExchange instance
            logger: TradeLogger instance
        """
        self.exchange = exchange
        self.logger = logger
        
        # Path to known symbols persistence
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.known_symbols_path = os.path.join(root_dir, 'data', 'known_symbols_mexc.json')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.known_symbols_path), exist_ok=True)
    
    def load_known_symbols(self) -> Set[str]:
        """Load previously seen symbols from disk"""
        if os.path.exists(self.known_symbols_path):
            try:
                with open(self.known_symbols_path, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"[DETECTOR] Error loading known symbols: {e}")
                return set()
        return set()
    
    def save_known_symbols(self, symbols: Set[str]):
        """Persist known symbols to disk"""
        try:
            with open(self.known_symbols_path, 'w') as f:
                json.dump(sorted(list(symbols)), f, indent=2)
            print(f"[DETECTOR] Saved {len(symbols)} known symbols")
        except Exception as e:
            print(f"[DETECTOR] Error saving known symbols: {e}")
    
    def fetch_current_listings(self) -> List[Dict]:
        """
        Fetch all active USDT pairs from MEXC
        
        Returns:
            List of market dicts with symbol, active status, etc.
        """
        try:
            markets = self.exchange.fetch_markets()
            
            if not markets:
                print("[DETECTOR] Warning: fetch_markets() returned an empty list.")
                return []

            # Filter for USDT pairs for spot trading
            # Note: We don't filter by 'active' because MEXC sometimes reports all markets as inactive
            usdt_pairs = [
                m for m in markets 
                if m.get('quote') == 'USDT' 
                and m.get('type') == 'spot'
            ]
            
            if not usdt_pairs and markets:
                print(f"[DETECTOR] Warning: Found {len(markets)} total markets, but 0 passed USDT/Spot filter.")
                print(f"[DETECTOR] Sample market data: {markets[0] if markets else 'None'}")

            print(f"[DETECTOR] Found {len(usdt_pairs)} active USDT pairs on MEXC")
            return usdt_pairs
            
        except Exception as e:
            print(f"[DETECTOR] Error fetching markets: {e}")
            return []
    
    def detect_new_listings(self) -> List[str]:
        """
        Main detection logic: compare current vs known symbols
        
        Returns:
            List of newly detected symbols
        """
        print(f"\n{'='*60}")
        print(f"🔍 [DETECTOR] Scanning MEXC for new listings...")
        print(f"{'='*60}")
        
        # Load known symbols
        known_symbols = self.load_known_symbols()
        print(f"[DETECTOR] Known symbols: {len(known_symbols)}")
        
        # Fetch current listings
        current_markets = self.fetch_current_listings()
        if not current_markets:
            print("[DETECTOR] No markets fetched, skipping scan")
            return []
        
        # Extract current symbols
        current_symbols = {m['symbol'] for m in current_markets}
        
        # Find new symbols
        new_symbols = current_symbols - known_symbols
        
        if new_symbols:
            print(f"✨ [DETECTOR] Detected {len(new_symbols)} new listings:")
            for symbol in sorted(new_symbols):
                print(f"   - {symbol}")
            
            # Update known symbols
            updated_symbols = known_symbols.union(current_symbols)
            self.save_known_symbols(updated_symbols)
        else:
            print(f"[DETECTOR] No new listings detected")
        
        print(f"{'='*60}\n")
        return sorted(list(new_symbols))
    
    def get_listing_metadata(self, symbol: str) -> Dict:
        """
        Get basic metadata for a newly listed symbol
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            
        Returns:
            Dict with metadata (price, volume, etc.)
        """
        try:
            # Fetch ticker data
            ticker = self.exchange.fetch_ticker(symbol)
            
            metadata = {
                'symbol': symbol,
                'price': ticker.get('last', 0),
                'volume_24h': ticker.get('quoteVolume', 0),
                'price_change_24h_pct': ticker.get('percentage', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'detected_at': datetime.utcnow().isoformat(),
            }
            
            return metadata
            
        except Exception as e:
            print(f"[DETECTOR] Error fetching metadata for {symbol}: {e}")
            return {
                'symbol': symbol,
                'price': 0,
                'volume_24h': 0,
                'detected_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def initialize_known_symbols(self):
        """
        One-time initialization: populate known_symbols.json with current listings
        Use this on first run or to reset the detector
        """
        print("[DETECTOR] Initializing known symbols from current MEXC listings...")
        
        current_markets = self.fetch_current_listings()
        if not current_markets:
            print("[DETECTOR] Failed to fetch markets for initialization")
            return
        
        current_symbols = {m['symbol'] for m in current_markets}
        self.save_known_symbols(current_symbols)
        
        print(f"[DETECTOR] Initialized with {len(current_symbols)} symbols")
        print(f"[DETECTOR] Detector is now ready to track new listings")


if __name__ == "__main__":
    """
    Standalone testing
    """
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.exchange_unified import UnifiedExchange
    from core.logger import TradeLogger
    
    print("Testing NewCoinDetector...\n")
    
    # Initialize dependencies
    exchange = UnifiedExchange(exchange_name='MEXC', mode='paper')
    logger = TradeLogger(mode='paper')
    
    # Create detector
    detector = NewCoinDetector(exchange, logger)
    
    # Check if this is first run
    if not os.path.exists(detector.known_symbols_path):
        print("First run detected. Initializing known symbols...")
        detector.initialize_known_symbols()
    else:
        # Run detection
        new_listings = detector.detect_new_listings()
        
        # Show metadata for new listings
        if new_listings:
            print(f"\nFetching metadata for {len(new_listings)} new listings...\n")
            for symbol in new_listings:
                metadata = detector.get_listing_metadata(symbol)
                print(f"Symbol: {symbol}")
                print(f"  Price: ${metadata.get('price', 0):.4f}")
                print(f"  Volume (24h): ${metadata.get('volume_24h', 0):,.0f}")
                print(f"  Change (24h): {metadata.get('price_change_24h_pct', 0):+.2f}%")
                print()
