"""
CryptoIntel Hub - Fundamental Analyzer
Extracts fundamental and macro context for new coin listings
"""

import logging
from typing import Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """
    Analyzes 'Fundamental' signals for coins, especially new listings.
    Uses proxies like volume growth, sector strength, and social sentiment.
    """
    
    def __init__(self, exchange=None, logger_instance=None):
        self.exchange = exchange
        self.logger = logger_instance
        
    def analyze_new_listing_fundamentals(self, symbol: str) -> Dict:
        """
        Gathers fundamental context for a new listing.
        Since deep fundamental data (whitepapers, team) is hard to automate,
        we use 'Market Fundamentals' as proxies.
        """
        analysis = {
            'symbol': symbol,
            'sector': self._detect_sector(symbol),
            'volume_status': 'UNKNOWN',
            'sentiment_proxy': 50,  # Neutral default
            'market_cap_tier': 'UNKNOWN'
        }
        
        if self.exchange:
            try:
                # 1. Volume Growth Analysis (Crucial for new coins)
                # Fetch 5m or 15m data to see initial burst
                df_short = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=12) # last hour
                if not df_short.empty:
                    current_vol = df_short['volume'].iloc[-1]
                    avg_vol = df_short['volume'].mean()
                    
                    if current_vol > avg_vol * 2:
                        analysis['volume_status'] = 'EXPLOSIVE'
                    elif current_vol > avg_vol:
                        analysis['volume_status'] = 'GROWING'
                    else:
                        analysis['volume_status'] = 'STABLE'
                
                # 2. Buy/Sell Ratio Proxy (Using ticker)
                ticker = self.exchange.fetch_ticker(symbol)
                if ticker and ticker.get('bid') and ticker.get('ask'):
                    # Spread as a proxy for liquidity/interest
                    spread = (ticker['ask'] - ticker['bid']) / ticker['bid']
                    analysis['spread_pct'] = float(spread * 100)
            except Exception as e:
                logger.error(f"Error in fundamental analysis for {symbol}: {e}")
                
        return analysis

    def _detect_sector(self, symbol: str) -> str:
        """Categorize coin into a sector based on symbol or lookups"""
        base = symbol.split('/')[0].upper()
        
        # Simple mapping for known categories
        sectors = {
            'MEME': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WIF'],
            'AI': ['FET', 'AGIX', 'OCEAN', 'RNDR', 'NEAR'],
            'L1/L2': ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'OP', 'ARB'],
            'DEFI': ['UNI', 'AAVE', 'LINK', 'SNX', 'MKR'],
            'GAMING': ['GALA', 'IMX', 'AXS', 'SAND', 'MANA']
        }
        
        for sector, coins in sectors.items():
            if base in coins:
                return sector
        return 'UNKNOWN'

    def get_fundamental_score(self, analysis: Dict) -> int:
        """Convert analysis into a score (0-20 points)"""
        score = 0
        
        # Volume (Max 10)
        vol_points = {
            'EXPLOSIVE': 10,
            'GROWING': 7,
            'STABLE': 4,
            'UNKNOWN': 2
        }
        score += vol_points.get(analysis['volume_status'], 0)
        
        # Sector/Market Cap (Placeholder for now, max 10)
        # In a real scenario, we'd boost coins in 'Hot' sectors
        score += 5 # Base fundamental score for being listed on MEXC (filtered)
        
        return min(20, score)
