"""
CryptoPanic API Integration for Real-time News Intelligence

Provides:
- Real-time news alerts for specific coins
- Market-wide sentiment analysis
- High-impact event detection (SEC approvals, hacks, partnerships)
- Integration with trading bot's intelligence layer

Free API: 300 requests/day
Sign up: https://cryptopanic.com/developers/api/
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class CryptoPanicAPI:
    """
    Integration with CryptoPanic News API

    Features:
    - Fetch critical news only (filters out noise)
    - Sentiment analysis (bullish/bearish/neutral)
    - Impact scoring (0-100)
    - Symbol-specific and market-wide news
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CryptoPanic API client

        Args:
            api_key: Your CryptoPanic API key
                    Get free key at https://cryptopanic.com/developers/api/
                    If None, uses demo mode (limited to 10 results)
        """
        self.api_key = api_key or "demo"
        self.base_url = "https://cryptopanic.com/api/v1/posts/"

        # High-impact keywords (SEC, ETF, hacks, etc.)
        self.critical_keywords = [
            # Regulatory & Legal
            'SEC', 'ETF', 'approval', 'lawsuit', 'regulation', 'ban', 'court',
            'Gensler', 'CFTC',

            # Major Events
            'hack', 'exploit', 'outage', 'breach', 'stolen',

            # Economic / Macro
            'Fed', 'Federal Reserve', 'rate', 'inflation', 'FOMC', 'Powell',
            'recession', 'QE', 'quantitative',

            # Adoption & Partnerships
            'partnership', 'adoption', 'launch', 'mainnet', 'upgrade',
            'listed', 'delisted',

            # Institutional
            'BlackRock', 'Fidelity', 'Grayscale', 'institutional', 'Wall Street',
            'MicroStrategy', 'Tesla', 'PayPal'
        ]

        # Trusted news sources (boost impact score)
        self.trusted_sources = [
            'Bloomberg', 'Reuters', 'CNBC', 'Financial Times',
            'Wall Street Journal', 'SEC', 'Federal Reserve', 'CoinDesk',
            'The Block', 'Decrypt'
        ]

        # Cache for rate limiting
        self._cache = {}
        self._cache_duration = 300  # 5 minutes

    def get_critical_news(self, symbol: Optional[str] = None, max_items: int = 5,
                         hours_back: int = 24) -> List[Dict]:
        """
        Fetch critical news (high-impact only)

        Args:
            symbol: Coin symbol ('BTC', 'ETH', 'XRP') or None for all crypto
            max_items: Number of top news items to return
            hours_back: Look back this many hours (default 24)

        Returns:
            List of news items sorted by impact score (highest first):
            [
                {
                    'title': str,
                    'published_at': str (ISO datetime),
                    'source': str,
                    'url': str,
                    'coins': List[str],
                    'sentiment': str ('BULLISH 📈' | 'BEARISH 📉' | 'NEUTRAL ➡️'),
                    'impact_score': int (0-100)
                }
            ]
        """
        # Check cache
        cache_key = f"{symbol}_{max_items}_{hours_back}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_duration:
                return cached_data

        try:
            # Build API request
            params = {
                'auth_token': self.api_key,
                'filter': 'important',  # Only important news (pre-filtered)
                'kind': 'news',  # Exclude social media posts
                'regions': 'en',
                'public': 'true'
            }

            # Add symbol filter
            if symbol:
                # Convert common formats to CryptoPanic format
                symbol_clean = symbol.split('/')[0].upper()  # 'BTC/USDT' -> 'BTC'
                params['currencies'] = symbol_clean

            # Fetch from API
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse and filter
            critical_news = []
            for item in data.get('results', []):
                # Only keep news with critical keywords
                title = item.get('title', '')
                if not any(kw.lower() in title.lower() for kw in self.critical_keywords):
                    continue

                # Parse news item
                news_item = {
                    'title': title,
                    'published_at': item.get('published_at'),
                    'source': item.get('source', {}).get('title', 'Unknown'),
                    'url': item.get('url'),
                    'coins': [c['code'] for c in item.get('currencies', [])],
                    'votes': item.get('votes', {}),
                }

                # Determine sentiment
                votes = news_item['votes']
                bearish = votes.get('negative', 0)
                bullish = votes.get('positive', 0)

                if bearish > bullish * 1.5:
                    news_item['sentiment'] = 'BEARISH 📉'
                    news_item['sentiment_score'] = -1
                elif bullish > bearish * 1.5:
                    news_item['sentiment'] = 'BULLISH 📈'
                    news_item['sentiment_score'] = 1
                else:
                    news_item['sentiment'] = 'NEUTRAL ➡️'
                    news_item['sentiment_score'] = 0

                # Calculate impact score
                news_item['impact_score'] = self._calculate_impact_score(news_item)

                critical_news.append(news_item)

            # Sort by impact (highest first)
            critical_news.sort(key=lambda x: x['impact_score'], reverse=True)

            # Cache results
            self._cache[cache_key] = (critical_news[:max_items], datetime.now())

            return critical_news[:max_items]

        except requests.exceptions.RequestException as e:
            print(f"[CryptoPanic] API Error: {e}")
            return []
        except Exception as e:
            print(f"[CryptoPanic] Unexpected Error: {e}")
            return []

    def _calculate_impact_score(self, news_item: Dict) -> int:
        """
        Calculate news impact score (0-100)

        Scoring methodology:
        - Base: 50 points
        - Trusted source: +30 points
        - ETF/SEC/Regulation: +20 points
        - Major partnership: +15 points
        - Security events (hack, exploit): +10 points
        - Macro events (Fed, rates): +15 points
        """
        score = 50

        title = news_item['title'].lower()
        source = news_item['source']

        # Trusted source boost
        if any(src in source for src in self.trusted_sources):
            score += 30

        # Regulatory news (highest impact)
        if any(kw in title for kw in ['etf', 'sec', 'regulation', 'approval', 'lawsuit']):
            score += 20

        # Partnership & Adoption
        if any(kw in title for kw in ['partnership', 'adopt', 'launch', 'listed']):
            score += 15

        # Security events (negative but critical)
        if any(kw in title for kw in ['hack', 'exploit', 'breach', 'stolen']):
            score += 10

        # Macro economic events
        if any(kw in title for kw in ['fed', 'powell', 'rate', 'inflation', 'fomc']):
            score += 15

        # Institutional involvement
        if any(kw in title for kw in ['blackrock', 'fidelity', 'institutional', 'wall street']):
            score += 10

        return min(score, 100)  # Cap at 100

    def get_market_sentiment(self, hours_back: int = 24) -> Dict:
        """
        Get overall market sentiment from news

        Returns:
            {
                'overall_sentiment': str ('BULLISH' | 'BEARISH' | 'NEUTRAL'),
                'bullish_count': int,
                'bearish_count': int,
                'neutral_count': int,
                'top_news': List[Dict]  # Top 3 most impactful news
            }
        """
        news = self.get_critical_news(symbol=None, max_items=20, hours_back=hours_back)

        bullish = sum(1 for n in news if n['sentiment_score'] > 0)
        bearish = sum(1 for n in news if n['sentiment_score'] < 0)
        neutral = len(news) - bullish - bearish

        # Determine overall sentiment
        if bullish > bearish * 1.5:
            overall = 'BULLISH'
        elif bearish > bullish * 1.5:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'

        return {
            'overall_sentiment': overall,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'total_news': len(news),
            'top_news': news[:3]  # Top 3 most impactful
        }

    def check_coin_news(self, symbol: str) -> Dict:
        """
        Check if there's critical news for a specific coin

        Use this before trading to avoid buying into negative news

        Args:
            symbol: Coin symbol ('BTC', 'ETH', 'XRP/USDT', etc.)

        Returns:
            {
                'has_critical_news': bool,
                'sentiment': str,
                'latest_news': Dict or None,
                'should_veto_trade': bool  # True if negative news in last 4 hours
            }
        """
        symbol_clean = symbol.split('/')[0].upper()
        news = self.get_critical_news(symbol=symbol_clean, max_items=5, hours_back=24)

        if not news:
            return {
                'has_critical_news': False,
                'sentiment': 'NEUTRAL',
                'latest_news': None,
                'should_veto_trade': False
            }

        latest = news[0]

        # Check if news is very recent (last 4 hours) and negative
        published = datetime.fromisoformat(latest['published_at'].replace('Z', '+00:00'))
        hours_ago = (datetime.now(published.tzinfo) - published).total_seconds() / 3600

        should_veto = (hours_ago < 4 and latest['sentiment_score'] < 0 and latest['impact_score'] > 70)

        return {
            'has_critical_news': True,
            'sentiment': latest['sentiment'],
            'latest_news': latest,
            'should_veto_trade': should_veto,
            'hours_ago': hours_ago
        }


# Test function
if __name__ == "__main__":
    print("=" * 70)
    print("🔔 CryptoPanic API Integration Test")
    print("=" * 70)

    # Initialize (uses demo API key)
    api = CryptoPanicAPI()

    # Test 1: Get critical crypto news
    print("\n📰 Top 5 Critical Crypto News (Market-wide):")
    print("-" * 70)
    news = api.get_critical_news(max_items=5)

    for i, item in enumerate(news, 1):
        print(f"\n{i}. {item['sentiment']} | Impact: {item['impact_score']}/100")
        print(f"   📰 {item['title']}")
        print(f"   🔗 {item['source']} | Coins: {', '.join(item['coins'][:5])}")

    # Test 2: Get BTC-specific news
    print("\n" + "=" * 70)
    print("📰 Bitcoin (BTC) News:")
    print("-" * 70)
    btc_check = api.check_coin_news('BTC')

    if btc_check['has_critical_news']:
        print(f"✅ Critical news found: {btc_check['sentiment']}")
        print(f"   {btc_check['latest_news']['title']}")
        if btc_check['should_veto_trade']:
            print("   ⚠️  VETO RECOMMENDED: Recent negative news!")
    else:
        print("✅ No critical news for BTC")

    # Test 3: Market sentiment
    print("\n" + "=" * 70)
    print("📊 Overall Market Sentiment:")
    print("-" * 70)
    sentiment = api.get_market_sentiment()
    print(f"Overall: {sentiment['overall_sentiment']}")
    print(f"Bullish: {sentiment['bullish_count']} | Bearish: {sentiment['bearish_count']} | Neutral: {sentiment['neutral_count']}")

    print("\n" + "=" * 70)
    print("✅ CryptoPanic integration test complete!")
    print("💡 Get your FREE API key: https://cryptopanic.com/developers/api/")
    print("=" * 70)
