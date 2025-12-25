"""
Data Sources Package

Collects fundamental data for regulatory scoring:
- GitHub: Developer activity, commit frequency
- ETF Flows: Institutional money flows
- News: Sentiment from CryptoPanic
- Partnerships: Corporate/institutional announcements
"""

__all__ = [
    'GitHubCollector',
    'ETFScraper',
    'NewsCollector',
    'PartnershipTracker',
]
