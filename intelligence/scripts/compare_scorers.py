"""
Scorer Comparison Tool

Compare Confluence V2 vs Regulatory scores for any asset.

Especially useful for regulatory assets like XRP to see the score difference.

Usage:
    python scripts/compare_scorers.py --symbol XRP/USDT
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intelligence.master_decision import MasterDecisionEngine


def format_comparison(comparison: dict):
    """Format comparison result for console output"""
    
    print("=" * 70)
    print(f"SCORER COMPARISON: {comparison['symbol']}")
    print("=" * 70)
    
    # Regulatory Score
    reg = comparison['regulatory']
    print(f"\n📊 REGULATORY SCORER:")
    print(f"   Score:          {reg['score']}/100")
    print(f"   Recommendation: {reg['recommendation']}")
    print(f"   Confidence:     {reg['confidence'].upper()}")
    
    # Confluence V2 Score
    v2 = comparison['confluence_v2']
    print(f"\n📈 CONFLUENCE V2 (Technical):")
    print(f"   Score:          {v2['score']}/100")
    print(f"   Recommendation: {v2['recommendation']}")
    if v2.get('note'):
        print(f"   Note:           {v2['note']}")
    
    # Comparison
    print(f"\n🎯 ANALYSIS:")
    print(f"   Recommended Scorer: {comparison['recommended_scorer'].upper()}")
    print(f"   Score Difference:   {comparison['score_difference']} points")
    
    # Interpretation
    classification = comparison['classification']
    print(f"\n💡 WHY {comparison['recommended_scorer'].upper()}?")
    print(f"   Asset Type: {classification['type']}")
    print(f"   Reason: {classification['reason']}")
    
    # Verdict
    print(f"\n{'=' * 70}")
    if comparison['recommended_scorer'] == 'regulatory':
        if comparison['score_difference'] > 50:
            print("✅ VERDICT: Regulatory scorer strongly recommended")
            print(f"   → {comparison['symbol']} is fundamentally-driven, not technical")
            print(f"   → Use {reg['score']}/100 ({reg['recommendation']}) instead of {v2['score']}/100")
        else:
            print("⚠️  VERDICT: Regulatory scorer recommended (moderate difference)")
    else:
        print("✅ VERDICT: Use Confluence V2 (technical scorer)")
        print(f"   → {comparison['symbol']} follows technical patterns")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Compare Regulatory vs Confluence V2 scores',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compare XRP scores
  python compare_scorers.py --symbol XRP/USDT
  
  # Compare multiple assets
  python compare_scorers.py --symbol XRP/USDT --symbol ADA/USDT
        '''
    )
    
    parser.add_argument(
        '--symbol', '-s',
        action='append',
        required=True,
        help='Trading pair symbol (e.g., XRP/USDT)'
    )
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = MasterDecisionEngine()
    
    # Compare each symbol
    for symbol in args.symbol:
        try:
            comparison = engine.compare_scorers(symbol)
            format_comparison(comparison)
            print("\n")
        except Exception as e:
            print(f"❌ Error comparing {symbol}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
