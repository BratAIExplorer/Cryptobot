"""
Transaction Parser Module
Parses Luno transaction history to calculate accurate buy prices
"""
from typing import Dict, List, Tuple
from datetime import datetime
import re

class TransactionParser:
    """Parse Luno transactions to calculate accurate cost basis"""
    
    def __init__(self, luno_client):
        """
        Initialize transaction parser
        
        Args:
            luno_client: Instance of LunoClient
        """
        self.luno_client = luno_client
    
    def get_orders_for_coin(self, coin: str) -> List[Dict]:
        """
        Get all completed orders for a specific coin
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            List of order dictionaries
        """
        try:
            pair = self.luno_client.config.CRYPTO_PAIRS.get(coin)
            if not pair:
                return []
            
            # Get completed orders
            response = self.luno_client._make_request('listorders', params={
                'pair': pair,
                'state': 'COMPLETE'
            })
            
            orders = response.get('orders', [])
            
            # Filter for buy orders only
            buy_orders = [
                order for order in orders 
                if order.get('type') == 'BID'  # BID = Buy order
            ]
            
            return buy_orders
            
        except Exception as e:
            print(f"Warning: Could not fetch orders for {coin}: {e}")
            return []
    
    def calculate_weighted_average_buy_price(self, coin: str) -> Tuple[float, float, int, List[Dict]]:
        """
        Calculate weighted average buy price from actual order history
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            Tuple of (avg_buy_price, total_coins, num_orders, order_details)
        """
        orders = self.get_orders_for_coin(coin)
        
        if not orders:
            # Fallback to current price if no orders found
            print(f"No order history found for {coin}, using current price")
            return self._fallback_price(coin)
        
        total_cost = 0.0
        total_coins = 0.0
        order_details = []
        
        for order in orders:
            # Get order details
            base_amount = float(order.get('base', 0))  # Amount of crypto bought
            counter_amount = float(order.get('counter', 0))  # Amount of ZAR spent
            fee_base = float(order.get('fee_base', 0))  # Fee in crypto
            fee_counter = float(order.get('fee_counter', 0))  # Fee in ZAR
            
            # Calculate effective price including fees
            # Total cost = counter amount + fees in ZAR
            order_cost = counter_amount + fee_counter
            
            # Total coins received = base amount - fees in crypto
            coins_received = base_amount - fee_base
            
            if coins_received > 0:
                price_per_coin = order_cost / coins_received
                
                total_cost += order_cost
                total_coins += coins_received
                
                order_details.append({
                    'timestamp': order.get('creation_timestamp'),
                    'amount': coins_received,
                    'price': price_per_coin,
                    'total_cost': order_cost,
                    'fee_zar': fee_counter,
                    'fee_crypto': fee_base
                })
        
        if total_coins > 0:
            avg_buy_price = total_cost / total_coins
            return (avg_buy_price, total_coins, len(orders), order_details)
        else:
            return self._fallback_price(coin)
    
    def _fallback_price(self, coin: str) -> Tuple[float, float, int, List[Dict]]:
        """Fallback to current price if no order history"""
        pair = self.luno_client.config.CRYPTO_PAIRS.get(coin)
        if not pair:
            return (0.0, 0.0, 0, [])
        
        try:
            ticker = self.luno_client.get_ticker(pair)
            balances = self.luno_client.get_balances()
            
            current_price = ticker['last_trade']
            balance = balances.get(coin, {}).get('balance', 0.0)
            
            return (current_price, balance, 0, [])
        except:
            return (0.0, 0.0, 0, [])
    
    def print_buy_summary(self, coin: str):
        """
        Print detailed buy summary for a coin
        
        Args:
            coin: Cryptocurrency symbol
        """
        avg_price, total_coins, num_orders, order_details = self.calculate_weighted_average_buy_price(coin)
        
        print(f"\n{'='*60}")
        print(f"{coin} BUY HISTORY")
        print(f"{'='*60}")
        print(f"Total Coins Bought: {total_coins:.8f}")
        print(f"Number of Orders: {num_orders}")
        print(f"Average Buy Price: R {avg_price:,.2f}")
        print(f"\nOrder Details:")
        print(f"{'-'*60}")
        
        for i, order in enumerate(order_details, 1):
            timestamp = datetime.fromtimestamp(int(order['timestamp']) / 1000)
            print(f"\nOrder {i} - {timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Amount: {order['amount']:.8f} {coin}")
            print(f"  Price: R {order['price']:,.2f} per {coin}")
            print(f"  Total Cost: R {order['total_cost']:,.2f}")
            print(f"  Fee (ZAR): R {order['fee_zar']:,.2f}")
            print(f"  Fee ({coin}): {order['fee_crypto']:.8f}")
        
        print(f"\n{'='*60}")


if __name__ == "__main__":
    # Test transaction parser
    import sys
    sys.path.append('..')
    
    from luno_client import LunoClient
    
    print("Testing Transaction Parser...")
    
    client = LunoClient()
    parser = TransactionParser(client)
    
    # Test with XRP (user's largest holding)
    parser.print_buy_summary('XRP')
