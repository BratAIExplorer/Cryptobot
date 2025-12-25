"""
Asset Classifier

Routes cryptocurrency symbols to the appropriate scoring system.

Classification Types:
- TECHNICAL: Assets driven by technical patterns (BTC, ETH, DOGE) → Use Confluence V2
- REGULATORY: Assets driven by fundamentals/regulation (XRP, ADA, SOL) → Use Regulatory Scorer  
- NEW_COIN: Newly listed assets (<90 days) → Use LaunchPad Module (future)
"""

from typing import Dict, Literal
from datetime import datetime
from .config import TECHNICAL_ASSETS, REGULATORY_ASSETS

AssetType = Literal['TECHNICAL', 'REGULATORY', 'NEW_COIN']


class AssetClassifier:
    """
    Classify cryptocurrency assets to determine which scoring system to use.
    
    Philosophy:
    - Different assets have different drivers (technical vs fundamental)
    - Using the wrong tool leads to bad signals (XRP + Confluence V2 = 1.8/100 useless)
    - Route intelligently based on asset characteristics
    """
    
    def __init__(self):
        """Initialize classifier with configured asset mappings"""
        self.technical_assets = TECHNICAL_ASSETS
        self.regulatory_assets = REGULATORY_ASSETS
        self.classification_cache = {}
        
    def classify(self, symbol: str) -> Dict[str, str]:
        """
        Classify a cryptocurrency symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'XRP/USDT')
            
        Returns:
            Dictionary with classification info:
            {
                'symbol': 'XRP/USDT',
                'type': 'REGULATORY',
                'scorer': 'regulatory',
                'reason': 'SEC lawsuit, ETFs, institutional adoption',
                'confidence': 'high'
            }
        """
        # Check cache first
        if symbol in self.classification_cache:
            return self.classification_cache[symbol]
        
        # Normalize symbol format
        symbol = symbol.upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"  # Default to USDT pair
        
        # Check if explicitly configured as regulatory
        if symbol in self.regulatory_assets:
            result = {
                'symbol': symbol,
                'type': 'REGULATORY',
                'scorer': 'regulatory',
                'reason': self.regulatory_assets[symbol]['reason'],
                'key_metrics': self.regulatory_assets[symbol].get('key_metrics', []),
                'confidence': 'high',  # Explicitly configured
            }
            self.classification_cache[symbol] = result
            return result
        
        # Check if explicitly configured as technical
        if symbol in self.technical_assets:
            result = {
                'symbol': symbol,
                'type': 'TECHNICAL',
                'scorer': 'confluence_v2',
                'reason': self.technical_assets[symbol]['reason'],
                'confidence': 'high',  # Explicitly configured
            }
            self.classification_cache[symbol] = result
            return result
        
        # Default: treat unknown assets as technical
        # (Conservative approach - V2 is battle-tested)
        result = {
            'symbol': symbol,
            'type': 'TECHNICAL',
            'scorer': 'confluence_v2',
            'reason': 'Default classification - no specific configuration',
            'confidence': 'low',  # Not explicitly configured
        }
        self.classification_cache[symbol] = result
        return result
    
    def is_regulatory_asset(self, symbol: str) -> bool:
        """Quick check if asset should use regulatory scoring"""
        classification = self.classify(symbol)
        return classification['type'] == 'REGULATORY'
    
    def is_technical_asset(self, symbol: str) -> bool:
        """Quick check if asset should use technical scoring (Confluence V2)"""
        classification = self.classify(symbol)
        return classification['type'] == 'TECHNICAL'
    
    def get_scorer_name(self, symbol: str) -> str:
        """Get the name of the scorer to use for this asset"""
        classification = self.classify(symbol)
        return classification['scorer']
    
    def get_all_regulatory_assets(self) -> list:
        """Get list of all assets configured for regulatory scoring"""
        return list(self.regulatory_assets.keys())
    
    def get_all_technical_assets(self) -> list:
        """Get list of all assets configured for technical scoring"""
        return list(self.technical_assets.keys())
    
    def add_asset_override(self, symbol: str, asset_type: AssetType, reason: str = None):
        """
        Add a runtime override for asset classification.
        
        Useful for testing or temporary adjustments without modifying config.
        
        Args:
            symbol: Trading pair (e.g., 'XRP/USDT')
            asset_type: 'TECHNICAL', 'REGULATORY', or 'NEW_COIN'
            reason: Optional explanation for override
        """
        symbol = symbol.upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        scorer_map = {
            'TECHNICAL': 'confluence_v2',
            'REGULATORY': 'regulatory',
            'NEW_COIN': 'launchpad',
        }
        
        override = {
            'symbol': symbol,
            'type': asset_type,
            'scorer': scorer_map[asset_type],
            'reason': reason or f'Runtime override to {asset_type}',
            'confidence': 'override',
        }
        
        # Update cache
        self.classification_cache[symbol] = override
        
        return override
    
    def clear_cache(self):
        """Clear classification cache (useful for testing)"""
        self.classification_cache = {}
    
    def get_classification_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of configured classifications.
        
        Returns:
            {
                'regulatory': 6,  # XRP, ADA, SOL, MATIC, LINK, DOT
                'technical': 5,   # BTC, ETH, DOGE, LTC, BCH
                'total': 11
            }
        """
        return {
            'regulatory': len(self.regulatory_assets),
            'technical': len(self.technical_assets),
            'total': len(self.regulatory_assets) + len(self.technical_assets),
        }


# Convenience functions for quick checks
def is_regulatory(symbol: str) -> bool:
    """Quick check if symbol needs regulatory scoring"""
    classifier = AssetClassifier()
    return classifier.is_regulatory_asset(symbol)


def is_technical(symbol: str) -> bool:
    """Quick check if symbol needs technical scoring (Confluence V2)"""
    classifier = AssetClassifier()
    return classifier.is_technical_asset(symbol)


def get_scorer(symbol: str) -> str:
    """Get scorer name for symbol"""
    classifier = AssetClassifier()
    return classifier.get_scorer_name(symbol)


# Example usage
if __name__ == '__main__':
    classifier = AssetClassifier()
    
    # Test regulatory assets
    print("=== REGULATORY ASSETS ===")
    for symbol in ['XRP/USDT', 'ADA/USDT', 'SOL/USDT']:
        result = classifier.classify(symbol)
        print(f"{symbol}: {result['type']} - Use {result['scorer']}")
        print(f"  Reason: {result['reason']}\n")
    
    # Test technical assets
    print("\n=== TECHNICAL ASSETS ===")
    for symbol in ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT']:
        result = classifier.classify(symbol)
        print(f"{symbol}: {result['type']} - Use {result['scorer']}")
        print(f"  Reason: {result['reason']}\n")
    
    # Test unknown asset (defaults to technical)
    print("\n=== UNKNOWN ASSET ===")
    result = classifier.classify('NEWCOIN/USDT')
    print(f"NEWCOIN/USDT: {result['type']} - Use {result['scorer']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Confidence: {result['confidence']}")
    
    # Summary
    print("\n=== SUMMARY ===")
    summary = classifier.get_classification_summary()
    print(f"Regulatory assets: {summary['regulatory']}")
    print(f"Technical assets: {summary['technical']}")
    print(f"Total configured: {summary['total']}")
