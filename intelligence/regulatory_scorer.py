"""
Regulatory Scorer

Scores cryptocurrency assets based on regulatory/fundamental metrics instead of technical indicators.

Designed for assets like XRP, ADA, SOL where:
- Regulatory progress (lawsuits, ETFs) drives price more than RSI
- Institutional adoption matters more than SMA crossovers
- Development milestones are more important than volume spikes

Scoring Rubric (0-100 points):
- Regulatory Progress: 40 pts (SEC status, ETFs, global compliance)
- Institutional Adoption: 30 pts (Partnerships, integrations, holdings)
- Ecosystem Development: 20 pts (GitHub activity, network growth)
- Market Position: 10 pts (Price vs MA200, relative strength)
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import sqlite3
import json

from .config import (
    REGULATORY_WEIGHTS,
    REGULATORY_BREAKDOWN,
    INSTITUTIONAL_BREAKDOWN,
    ECOSYSTEM_BREAKDOWN,
    MARKET_BREAKDOWN,
    REGULATORY_SCORE_THRESHOLDS,
    INTELLIGENCE_DB_PATH,
    CACHE_TTLS,
)


class RegulatoryScorer:
    """
    Score regulatory/fundamental-driven assets.
    
    Philosophy:
    - XRP doesn't follow RSI - it follows lawsuits and ETF approvals
    - ADA doesn't care about SMA200 - it cares about Cardano Summit announcements
    - SOL doesn't trade on volume - it trades on ecosystem growth
    
    This scorer captures what ACTUALLY drives these assets.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize regulatory scorer.
        
        Args:
            db_path: Path to intelligence database (separate from bot DB)
        """
        self.db_path = db_path or INTELLIGENCE_DB_PATH
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Regulatory scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regulatory_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_score REAL,
                regulatory_score REAL,
                institutional_score REAL,
                ecosystem_score REAL,
                market_score REAL,
                recommendation TEXT,
                details_json TEXT,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        # API cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                expires_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_score(self, symbol: str, exchange_data: Optional[Dict] = None) -> Dict:
        """
        Calculate comprehensive regulatory score for an asset.
        
        Args:
            symbol: Trading pair (e.g., 'XRP/USDT')
            exchange_data: Optional market data from exchange (price, volume)
            
        Returns:
            {
                'symbol': 'XRP/USDT',
                'total_score': 70,
                'breakdown': {
                    'regulatory': 30,
                    'institutional': 22,
                    'ecosystem': 13,
                    'market': 5
                },
                'recommendation': 'BUY',
                'confidence': 'high',
                'details': { ... }
            }
        """
        # Calculate each pillar
        regulatory_score, regulatory_details = self._score_regulatory(symbol)
        institutional_score, institutional_details = self._score_institutional(symbol)
        ecosystem_score, ecosystem_details = self._score_ecosystem(symbol)
        market_score, market_details = self._score_market_position(symbol, exchange_data)
        
        # Total score
        total = regulatory_score + institutional_score + ecosystem_score + market_score
        total = max(0, min(100, total))  # Clamp to 0-100
        
        # Get recommendation
        recommendation = self._get_recommendation(total)
        
        # Determine confidence level
        confidence = self._calculate_confidence(
            regulatory_score, institutional_score, ecosystem_score, market_score
        )
        
        result = {
            'symbol': symbol,
            'total_score': round(total, 1),
            'breakdown': {
                'regulatory': round(regulatory_score, 1),
                'institutional': round(institutional_score, 1),
                'ecosystem': round(ecosystem_score, 1),
                'market': round(market_score, 1),
            },
            'recommendation': recommendation,
            'confidence': confidence,
            'details': {
                'regulatory': regulatory_details,
                'institutional': institutional_details,
                'ecosystem': ecosystem_details,
                'market': market_details,
            },
            'timestamp': datetime.now().isoformat(),
        }
        
        # Store in database
        self._save_score(result)
        
        return result
    
    def _score_regulatory(self, symbol: str) -> Tuple[float, Dict]:
        """
        Score regulatory progress (0-40 points).
        
        Metrics:
        - Legal status: SEC clarity, lawsuit resolution, compliance (15 pts)
        - ETF status: Approved ETFs, inflow trends (15 pts)
        - Global regulation: Approval in major jurisdictions (10 pts)
        """
        score = 0.0
        details = {}
        
        # Symbol-specific scoring (for now, will integrate data sources in Phase 2)
        base_symbol = symbol.split('/')[0]
        
        if base_symbol == 'XRP':
            # Legal Status (15 pts)
            # XRP: SEC lawsuit resolved favorably
            legal_score = 15.0
            details['legal_status'] = {
                'score': legal_score,
                'reason': 'SEC lawsuit resolved favorably (Ripple victory)',
                'sources': ['court_records', 'sec_filings']
            }
            score += legal_score
            
            # ETF Status (15 pts)
            # XRP: Multiple ETFs approved, moderate inflows
            etf_score = 10.0  # Approved but not massive inflows yet
            details['etf_status'] = {
                'score': etf_score,
                'reason': 'Multiple XRP ETFs approved, moderate inflows',
                'etfs': ['21Shares', 'Wisdom Tree', 'Bitwise'],
                'sources': ['sosovaluecom', 'etf_filings']
            }
            score += etf_score
            
            # Global Regulation (10 pts)
            # XRP: Mixed - strong in UAE, Japan; uncertain in EU
            global_score = 5.0
            details['global_regulation'] = {
                'score': global_score,
                'reason': 'Strong in UAE/Japan, uncertain in EU/UK',
                'jurisdictions': {
                    'UAE': 'approved',
                    'Japan': 'approved',
                    'EU': 'pending',
                    'UK': 'under_review'
                }
            }
            score += global_score
            
        elif base_symbol == 'ADA':
            # Cardano: No major lawsuit, but SEC classification concerns
            legal_score = 8.0
            details['legal_status'] = {
                'score': legal_score,
                'reason': 'No lawsuit, but potential security classification concerns',
                'sources': ['sec_statements']
            }
            score += legal_score
            
            # No ETF yet
            etf_score = 0.0
            details['etf_status'] = {
                'score': etf_score,
                'reason': 'No ADA ETF approved yet',
            }
            score += etf_score
            
            # Strong global presence (Ethiopia, academic partnerships)
            global_score = 8.0
            details['global_regulation'] = {
                'score': global_score,
                'reason': 'Strong presence in Africa, academic partnerships',
                'jurisdictions': {
                    'Ethiopia': 'partnership',
                    'Georgia': 'blockchain_partnership'
                }
            }
            score += global_score
            
        elif base_symbol == 'SOL':
            # Solana: SEC concerns (deemed security in some cases)
            legal_score = 5.0
            details['legal_status'] = {
                'score': legal_score,
                'reason': 'SEC concerns in some cases, but gaining clarity',
                'sources': ['sec_statements', 'exchange_listings']
            }
            score += legal_score
            
            # Multiple ETF filings pending
            etf_score = 5.0
            details['etf_status'] = {
                'score': etf_score,
                'reason': 'Multiple ETF filings pending approval',
                'filings': ['VanEck', '21Shares'],
            }
            score += etf_score
            
            # Strong institutional interest
            global_score = 7.0
            details['global_regulation'] = {
                'score': global_score,
                'reason': 'Gaining regulatory clarity globally',
            }
            score += global_score
            
        else:
            # Default scoring for other assets (conservative)
            legal_score = 5.0
            etf_score = 0.0
            global_score = 3.0
            details['legal_status'] = {'score': legal_score, 'reason': 'Default scoring - no specific intel'}
            details['etf_status'] = {'score': etf_score, 'reason': 'No ETF data available'}
            details['global_regulation'] = {'score': global_score, 'reason': 'Limited regulatory data'}
            score = legal_score + etf_score + global_score
        
        return min(score, 40.0), details
    
    def _score_institutional(self, symbol: str) -> Tuple[float, Dict]:
        """
        Score institutional adoption (0-30 points).
        
        Metrics:
        - Partnerships: Major banks, payment processors (15 pts)
        - Integration progress: Actual usage, deployed systems (10 pts)
        - Corporate holdings: Companies holding on balance sheet (5 pts)
        """
        score = 0.0
        details = {}
        
        base_symbol = symbol.split('/')[0]
        
        if base_symbol == 'XRP':
            # Partnerships (15 pts)
            partnership_score = 12.0
            details['partnerships'] = {
                'score': partnership_score,
                'reason': 'Major banking partnerships active',
                'partners': ['Hidden Road', 'UAE Central Bank', 'SBI Holdings'],
                'count': 3
            }
            score += partnership_score
            
            # Integration Progress (10 pts)
            integration_score = 8.0
            details['integration_progress'] = {
                'score': integration_score,
                'reason': 'RLUSD stablecoin launched, payments live',
                'milestones': ['RLUSD launch', 'XRP Ledger EVM sidechain development'],
            }
            score += integration_score
            
            # Corporate Holdings (5 pts)
            holdings_score = 2.0
            details['corporate_holdings'] = {
                'score': holdings_score,
                'reason': 'Limited corporate treasury holdings',
            }
            score += holdings_score
            
        elif base_symbol == 'ADA':
            partnership_score = 10.0
            details['partnerships'] = {
                'score': partnership_score,
                'reason': 'Government partnerships (Ethiopia education system)',
                'partners': ['Ethiopian Ministry of Education', 'University partnerships'],
            }
            score += partnership_score
            
            integration_score = 5.0
            details['integration_progress'] = {
                'score': integration_score,
                'reason': 'Hydra development ongoing, dApp ecosystem growing',
            }
            score += integration_score
            
            holdings_score = 1.0
            details['corporate_holdings'] = {
                'score': holdings_score,
                'reason': 'Minimal corporate holdings',
            }
            score += holdings_score
            
        elif base_symbol == 'SOL':
            partnership_score = 13.0
            details['partnerships'] = {
                'score': partnership_score,
                'reason': 'Strong VC backing, Visa/Shopify integrations',
                'partners': ['Visa', 'Shopify', 'Multicoin Capital', 'a16z'],
            }
            score += partnership_score
            
            integration_score = 9.0
            details['integration_progress'] = {
                'score': integration_score,
                'reason': 'Large dApp ecosystem, NFT marketplace dominance',
                'metrics': {'defi_tvl': 'high', 'nft_volume': 'top_3'},
            }
            score += integration_score
            
            holdings_score = 2.0
            details['corporate_holdings'] = {
                'score': holdings_score,
                'reason': 'Some VC holdings, limited corporate treasuries',
            }
            score += holdings_score
            
        else:
            # Default
            partnership_score = 3.0
            integration_score = 2.0
            holdings_score = 0.0
            details['partnerships'] = {'score': partnership_score, 'reason': 'Limited data'}
            details['integration_progress'] = {'score': integration_score, 'reason': 'Limited data'}
            details['corporate_holdings'] = {'score': holdings_score, 'reason': 'No data'}
            score = partnership_score + integration_score + holdings_score
        
        return min(score, 30.0), details
    
    def _score_ecosystem(self, symbol: str) -> Tuple[float, Dict]:
        """
        Score ecosystem development (0-20 points).
        
        Metrics:
        - Developer activity: GitHub commits, upgrades, dApps (10 pts)
        - Network growth: Transaction volume, active addresses (10 pts)
        """
        score = 0.0
        details = {}
        
        base_symbol = symbol.split('/')[0]
        
        if base_symbol == 'XRP':
            # Developer Activity (10 pts)
            dev_score = 7.0
            details['developer_activity'] = {
                'score': dev_score,
                'reason': 'Active EVM sidechain development, regular XRPL upgrades',
                'activity_level': 'moderate',
            }
            score += dev_score
            
            # Network Growth (10 pts)
            network_score = 6.0
            details['network_growth'] = {
                'score': network_score,
                'reason': 'Stable transaction volume, moderate address growth',
                'trend': 'stable',
            }
            score += network_score
            
        elif base_symbol == 'ADA':
            dev_score = 8.0
            details['developer_activity'] = {
                'score': dev_score,
                'reason': 'Strong academic development, peer-reviewed approach',
                'activity_level': 'high',
            }
            score += dev_score
            
            network_score = 5.0
            details['network_growth'] = {
                'score': network_score,
                'reason': 'Growing dApp ecosystem, steady but not explosive',
                'trend': 'growing',
            }
            score += network_score
            
        elif base_symbol == 'SOL':
            dev_score = 9.0
            details['developer_activity'] = {
                'score': dev_score,
                'reason': 'Very high developer activity, rapid dApp launches',
                'activity_level': 'very_high',
            }
            score += dev_score
            
            network_score = 8.0
            details['network_growth'] = {
                'score': network_score,
                'reason': 'Strong network growth, high transaction volume',
                'trend': 'strong_growth',
            }
            score += network_score
            
        else:
            dev_score = 3.0
            network_score = 2.0
            details['developer_activity'] = {'score': dev_score, 'reason': 'Limited data'}
            details['network_growth'] = {'score': network_score, 'reason': 'Limited data'}
            score = dev_score + network_score
        
        return min(score, 20.0), details
    
    def _score_market_position(self, symbol: str, exchange_data: Optional[Dict] = None) -> Tuple[float, Dict]:
        """
        Score market position (0-10 points).
        
        Metrics:
        - Price vs MA200: Distance from long-term average (5 pts)
        - Relative strength: Performance vs BTC (5 pts)
        
        Note: This uses some technical data, but it's just for context (10% weight)
        """
        score = 0.0
        details = {}
        
        # For now, use simplified scoring (will integrate exchange data in Phase 2)
        base_symbol = symbol.split('/')[0]
        
        if base_symbol == 'XRP':
            # XRP currently below MA200
            ma200_score = 2.0
            details['price_vs_ma200'] = {
                'score': ma200_score,
                'reason': 'Below MA200 (consolidation phase)',
                'status': 'below',
            }
            score += ma200_score
            
            # Stable vs BTC recently
            relative_score = 3.0
            details['relative_strength'] = {
                'score': relative_score,
                'reason': 'Stable vs BTC, not losing ground',
                'trend': 'stable',
            }
            score += relative_score
            
        elif base_symbol in ['ADA', 'SOL']:
            ma200_score = 3.0
            relative_score = 3.0
            details['price_vs_ma200'] = {'score': ma200_score, 'reason': 'Near MA200'}
            details['relative_strength'] = {'score': relative_score, 'reason': 'Neutral vs BTC'}
            score = ma200_score + relative_score
            
        else:
            ma200_score = 2.0
            relative_score = 2.0
            details['price_vs_ma200'] = {'score': ma200_score, 'reason': 'Default scoring'}
            details['relative_strength'] = {'score': relative_score, 'reason': 'Default scoring'}
            score = ma200_score + relative_score
        
        return min(score, 10.0), details
    
    def _get_recommendation(self, total_score: float) -> str:
        """
        Convert score to recommendation.
        
        Thresholds:
        - 85-100: STRONG_BUY
        - 70-84: BUY
        - 50-69: WATCH
        - 30-49: AVOID
        - 0-29: FREEZE
        """
        if total_score >= REGULATORY_SCORE_THRESHOLDS['STRONG_BUY']:
            return 'STRONG_BUY'
        elif total_score >= REGULATORY_SCORE_THRESHOLDS['BUY']:
            return 'BUY'
        elif total_score >= REGULATORY_SCORE_THRESHOLDS['WATCH']:
            return 'WATCH'
        elif total_score >= REGULATORY_SCORE_THRESHOLDS['AVOID']:
            return 'AVOID'
        else:
            return 'FREEZE'
    
    def _calculate_confidence(self, reg: float, inst: float, eco: float, mkt: float) -> str:
        """
        Calculate confidence level based on score distribution.
        
        High confidence: All pillars scoring reasonably well
        Medium confidence: Mixed signals
        Low confidence: Conflicting or weak signals
        """
        # Strong across all pillars
        if reg >= 25 and inst >= 20 and eco >= 12:
            return 'HIGH'
        
        # At least two strong pillars
        strong_pillars = sum([
            reg >= 25,
            inst >= 20,
            eco >= 12,
        ])
        
        if strong_pillars >= 2:
            return 'MEDIUM'
        
        # Weak signals
        return 'LOW'
    
    def _save_score(self, result: Dict):
        """Save score to database for historical tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO regulatory_scores 
                (symbol, timestamp, total_score, regulatory_score, institutional_score, 
                 ecosystem_score, market_score, recommendation, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['symbol'],
                result['timestamp'],
                result['total_score'],
                result['breakdown']['regulatory'],
                result['breakdown']['institutional'],
                result['breakdown']['ecosystem'],
                result['breakdown']['market'],
                result['recommendation'],
                json.dumps(result['details'])
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_historical_scores(self, symbol: str, days: int = 30) -> list:
        """Get historical scores for an asset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        cursor.execute('''
            SELECT timestamp, total_score, recommendation 
            FROM regulatory_scores
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (symbol, cutoff.isoformat()))
        
        results = [
            {'timestamp': row[0], 'score': row[1], 'recommendation': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results


# Convenience function
def score_asset(symbol: str) -> Dict:
    """Quick scoring function"""
    scorer = RegulatoryScorer()
    return scorer.calculate_score(symbol)


if __name__ == '__main__':
    # Example: Score XRP
    scorer = RegulatoryScorer()
    
    print("=" * 60)
    print("XRP/USDT Regulatory Score")
    print("=" * 60)
    
    result = scorer.calculate_score('XRP/USDT')
    
    print(f"\nTotal Score: {result['total_score']}/100")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']}")
    
    print("\nBreakdown:")
    for category, score in result['breakdown'].items():
        print(f"  {category.capitalize():20s}: {score:5.1f} pts")
    
    print("\nDetails:")
    for category, details in result['details'].items():
        print(f"\n{category.upper()}:")
        for key, value in details.items():
            if isinstance(value, dict):
                print(f"  {key}: {value.get('score', 'N/A')} - {value.get('reason', 'N/A')}")
