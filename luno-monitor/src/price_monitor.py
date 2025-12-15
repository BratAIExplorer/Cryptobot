"""
Price Monitoring Module
Fetches live cryptocurrency prices from multiple sources
"""
import requests
import time
from typing import Dict, Optional
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import config
from src.luno_client import LunoClient

class PriceMonitor:
    """Monitor cryptocurrency prices from multiple sources"""
    
    def __init__(self):
        """Initialize price monitoring with multiple data sources"""
        self.luno_client = LunoClient()
        self.coingecko_client = CoinGeckoAPI()
        self.price_history = {coin: [] for coin in config.CRYPTO_PAIRS.keys()}
        self.last_prices = {}
    
    def get_luno_price(self, coin: str) -> Optional[float]:
        """
        Get current price from Luno (primary source)
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            Current price in MYR or None if error
        """
        try:
            pair = config.CRYPTO_PAIRS.get(coin)
            if not pair:
                return None
            
            ticker = self.luno_client.get_ticker(pair)
            return ticker['last_trade']
        except Exception as e:
            print(f"Error fetching Luno price for {coin}: {e}")
            return None
    
    def get_coingecko_price(self, coin: str) -> Optional[float]:
        """
        Get current price from CoinGecko (backup source)
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            Current price in MYR or None if error
        """
        try:
            coin_id = config.COINGECKO_IDS.get(coin)
            if not coin_id:
                return None
            
            # Get price in MYR from CoinGecko
            price_data = self.coingecko_client.get_price(
                ids=coin_id,
                vs_currencies='myr'
            )
            
            return price_data[coin_id]['myr']
        except Exception as e:
            print(f"Error fetching CoinGecko price for {coin}: {e}")
            return None
    
    def get_current_price(self, coin: str) -> Optional[float]:
        """
        Get current price with fallback logic
        Primary: Luno, Backup: CoinGecko
        
        Args:
            coin: Cryptocurrency symbol
        
        Returns:
            Current price in MYR
        """
        # Try Luno first (most accurate for your exchange)
        price = self.get_luno_price(coin)
        
        # Fallback to CoinGecko if Luno fails
        if price is None:
            price = self.get_coingecko_price(coin)
        
        # Store price in history
        if price is not None:
            self.price_history[coin].append({
                'timestamp': datetime.now(),
                'price': price
            })
            
            # Keep only last 1000 prices per coin
            if len(self.price_history[coin]) > 1000:
                self.price_history[coin] = self.price_history[coin][-1000:]
            
            self.last_prices[coin] = price
        
        return price
    
    def get_all_prices(self) -> Dict[str, float]:
        """
        Get current prices for all monitored cryptocurrencies
        
        Returns:
            Dictionary mapping coin symbol to current price
        """
        prices = {}
        
        for coin in config.CRYPTO_PAIRS.keys():
            price = self.get_current_price(coin)
            if price is not None:
                prices[coin] = price
        
        return prices
    
    def calculate_profit_loss(self, coin: str, avg_buy_price: float, current_price: float) -> Dict:
        """
        Calculate profit/loss metrics
        
        Args:
            coin: Cryptocurrency symbol
            avg_buy_price: Average price at which coin was bought
            current_price: Current market price
        
        Returns:
            Dictionary with profit/loss metrics
        """
        if avg_buy_price == 0:
            return {
                'profit_loss_myr': 0,
                'profit_loss_percent': 0,
                'status': 'unknown'
            }
        
        profit_loss_percent = ((current_price - avg_buy_price) / avg_buy_price) * 100
        profit_loss_myr = current_price - avg_buy_price
        
        status = 'profit' if profit_loss_percent > 0 else 'loss' if profit_loss_percent < 0 else 'break_even'
        
        return {
            'profit_loss_myr': profit_loss_myr,
            'profit_loss_percent': profit_loss_percent,
            'status': status
        }
    
    def detect_price_alerts(self, coin: str, current_price: float, target_prices: Dict[float, float]) -> list:
        """
        Detect if any price alerts should be triggered
        
        Args:
            coin: Cryptocurrency symbol
            current_price: Current market price
            target_prices: Dictionary of profit percentage to target price
        
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        # Check if any profit targets are reached
        for profit_pct, target_price in target_prices.items():
            if current_price >= target_price:
                alerts.append({
                    'type': 'target_reached',
                    'coin': coin,
                    'profit_pct': profit_pct,
                    'target_price': target_price,
                    'current_price': current_price,
                    'message': f"🎯 {coin} reached {profit_pct}% profit target! Current: RM{current_price:,.2f}, Target: RM{target_price:,.2f}"
                })
        
        # Check for significant price drops
        if coin in self.last_prices:
            last_price = self.last_prices[coin]
            price_change_pct = ((current_price - last_price) / last_price) * 100
            
            if price_change_pct <= -config.ALERT_ON_PRICE_DROP_PERCENT:
                alerts.append({
                    'type': 'price_drop',
                    'coin': coin,
                    'drop_pct': abs(price_change_pct),
                    'current_price': current_price,
                    'previous_price': last_price,
                    'message': f"⚠️ {coin} dropped {abs(price_change_pct):.2f}%! From RM{last_price:,.2f} to RM{current_price:,.2f}"
                })
        
        return alerts
    
    def get_price_trend(self, coin: str, hours: int = 24) -> Dict:
        """
        Analyze price trend over specified time period
        
        Args:
            coin: Cryptocurrency symbol
            hours: Number of hours to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        if coin not in self.price_history or len(self.price_history[coin]) < 2:
            return {'trend': 'unknown', 'change_pct': 0}
        
        history = self.price_history[coin]
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        # Filter prices within time window
        recent_prices = [p for p in history if p['timestamp'].timestamp() >= cutoff_time]
        
        if len(recent_prices) < 2:
            return {'trend': 'unknown', 'change_pct': 0}
        
        first_price = recent_prices[0]['price']
        last_price = recent_prices[-1]['price']
        
        change_pct = ((last_price - first_price) / first_price) * 100
        
        if change_pct > 2:
            trend = 'up'
        elif change_pct < -2:
            trend = 'down'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_pct': change_pct,
            'first_price': first_price,
            'last_price': last_price,
            'high': max(p['price'] for p in recent_prices),
            'low': min(p['price'] for p in recent_prices)
        }


if __name__ == "__main__":
    # Test price monitoring
    print("Testing Price Monitor...")
    
    monitor = PriceMonitor()
    
    print("\nFetching current prices for all cryptocurrencies...")
    prices = monitor.get_all_prices()
    
    for coin, price in prices.items():
        print(f"{coin}: RM {price:,.2f}")
    
    print(f"\n✓ Successfully fetched prices for {len(prices)} cryptocurrencies")
