"""
Test script for Confluence Engine V2 with Regime Detection
"""

import sys
import os
import pandas as pd
import ccxt

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'luno-monitor', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from confluence_engine import ConfluenceEngine
from regime_detector import RegimeDetector
from execution_validator import ExecutionValidator

def fetch_btc_data():
    """Fetch BTC historical data for regime detection"""
    print("Fetching BTC data from MEXC...")
    try:
        exchange = ccxt.mexc()
        # Fetch 250 daily candles (need 200+ for MA200)
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=250)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print(f"✅ Fetched {len(df)} candles")
        print(f"   Latest BTC price: ${df['close'].iloc[-1]:,.0f}")
        print(f"   Latest MA200: ${df['close'].rolling(200).mean().iloc[-1]:,.0f}")
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching BTC data: {e}")
        return None


def test_regime_detection():
    """Test regime detector"""
    print("\n" + "="*60)
    print("TEST 1: Regime Detection")
    print("="*60)
    
    btc_df = fetch_btc_data()
    if btc_df is None:
        return
    
    detector = RegimeDetector()
    regime, confidence, metrics = detector.detect_regime(btc_df)
    
    print(f"\n🎯 Detected Regime: {regime.value}")
    print(f"   Confidence: {confidence:.1%}")
    print(f"   Risk Multiplier: {detector.get_risk_multiplier(regime)}x")
    print(f"   Trading Allowed: {'✅ YES' if detector.should_trade(regime) else '❌ NO'}")
    
    print(f"\n📊 Metrics:")
    print(f"   BTC Price: ${metrics.get('btc_price', 0):,.0f}")
    print(f"   vs MA200: {metrics.get('price_vs_ma200', 0):+.1f}%")
    print(f"   Volatility: {metrics.get('volatility_percentile', 0):.0f}th percentile")
    print(f"   Higher Highs: {'✅' if metrics.get('higher_highs') else '❌'}")
    print(f"   Lower Lows: {'✅' if metrics.get('lower_lows') else '❌'}")
    print(f"   Volume Trend: {metrics.get('volume_trend', 'UNKNOWN')}")


def test_confluence_engine_v2():
    """Test enhanced confluence engine with regime detection"""
    print("\n" + "="*60)
    print("TEST 2: Confluence Engine V2")
    print("="*60)
    
    engine = ConfluenceEngine()
    
    # Sample inputs (in production, these come from APIs)
    test_inputs = {
        'rsi': 55,
        'macd_signal': 'BULLISH',
        'volume_trend': 'INCREASING',
        'price': 2.10,
        'ma50': 1.95,
        'ma200': 1.70,
        'whale_holdings': 47,
        'exchange_reserves': 2.8,
        'velocity': 0.0285,
        'exchange_flow_ratio': 0.15,
        'btc_trend': 'BULLISH',
        'btc_price': 98500,
        'risk_regime': 'RISK-ON',
        'fed_rate_cut_prob': 75,
        'etf_inflows': 320,
        'xlm_outperformance_pct': 8
    }
    
    # Fetch BTC data for regime detection
    btc_df = fetch_btc_data()
    
    # Calculate score
    print("\nCalculating confluence score for XRP...")
    result = engine.get_total_confluence_score(
        'XRP', 
        manual_inputs=test_inputs,
        btc_df=btc_df,
        enable_regime_detection=True
    )
    
    # Print results
    engine.print_confluence_report(result)
    
    print(f"\n🌍 Regime Impact:")
    regime = result['regime']
    print(f"   Market Regime: {regime['state']}")
    print(f"   Confidence: {regime['confidence']:.1%}")
    print(f"   Risk Multiplier: {regime['multiplier']}x")
    
    scores = result['scores']
    print(f"\n🎯 Score Breakdown:")
    print(f"   Raw Score: {scores['raw_total']}/100")
    print(f"   Final Score (after regime): {scores['final_total']}/100")
    print(f"   Adjustment: {scores['final_total'] - scores['raw_total']:+d} points")


def test_execution_validator():
    """Test execution validation"""
    print("\n" + "="*60)
    print("TEST 3: Execution Validator")
    print("="*60)
    
    try:
        exchange = ccxt.mexc()
        validator = ExecutionValidator(exchange)
        
        # Test validation for XRP
        print("\nValidating execution for XRP/USDT...")
        is_allowed, reason, metrics = validator.validate_execution(
            symbol='XRP/USDT',
            side='BUY',
            theoretical_price=2.10,
            order_size_usd=1000
        )
        
        if is_allowed:
            print("✅ Execution APPROVED")
        else:
            print(f"❌ Execution REJECTED: {reason}")
        
        print(f"\n📊 Execution Metrics:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_signal_redundancy():
    """Test redundancy penalty logic"""
    print("\n" + "="*60)
    print("TEST 4: Signal Redundancy Penalty")
    print("="*60)
    
    engine = ConfluenceEngine()
    
    # Inputs that trigger redundancy:
    # Multiple momentum (RSI) and trend (MA50, MA200) signals
    redundant_inputs = {
        'rsi': 25, # Deeply oversold
        'macd_signal': 'BULLISH', # Overlaps with momentum
        'price': 105,
        'ma50': 100, # Price > MA50 (Trend)
        'ma200': 90,  # Price > MA200 (Trend) - Overlaps with MA50
        'velocity': 0.05,
        'volume_trend': 'INCREASING'
    }
    
    # Calculation without regime to see raw impact
    print("\nCalculating confluence with REDUNDANT signals...")
    result = engine.get_total_confluence_score(
        'XRP', 
        manual_inputs=redundant_inputs,
        enable_regime_detection=False # Focus on redundancy
    )
    
    engine.print_confluence_report(result)
    
    scores = result['scores']
    print(f"📊 Redundancy Check:")
    print(f"   Technical Score reached: {scores['technical']['score']}/{scores['technical']['max_score']}")
    # 5% penalty for 2 trend signals, plus potential MACD/RSI overlap
    # We expect some reduction in the technical score relative to summing raw values

if __name__ == "__main__":
    print("🚀 Confluence Engine V2 - Test Suite")
    print("="*60)
    
    try:
        # Run all tests
        test_regime_detection()
        test_confluence_engine_v2()
        test_execution_validator()
        test_signal_redundancy()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)

        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
