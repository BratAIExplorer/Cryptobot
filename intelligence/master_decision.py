"""
Master Decision Engine

Unified interface that routes cryptocurrency symbols to the appropriate scoring system.

Architecture:
- AssetClassifier determines which scorer to use
- Routes to Confluence V2 (technical) or Regulatory Scorer (fundamental)
- Returns unified response format

This is the single entry point for all asset scoring queries.
"""

from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .asset_classifier import AssetClassifier
from .regulatory_scorer import RegulatoryScorer
from .config import FEATURE_FLAGS

# Import Confluence V2 (existing system)
try:
    from utils.confluence_filter import ConfluenceFilter
except ImportError:
    # Fallback if import fails
    ConfluenceFilter = None


class MasterDecisionEngine:
    """
    Unified intelligence interface.
    
    Routes assets to appropriate scorer:
    - BTC, ETH, DOGE → Confluence V2 (technical)
    - XRP, ADA, SOL → Regulatory Scorer (fundamental)
    
    Returns consistent format regardless of scorer used.
    """
    
    def __init__(self, exchange=None):
        """
        Initialize master decision engine.
        
        Args:
            exchange: Exchange interface (for fetching market data)
        """
        self.classifier = AssetClassifier()
        self.regulatory_scorer = RegulatoryScorer()
        self.confluence_v2 = ConfluenceFilter(exchange=exchange) if ConfluenceFilter else None
        self.exchange = exchange
        
    def get_signal(self, symbol: str, market_data: Optional[Dict] = None) -> Dict:
        """
        Get trading signal for any cryptocurrency.
        
        This is the main entry point. It automatically:
        1. Classifies the asset type
        2. Routes to appropriate scorer
        3. Returns unified response
        
        Args:
            symbol: Trading pair (e.g., 'XRP/USDT')
            market_data: Optional market data (price, volume, etc.)
            
        Returns:
            {
                'symbol': 'XRP/USDT',
                'score': 70,
                'recommendation': 'BUY',
                'scorer_used': 'regulatory',
                'confidence': 'high',
                'breakdown': {...},
                'details': {...}
            }
        """
        # Classify asset
        classification = self.classifier.classify(symbol)
        
        # Route to appropriate scorer
        if classification['scorer'] == 'regulatory':
            return self._score_regulatory(symbol, classification, market_data)
        elif classification['scorer'] == 'confluence_v2':
            return self._score_technical(symbol, classification, market_data)
        else:
            # Unknown scorer (future: launchpad for new coins)
            return {
                'symbol': symbol,
                'score': 0,
                'recommendation': 'NOT_SUPPORTED',
                'scorer_used': classification['scorer'],
                'confidence': 'none',
                'error': f"Scorer '{classification['scorer']}' not yet implemented"
            }
    
    def _score_regulatory(self, symbol: str, classification: Dict, market_data: Optional[Dict]) -> Dict:
        """Score using Regulatory Scorer"""
        result = self.regulatory_scorer.calculate_score(symbol, exchange_data=market_data)
        
        # Add classification info
        result['scorer_used'] = 'regulatory'
        result['asset_type'] = classification['type']
        result['classification'] = classification['type'] # Backward compat alias
        result['classification_reason'] = classification['reason']
        result['score'] = result['total_score'] # Alias for consistency
        
        return result
    
        return result
    
    def _score_technical(self, symbol: str, classification: Dict, market_data: Optional[Dict]) -> Dict:
        """Score using Confluence V2 (existing system)"""
        
        if not self.confluence_v2:
            return {
                'symbol': symbol,
                'score': 0,
                'total_score': 0,
                'recommendation': 'ERROR',
                'scorer_used': 'confluence_v2',
                'confidence': 'none',
                'error': 'Confluence V2 not available (import failed)'
            }
        
        # For now, return placeholder (will integrate properly in Phase 4)
        return {
            'symbol': symbol,
            'score': 0,
            'total_score': 0,  # Standardization
            'recommendation': 'NOT_IMPLEMENTED',
            'scorer_used': 'confluence_v2',
            'asset_type': classification['type'],
            'classification': classification['type'], # Backward compat alias
            'classification_reason': classification['reason'],
            'note': 'Confluence V2 integration pending (requires OHLCV data fetch)'
        }
    
    def compare_scorers(self, symbol: str) -> Dict:
        """
        Compare scores from both systems (if applicable).
        
        Useful for regulatory assets to see how V2 vs Regulatory differ.
        
        Returns:
            {
                'symbol': 'XRP/USDT',
                'regulatory': {score: 70, recommendation: 'BUY'},
                'confluence_v2': {score: 1.8, recommendation: 'AVOID'},
                'recommended_scorer': 'regulatory',
                'score_difference': 68.2
            }
        """
        # Get both scores
        regulatory_result = self._score_regulatory(symbol, {'type': 'REGULATORY'}, None)
        technical_result = self._score_technical(symbol, {'type': 'TECHNICAL'}, None)
        
        # Determine which to recommend
        classification = self.classifier.classify(symbol)
        recommended = classification['scorer']
        
        score_diff = abs(
            regulatory_result.get('total_score', 0) - 
            technical_result.get('score', 0)
        )
        
        return {
            'symbol': symbol,
            'regulatory': {
                'score': regulatory_result.get('total_score', 0),
                'recommendation': regulatory_result.get('recommendation', 'N/A'),
                'confidence': regulatory_result.get('confidence', 'N/A'),
            },
            'confluence_v2': {
                'score': technical_result.get('score', 0),
                'recommendation': technical_result.get('recommendation', 'N/A'),
                'note': technical_result.get('note', ''),
            },
            'recommended_scorer': recommended,
            'score_difference': round(score_diff, 1),
            'classification': classification,
        }
    
    def get_all_signals(self, symbols: list) -> Dict[str, Dict]:
        """
        Get signals for multiple symbols at once.
        
        Args:
            symbols: List of trading pairs
            
        Returns:
            Dictionary mapping symbol to signal
        """
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_signal(symbol)
            except Exception as e:
                results[symbol] = {
                    'symbol': symbol,
                    'score': 0,
                    'recommendation': 'ERROR',
                    'error': str(e)
                }
        return results


# Convenience functions
def get_signal(symbol: str) -> Dict:
    """Get signal for a single asset"""
    engine = MasterDecisionEngine()
    return engine.get_signal(symbol)


def compare_scorers(symbol: str) -> Dict:
    """Compare Regulatory vs Confluence V2 for an asset"""
    engine = MasterDecisionEngine()
    return engine.compare_scorers(symbol)


if __name__ == '__main__':
    # Example usage
    engine = MasterDecisionEngine()
    
    print("=" * 70)
    print("MASTER DECISION ENGINE - Examples")
    print("=" * 70)
    
    # Test XRP (should use regulatory scorer)
    print("\n1. XRP/USDT (Regulatory Asset):")
    print("-" * 70)
    xrp_signal = engine.get_signal('XRP/USDT')
    print(f"Score: {xrp_signal.get('total_score', 'N/A')}/100")
    print(f"Recommendation: {xrp_signal.get('recommendation', 'N/A')}")
    print(f"Scorer Used: {xrp_signal.get('scorer_used', 'N/A')}")
    print(f"Confidence: {xrp_signal.get('confidence', 'N/A')}")
    
    # Test BTC (should use confluience v2)
    print("\n2. BTC/USDT (Technical Asset):")
    print("-" * 70)
    btc_signal = engine.get_signal('BTC/USDT')
    print(f"Score: {btc_signal.get('score', 'N/A')}/100")
    print(f"Recommendation: {btc_signal.get('recommendation', 'N/A')}")
    print(f"Scorer Used: {btc_signal.get('scorer_used', 'N/A')}")
    print(f"Note: {btc_signal.get('note', 'N/A')}")
    
    # Compare scorers for XRP
    print("\n3. Comparison: XRP/USDT (Both Scorers):")
    print("-" * 70)
    comparison = engine.compare_scorers('XRP/USDT')
    print(f"Regulatory Score: {comparison['regulatory']['score']}/100 - {comparison['regulatory']['recommendation']}")
    print(f"Confluence V2:    {comparison['confluence_v2']['score']}/100 - {comparison['confluence_v2']['recommendation']}")
    print(f"Recommended: Use {comparison['recommended_scorer']}")
    print(f"Score Difference: {comparison['score_difference']} points")
