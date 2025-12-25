"""
Luno API Client Module
Handles all interactions with Luno Exchange API (READ-ONLY)
"""
import requests
import base64
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config

class LunoClient:
    """Client for interacting with Luno API"""
    
    def __init__(self):
        """Initialize Luno API client with read-only credentials"""
        self.api_key_id = config.LUNO_API_KEY_ID
        self.api_key_secret = config.LUNO_API_KEY_SECRET
        self.base_url = config.LUNO_BASE_URL
        self.session = requests.Session()
        
        # Set up authentication header
        credentials = f"{self.api_key_id}:{self.api_key_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Luno API
        
        Args:
            endpoint: API endpoint (e.g., 'listorders')
            params: Query parameters
        
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Luno API credentials. Please check your API key.")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please wait before making more requests.")
            else:
                raise ValueError(f"Luno API error: {e}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error connecting to Luno: {e}")
    
    def get_balances(self) -> Dict[str, Dict]:
        """
        Get account balances for all cryptocurrencies
        
        Returns:
            Dictionary mapping coin symbol to balance info
        """
        response = self._make_request('balance')
        balances = {}
        
        for balance in response.get('balance', []):
            asset = balance['asset']
            # Map Luno asset codes to our symbols
            if asset == 'XBT':
                asset = 'BTC'
            
            if asset in config.CRYPTO_PAIRS:
                balances[asset] = {
                    'balance': float(balance['balance']),
                    'reserved': float(balance['reserved']),
                    'available': float(balance['balance']) - float(balance['reserved'])
                }
        
        return balances
    
    def get_transactions(self, account_id: str, min_row: int = -1000, max_row: int = 0) -> List[Dict]:
        """
        Get transaction history for a specific account
        
        Args:
            account_id: Luno account ID
            min_row: Minimum row number (negative for recent)
            max_row: Maximum row number (0 for most recent)
        
        Returns:
            List of transaction dictionaries
        """
        params = {
            'id': account_id,
            'min_row': min_row,
            'max_row': max_row
        }
        
        response = self._make_request('accounts/{}/transactions'.format(account_id), params)
        return response.get('transactions', [])
    
    def get_all_accounts(self) -> List[Dict]:
        """
        Get all account IDs for the user
        
        Returns:
            List of account dictionaries
        """
        balances = self._make_request('balance')
        accounts = []
        
        for balance in balances.get('balance', []):
            asset = balance['asset']
            if asset == 'XBT':
                asset = 'BTC'
            
            if asset in config.CRYPTO_PAIRS:
                accounts.append({
                    'asset': asset,
                    'account_id': balance.get('account_id'),
                    'balance': float(balance['balance'])
                })
        
        return accounts
    
    def get_buy_transactions(self, coin: str) -> List[Dict]:
        """
        Get all buy transactions for a specific cryptocurrency
        
        Args:
            coin: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            List of buy transaction dictionaries with amount, price, and fees
        """
        # Get account ID for this coin
        accounts = self.get_all_accounts()
        account_id = None
        
        for account in accounts:
            if account['asset'] == coin:
                account_id = account['account_id']
                break
        
        if not account_id:
            return []
        
        # Get transactions
        all_transactions = self.get_transactions(account_id)
        
        # Filter for buy transactions
        buy_transactions = []
        for txn in all_transactions:
            # Look for credit transactions (buys)
            if float(txn.get('balance_delta', 0)) > 0:
                buy_transactions.append({
                    'timestamp': txn.get('timestamp'),
                    'amount': float(txn.get('balance_delta', 0)),
                    'description': txn.get('description', ''),
                    'balance': float(txn.get('balance', 0))
                })
        
        return buy_transactions
    
    def get_ticker(self, pair: str) -> Dict:
        """
        Get current ticker price for a trading pair
        
        Args:
            pair: Trading pair (e.g., 'XBTZAR')
        
        Returns:
            Ticker information including last_trade, bid, ask
        """
        response = self._make_request('ticker', params={'pair': pair})
        return {
            'last_trade': float(response.get('last_trade', 0)),
            'bid': float(response.get('bid', 0)),
            'ask': float(response.get('ask', 0)),
            'timestamp': response.get('timestamp')
        }
    
    def get_fee_info(self, pair: str) -> Dict:
        """
        Get fee information for a trading pair
        
        Args:
            pair: Trading pair (e.g., 'XBTZAR')
        
        Returns:
            Fee information including maker and taker fees
        """
        response = self._make_request('fee_info', params={'pair': pair})
        return {
            'maker_fee': float(response.get('maker_fee', config.ESTIMATED_MAKER_FEE)),
            'taker_fee': float(response.get('taker_fee', config.ESTIMATED_TAKER_FEE)),
            'thirty_day_volume': float(response.get('thirty_day_volume', 0))
        }
    
    def calculate_average_buy_price(self, coin: str) -> Tuple[float, float, int]:
        """
        Calculate average buy price for a cryptocurrency including fees
        Uses account transaction history to capture both Exchange and Instant Buy orders
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            Tuple of (average_price, total_amount, transaction_count)
        """
        # 1. Get Account ID for this coin
        accounts = self.get_all_accounts()
        account_id = None
        for acc in accounts:
            if acc['asset'] == coin:
                account_id = acc['account_id']
                break
        
        if not account_id:
            return (0.0, 0.0, 0)
            
        try:
            # 2. Get transactions (last 100 should cover recent history)
            # For a full history, we might need to paginate, but let's start with 100
            transactions = self.get_transactions(account_id, min_row=-100, max_row=0)
            
            total_cost = 0.0
            total_coins = 0.0
            buy_count = 0
            
            for txn in transactions:
                # Look for EXCHANGE type transactions (Instant Buy or Market Buy)
                # Positive balance delta means we received coins
                delta = float(txn.get('balance_delta', 0))
                
                if delta > 0 and txn.get('kind') == 'EXCHANGE':
                    # Try to get details from detail_fields
                    details = txn.get('detail_fields', {}).get('trade_details', {})
                    
                    if details:
                        price = float(details.get('price', 0))
                        volume = float(details.get('volume', 0))
                        
                        if price > 0 and volume > 0:
                            cost = price * volume
                            total_cost += cost
                            total_coins += volume
                            buy_count += 1
                    else:
                        # Fallback: Parse description "Bought X XRP/MYR @ Y"
                        desc = txn.get('description', '')
                        if 'Bought' in desc and '@' in desc:
                            try:
                                parts = desc.split('@')
                                price_part = parts[1].strip()
                                price = float(price_part)
                                
                                # Volume is delta (approx, excluding fee)
                                # But delta is net of fee, so let's use that for conservative calc
                                cost = price * delta
                                total_cost += cost
                                total_coins += delta
                                buy_count += 1
                            except:
                                pass

            if total_coins > 0:
                avg_price = total_cost / total_coins
                return (avg_price, total_coins, buy_count)
            else:
                # Fallback to current price if no history found
                pair = config.CRYPTO_PAIRS.get(coin)
                if pair:
                    ticker = self.get_ticker(pair)
                    balances = self.get_balances()
                    return (ticker['last_trade'], balances.get(coin, {}).get('balance', 0), 0)
                return (0.0, 0.0, 0)
                
        except Exception as e:
            print(f"Warning: Could not fetch transaction history for {coin}: {e}")
            # Fallback
            return (0.0, 0.0, 0)
    
    def calculate_target_prices(self, avg_buy_price: float, coin: str) -> Dict[float, float]:
        """
        Calculate target sell prices for different profit percentages
        
        Args:
            avg_buy_price: Average price at which coin was bought
            coin: Cryptocurrency symbol
        
        Returns:
            Dictionary mapping profit percentage to target sell price
        """
        pair = config.CRYPTO_PAIRS.get(coin)
        if not pair:
            return {}
        
        # Get fee info
        try:
            fee_info = self.get_fee_info(pair)
            sell_fee = fee_info['taker_fee']  # Assume selling as taker
        except:
            sell_fee = config.ESTIMATED_TAKER_FEE
        
        # FIX: If avg_buy_price is 0 or invalid, use current market price as fallback
        # This prevents "Target Price: RM 0.00" alerts when transaction history is unavailable
        if avg_buy_price <= 0.001:  # Essentially zero or invalid
            try:
                ticker = self.get_ticker(pair)
                avg_buy_price = ticker['last_trade']
                print(f\"Warning: Using current price as fallback for {coin} target calculation (no buy history found)\")
            except:
                # If we can't get current price either, return empty targets
                print(f\"Error: Cannot calculate targets for {coin} - no buy price or current price available\")
                return {}
        
        targets = {}
        for profit_pct in config.PROFIT_TARGETS:
            # Calculate price needed to achieve target profit after fees
            # Formula: target_price = avg_buy_price * (1 + profit_pct/100) / (1 - sell_fee)
            target_price = avg_buy_price * (1 + profit_pct / 100) / (1 - sell_fee)
            targets[profit_pct] = target_price
        
        return targets
    
    def test_connection(self) -> bool:
        """
        Test if API credentials are valid
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._make_request('balance')
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


if __name__ == "__main__":
    # Test the Luno client
    print("Testing Luno API connection...")
    
    try:
        client = LunoClient()
        
        if client.test_connection():
            print("✓ Successfully connected to Luno API")
            
            # Get balances
            balances = client.get_balances()
            print(f"\n✓ Found balances for {len(balances)} cryptocurrencies:")
            for coin, balance in balances.items():
                print(f"  {coin}: {balance['balance']:.8f}")
            
            # Test ticker for BTC
            if 'BTC' in config.CRYPTO_PAIRS:
                ticker = client.get_ticker(config.CRYPTO_PAIRS['BTC'])
                print(f"\n✓ BTC/ZAR Price: R {ticker['last_trade']:,.2f}")
        else:
            print("✗ Failed to connect to Luno API")
            print("Please check your API credentials in .env file")
    
    except Exception as e:
        print(f"✗ Error: {e}")
