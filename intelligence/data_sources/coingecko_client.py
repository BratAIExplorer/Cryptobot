import requests
import time
import logging

class CoinGeckoClient:
    """
    Client for fetching live market data from CoinGecko.
    Used to automate 'Market Position' scoring components.
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Mapping symbols to CoinGecko IDs
    COIN_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'XRP': 'ripple',
        'SOL': 'solana',
        'ADA': 'cardano',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'LINK': 'chainlink',
        'DOGE': 'dogecoin',
        'LTC': 'litecoin'
    }

    def __init__(self):
        self.logger = logging.getLogger("CoinGeckoClient")

    def get_market_data(self, symbol):
        """
        Fetch market data for a given symbol (e.g., 'XRP').
        Returns dict with price, mcap_rank, volume, etc.
        """
        coin_id = self.COIN_MAP.get(symbol.upper())
        if not coin_id:
            self.logger.error(f"Symbol {symbol} not found in COIN_MAP")
            return None

        url = f"{self.BASE_URL}/coins/{coin_id}"
        
        try:
            # Add simple rate limiting
            time.sleep(1.2) 
            
            response = requests.get(url, params={
                "localization": "false",
                "tickers": "false",
                "community_data": "true",
                "developer_data": "true",
                "sparkline": "false"
            })
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'price_usd': market_data.get('current_price', {}).get('usd'),
                    'market_cap_rank': data.get('market_cap_rank'),
                    'ath_change_percentage': market_data.get('ath_change_percentage', {}).get('usd'),
                    'price_change_24h': market_data.get('price_change_24h'),
                    'developer_score': data.get('developer_score'),
                    'community_score': data.get('community_score')
                }
            else:
                self.logger.error(f"Failed to fetch data for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Exception fetching {symbol}: {e}")
            return None

    def get_batch_prices(self, symbols):
        """
        Fetch simple prices for multiple coins to save API calls.
        """
        ids = [self.COIN_MAP.get(s.upper()) for s in symbols if self.COIN_MAP.get(s.upper())]
        if not ids:
            return {}
            
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ",".join(ids),
            "vs_currencies": "usd"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Batch fetch error: {e}")
            
        return {}

if __name__ == "__main__":
    # Test Script
    print("🔬 Testing CoinGecko API Connection...")
    client = CoinGeckoClient()
    
    # Test 1: Fetch XRP
    print("\n1. Fetching XRP Data...")
    xrp_data = client.get_market_data("XRP")
    if xrp_data:
        print(f"   ✅ Success: Price ${xrp_data['price_usd']}, Rank #{xrp_data['market_cap_rank']}")
    else:
        print("   ❌ Failed to fetch XRP.")

    # Test 2: Fetch BTC
    print("\n2. Fetching BTC Data...")
    btc_data = client.get_market_data("BTC")
    if btc_data:
        print(f"   ✅ Success: Price ${btc_data['price_usd']}, Rank #{btc_data['market_cap_rank']}")
    else:
        print("   ❌ Failed to fetch BTC.")
