"""
Coin Classifier - Pillar C: Hybrid Watchlist
Classifies coins as Type A/B/C based on age across all exchanges
"""
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

class CoinClassifier:
    """
    Determines coin age and classification using CoinGecko API
    
    Type A: <30 days old (Brand New)
    Type B: 90-180 days old (Emerging)
    Type C: 180+ days old (Established)
    """
    
    # CoinGecko Free API (no key needed, 10-30 calls/min)
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    # Cache to avoid repeated API calls
    CACHE_FILE = None
    _cache = {}
    
    def __init__(self, logger=None):
        """
        Initialize classifier
        
        Args:
            logger: Optional TradeLogger instance
        """
        self.logger = logger
        
        # Setup cache file
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.CACHE_FILE = os.path.join(root_dir, 'data', 'coin_age_cache.json')
        os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
        
        # Load cache
        self._load_cache()
    
    def _load_cache(self):
        """Load coin age cache from disk"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    self._cache = json.load(f)
                print(f"[CLASSIFIER] Loaded cache with {len(self._cache)} entries")
            except Exception as e:
                print(f"[CLASSIFIER] Error loading cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        """Save coin age cache to disk"""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            print(f"[CLASSIFIER] Error saving cache: {e}")
    
    def _search_coin(self, symbol: str) -> Optional[str]:
        """
        Search for coin ID on CoinGecko
        
        Args:
            symbol: Base coin symbol (e.g., "BTC" from "BTC/USDT")
            
        Returns:
            CoinGecko coin ID or None
        """
        try:
            # Remove /USDT suffix if present
            base_symbol = symbol.split('/')[0].lower()
            
            # Search API
            url = f"{self.COINGECKO_API}/search"
            params = {'query': base_symbol}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get('coins', [])
            
            if not coins:
                return None
            
            # Try exact symbol match first
            for coin in coins:
                if coin.get('symbol', '').lower() == base_symbol:
                    return coin.get('id')
            
            # Fallback to first result
            return coins[0].get('id')
            
        except Exception as e:
            print(f"[CLASSIFIER] Error searching for {symbol}: {e}")
            return None
    
    def get_coin_age_days(self, symbol: str) -> Optional[int]:
        """
        Get coin age in days since first listing anywhere
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            
        Returns:
            Age in days or None if not found
        """
        base_symbol = symbol.split('/')[0]
        
        # Check cache first (valid for 24 hours)
        cache_key = base_symbol.lower()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cache_time = datetime.fromisoformat(cached['cached_at'])
            if datetime.utcnow() - cache_time < timedelta(hours=24):
                return cached['age_days']
        
        # Search for coin
        coin_id = self._search_coin(symbol)
        if not coin_id:
            print(f"[CLASSIFIER] Coin not found on CoinGecko: {symbol}")
            return None
        
        try:
            # Get coin data
            url = f"{self.COINGECKO_API}/coins/{coin_id}"
            params = {'localization': 'false', 'tickers': 'false', 'community_data': 'false', 'developer_data': 'false'}
            
            time.sleep(1.2)  # Rate limit: ~50 calls/min
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get genesis date
            genesis_date_str = data.get('genesis_date')
            if not genesis_date_str:
                # Fallback: use ICO date or listing date
                genesis_date_str = data.get('ico_data', {}).get('ico_start_date')
            
            if not genesis_date_str:
                print(f"[CLASSIFIER] No genesis date for {symbol}")
                return None
            
            # Calculate age
            genesis_date = datetime.strptime(genesis_date_str, '%Y-%m-%d')
            age_days = (datetime.utcnow() - genesis_date).days
            
            # Cache result
            self._cache[cache_key] = {
                'age_days': age_days,
                'genesis_date': genesis_date_str,
                'cached_at': datetime.utcnow().isoformat()
            }
            self._save_cache()
            
            return age_days
            
        except Exception as e:
            print(f"[CLASSIFIER] Error getting age for {symbol}: {e}")
            return None
    
    def classify_coin(self, symbol: str) -> Dict:
        """
        Classify coin as Type A/B/C based on age
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            
        Returns:
            Dict with classification results
        """
        print(f"[CLASSIFIER] Classifying {symbol}...")
        
        age_days = self.get_coin_age_days(symbol)
        
        if age_days is None:
            # Unknown coin - treat as Type A (most conservative)
            return {
                'symbol': symbol,
                'type': 'A',
                'age_days': None,
                'classification': 'BRAND_NEW (Unknown)',
                'risk_level': 'EXTREME',
                'waiting_period_days': 60,
                'error': 'Coin not found on CoinGecko'
            }
        
        # Classify based on age
        if age_days < 30:
            coin_type = 'A'
            classification = 'BRAND_NEW'
            risk_level = 'EXTREME'
            waiting_period = 60  # 60 day wait for brand new coins
        elif age_days < 90:
            coin_type = 'A'  # Still brand new category
            classification = 'VERY_NEW'
            risk_level = 'HIGH'
            waiting_period = 30
        elif age_days < 180:
            coin_type = 'B'
            classification = 'EMERGING'
            risk_level = 'MEDIUM'
            waiting_period = 14 # Shorter wait for proven coins
        else:
            coin_type = 'C'
            classification = 'ESTABLISHED'
            risk_level = 'LOW'
            waiting_period = 0 if age_days > 365 else 7  # Can fast-track if >1 year
        
        result = {
            'symbol': symbol,
            'type': coin_type,
            'age_days': age_days,
            'classification': classification,
            'risk_level': risk_level,
            'waiting_period_days': waiting_period,
            'first_listed': (datetime.utcnow() - timedelta(days=age_days)).strftime('%Y-%m-%d')
        }
        
        print(f"[CLASSIFIER] {symbol} → Type {coin_type} ({classification}, {age_days} days old)")
        
        return result


if __name__ == "__main__":
    """
    Standalone testing
    """
    print("Testing CoinClassifier...\n")
    
    classifier = CoinClassifier()
    
    # Test various coins
    test_symbols = [
        "BTC/USDT",   # Should be Type C (established)
        "ETH/USDT",   # Should be Type C
        "SOL/USDT",   # Should be Type C
    ]
    
    for symbol in test_symbols:
        result = classifier.classify_coin(symbol)
        print(f"\n{symbol}:")
        print(f"  Type: {result['type']}")
        print(f"  Age: {result['age_days']} days")
        print(f"  Classification: {result['classification']}")
        print(f"  Risk: {result['risk_level']}")
        print(f"  Waiting period: {result['waiting_period_days']} days")
        print(f"  First listed: {result.get('first_listed', 'Unknown')}")
        print()
