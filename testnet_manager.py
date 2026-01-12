"""
CryptoBots V3 - Binance Testnet Manager
Handles Binance Testnet integration for safe testing with fake money.
"""

import ccxt
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class TestnetManager:
    """
    Manages Binance Testnet connections and trading.
    Testnet = Real API calls + Real market data + Fake money
    """
    
    # Binance Spot Testnet URL
    TESTNET_API_URL = 'https://testnet.binance.vision/api'
    
    def __init__(self):
        """Initialize testnet manager."""
        self.testnet_key = os.getenv('BINANCE_TESTNET_API_KEY', '')
        self.testnet_secret = os.getenv('BINANCE_TESTNET_API_SECRET', '')
        self.exchange = None
    
    def get_exchange(self, mode: str = 'testnet') -> Optional[ccxt.Exchange]:
        """
        Get exchange instance based on mode.
        
        Args:
            mode: 'paper', 'testnet', or 'live'
            
        Returns:
            CCXT exchange instance
        """
        if mode == 'paper':
            # Paper trading - no real API calls
            return self._get_paper_exchange()
        
        elif mode == 'testnet':
            # Binance Testnet - real API, fake money
            return self._get_testnet_exchange()
        
        elif mode == 'live':
            # Live trading - real money!
            return self._get_live_exchange()
        
        return None
    
    def _get_paper_exchange(self) -> ccxt.Exchange:
        """Get paper trading exchange (no real API)."""
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        return exchange
    
    def _get_testnet_exchange(self) -> Optional[ccxt.Exchange]:
        """Get Binance Testnet exchange."""
        if not self.testnet_key or not self.testnet_secret:
            print("⚠️ Testnet API keys not configured")
            return None
        
        try:
            exchange = ccxt.binance({
                'apiKey': self.testnet_key,
                'secret': self.testnet_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                },
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            })
            
            # Test connection
            exchange.load_markets()
            print("✅ Binance Testnet connected successfully")
            return exchange
            
        except Exception as e:
            print(f"❌ Testnet connection failed: {e}")
            return None
    
    def _get_live_exchange(self) -> Optional[ccxt.Exchange]:
        """Get live Binance exchange (REAL MONEY!)."""
        live_key = os.getenv('BINANCE_API_KEY', '')
        live_secret = os.getenv('BINANCE_API_SECRET', '')
        
        if not live_key or not live_secret:
            print("⚠️ Live API keys not configured")
            return None
        
        try:
            exchange = ccxt.binance({
                'apiKey': live_key,
                'secret': live_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            exchange.load_markets()
            print("✅ Binance LIVE connected (REAL MONEY MODE)")
            return exchange
            
        except Exception as e:
            print(f"❌ Live connection failed: {e}")
            return None
    
    def get_testnet_balance(self) -> Dict:
        """Get testnet account balance."""
        exchange = self._get_testnet_exchange()
        if not exchange:
            return {}
        
        try:
            balance = exchange.fetch_balance()
            return balance
        except Exception as e:
            print(f"⚠️ Failed to fetch testnet balance: {e}")
            return {}
    
    def get_wallet_summary(self, mode: str = 'testnet') -> Dict:
        """
        Get wallet summary with all balances.
        
        Args:
            mode: Trading mode
            
        Returns:
            Dictionary with wallet balances
        """
        exchange = self.get_exchange(mode)
        if not exchange:
            return {'total_usd': 0, 'balances': {}}
        
        try:
            balance = exchange.fetch_balance()
            
            # Extract non-zero balances
            balances = {}
            total_usd = 0
            
            for currency, amount in balance['total'].items():
                if amount > 0:
                    balances[currency] = {
                        'total': amount,
                        'free': balance['free'].get(currency, 0),
                        'used': balance['used'].get(currency, 0)
                    }
                    
                    # Try to get USD value
                    if currency != 'USDT' and currency != 'USD':
                        try:
                            ticker = exchange.fetch_ticker(f"{currency}/USDT")
                            usd_value = amount * ticker['last']
                            balances[currency]['usd_value'] = usd_value
                            total_usd += usd_value
                        except:
                            balances[currency]['usd_value'] = 0
                    else:
                        total_usd += amount
                        balances[currency]['usd_value'] = amount
            
            return {
                'total_usd': total_usd,
                'balances': balances,
                'mode': mode
            }
            
        except Exception as e:
            print(f"⚠️ Failed to fetch wallet summary: {e}")
            return {'total_usd': 0, 'balances': {}, 'error': str(e)}
    
    def test_connection(self, mode: str = 'testnet') -> bool:
        """
        Test exchange connection.
        
        Args:
            mode: Trading mode to test
            
        Returns:
            True if connection successful
        """
        exchange = self.get_exchange(mode)
        if not exchange:
            return False
        
        try:
            # Try fetching ticker
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"✅ {mode.upper()} connection test passed")
            print(f"   BTC/USDT: ${ticker['last']:,.2f}")
            return True
        except Exception as e:
            print(f"❌ {mode.upper()} connection test failed: {e}")
            return False
    
    @staticmethod
    def get_testnet_setup_instructions() -> str:
        """Get instructions for setting up Binance Testnet."""
        return """
🔧 Binance Testnet Setup Instructions:

1. Visit: https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key" 
3. Save your API Key and Secret Key
4. Add to your .env file:
   
   BINANCE_TESTNET_API_KEY=your_testnet_key_here
   BINANCE_TESTNET_API_SECRET=your_testnet_secret_here

5. Restart the bot

Note: Testnet gives you fake USDT for testing!
"""


# Quick test function
def main():
    """Test testnet connection."""
    manager = TestnetManager()
    
    print("=" * 60)
    print("🧪 Testing Binance Testnet Connection")
    print("=" * 60)
    
    # Test connection
    if manager.test_connection('testnet'):
        # Get wallet summary
        wallet = manager.get_wallet_summary('testnet')
        print(f"\n💼 Testnet Wallet Balance: ${wallet['total_usd']:,.2f}")
        
        for currency, data in wallet['balances'].items():
            print(f"   {currency}: {data['total']:.8f} (${data.get('usd_value', 0):,.2f})")
    else:
        print("\n" + TestnetManager.get_testnet_setup_instructions())


if __name__ == '__main__':
    main()
