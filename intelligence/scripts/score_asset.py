"""
Manual Asset Scoring Tool

Score any cryptocurrency using the appropriate scoring system.

Usage:
    python scripts/score_asset.py --symbol XRP/USDT
    python scripts/score_asset.py --symbol BTC/USDT
    python scripts/score_asset.py --symbol ADA/USDT --verbose
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intelligence.master_decision import MasterDecisionEngine
from intelligence.asset_classifier import AssetClassifier


def format_score_output(result: dict, verbose: bool = False):
    """Format scoring result for console output"""
    
    print("=" * 70)
    print(f"{result['symbol']} - Intelligence Score")
    print("=" * 70)
    
    # Main score
    total_score = result.get('total_score', result.get('score', 0))
    recommendation = result.get('recommendation', 'N/A')
    confidence = result.get('confidence', 'N/A')
    scorer_used = result.get('scorer_used', 'unknown')
    
    print(f"\nTotal Score: {total_score}/100")
    print(f"Recommendation: {recommendation}")
    print(f"Confidence: {confidence.upper()}")
    print(f"Scorer Used: {scorer_used}")
    
    # Breakdown (if regulatory)
    if 'breakdown' in result:
        print("\nScore Breakdown:")
        print("-" * 70)
        breakdown = result['breakdown']
        print(f"  Regulatory Progress:     {breakdown.get('regulatory', 0):5.1f}/40 pts")
        print(f"  Institutional Adoption:  {breakdown.get('institutional', 0):5.1f}/30 pts")
        print(f"  Ecosystem Development:   {breakdown.get('ecosystem', 0):5.1f}/20 pts")
        print(f"  Market Position:         {breakdown.get('market', 0):5.1f}/10 pts")
    
    # Verbose details
    if verbose and 'details' in result:
        print("\n" + "=" * 70)
        print("DETAILED BREAKDOWN")
        print("=" * 70)
        
        details = result['details']
        
        # Regulatory details
        if 'regulatory' in details:
            print("\n1. REGULATORY PROGRESS (0-40 pts):")
            print("-" * 70)
            reg = details['regulatory']
            
            if 'legal_status' in reg:
                print(f"\n   Legal Status: {reg['legal_status']['score']}/15 pts")
                print(f"   → {reg['legal_status']['reason']}")
                
            if 'etf_status' in reg:
                print(f"\n   ETF Status: {reg['etf_status']['score']}/15 pts")
                print(f"   → {reg['etf_status']['reason']}")
                if 'etfs' in reg['etf_status']:
                    print(f"   → ETFs: {', '.join(reg['etf_status']['etfs'])}")
                    
            if 'global_regulation' in reg:
                print(f"\n   Global Regulation: {reg['global_regulation']['score']}/10 pts")
                print(f"   → {reg['global_regulation']['reason']}")
        
        # Institutional details
        if 'institutional' in details:
            print("\n2. INSTITUTIONAL ADOPTION (0-30 pts):")
            print("-" * 70)
            inst = details['institutional']
            
            if 'partnerships' in inst:
                print(f"\n   Partnerships: {inst['partnerships']['score']}/15 pts")
                print(f"   → {inst['partnerships']['reason']}")
                if 'partners' in inst['partnerships']:
                    print(f"   → Partners: {', '.join(inst['partnerships']['partners'])}")
                    
            if 'integration_progress' in inst:
                print(f"\n   Integration Progress: {inst['integration_progress']['score']}/10 pts")
                print(f"   → {inst['integration_progress']['reason']}")
                
            if 'corporate_holdings' in inst:
                print(f"\n   Corporate Holdings: {inst['corporate_holdings']['score']}/5 pts")
                print(f"   → {inst['corporate_holdings']['reason']}")
        
        # Ecosystem details
        if 'ecosystem' in details:
            print("\n3. ECOSYSTEM DEVELOPMENT (0-20 pts):")
            print("-" * 70)
            eco = details['ecosystem']
            
            if 'developer_activity' in eco:
                print(f"\n   Developer Activity: {eco['developer_activity']['score']}/10 pts")
                print(f"   → {eco['developer_activity']['reason']}")
                
            if 'network_growth' in eco:
                print(f"\n   Network Growth: {eco['network_growth']['score']}/10 pts")
                print(f"   → {eco['network_growth']['reason']}")
        
        # Market details
        if 'market' in details:
            print("\n4. MARKET POSITION (0-10 pts):")
            print("-" * 70)
            mkt = details['market']
            
            if 'price_vs_ma200' in mkt:
                print(f"\n   Price vs MA200: {mkt['price_vs_ma200']['score']}/5 pts")
                print(f"   → {mkt['price_vs_ma200']['reason']}")
                
            if 'relative_strength' in mkt:
                print(f"\n   Relative Strength vs BTC: {mkt['relative_strength']['score']}/5 pts")
                print(f"   → {mkt['relative_strength']['reason']}")
    
    # Classification info
    if 'classification_reason' in result:
        print(f"\n{'-' * 70}")
        print(f"Asset Type: {result.get('asset_type', 'N/A')}")
        print(f"Reason: {result['classification_reason']}")
    
    # Error handling
    if 'error' in result:
        print(f"\n⚠️  ERROR: {result['error']}")
    
    if 'note' in result:
        print(f"\n📌 NOTE: {result['note']}")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Score cryptocurrency assets using Multi-Asset Intelligence System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Score XRP (regulatory asset)
  python score_asset.py --symbol XRP/USDT
  
  # Score with verbose details
  python score_asset.py --symbol XRP/USDT --verbose
  
  # Score BTC (technical asset)
  python score_asset.py --symbol BTC/USDT
  
  # Score multiple assets
  python score_asset.py --symbol XRP/USDT --symbol ADA/USDT --symbol SOL/USDT
        '''
    )
    
    parser.add_argument(
        '--symbol', '-s',
        action='append',
        required=True,
        help='Trading pair symbol (e.g., XRP/USDT). Can specify multiple.'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed breakdown of scoring'
    )
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = MasterDecisionEngine()
    
    # Score each symbol
    for symbol in args.symbol:
        try:
            result = engine.get_signal(symbol)
            format_score_output(result, verbose=args.verbose)
            print("\n")
        except Exception as e:
            print(f"❌ Error scoring {symbol}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
