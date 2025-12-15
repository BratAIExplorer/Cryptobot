"""
Currency Conversion Verification Script
Tests the ZAR to MYR conversion for all coins
"""
import sys
import os

# Add luno-monitor directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'luno-monitor'))

from src.currency_converter import CurrencyConverter
from src.luno_client import LunoClient
import config

def test_currency_conversion():
    """Test currency conversion for all configured coins"""
    print("=" * 70)
    print("CURRENCY CONVERSION VERIFICATION")
    print("=" * 70)
    
    # Initialize converter
    converter = CurrencyConverter()
    luno_client = LunoClient()
    
    print(f"\n✓ Exchange Rate: 1 ZAR = {converter.get_rate():.4f} MYR")
    print(f"✓ Last Updated: {converter.last_update}")
    
    # Test connection
    if not luno_client.test_connection():
        print("\n✗ Failed to connect to Luno API")
        return
    
    print("\n" + "=" * 70)
    print("TESTING PRICES FOR ALL COINS")
    print("=" * 70)
    
    # Get prices for all coins
    for coin, pair in config.CRYPTO_PAIRS.items():
        try:
            # Get ticker (returns ZAR price)
            ticker = luno_client.get_ticker(pair)
            zar_price = ticker['last_trade']
            
            # Convert to MYR
            myr_price = converter.zar_to_myr(zar_price)
            
            print(f"\n{coin} ({pair}):")
            print(f"  ZAR Price: R {zar_price:,.2f}")
            print(f"  MYR Price: {converter.format_myr_primary(zar_price)}")
            print(f"  Conversion: R {zar_price:,.2f} × {converter.get_rate():.4f} = RM {myr_price:,.2f}")
            
        except Exception as e:
            print(f"\n{coin}: ✗ Error - {e}")
    
    print("\n" + "=" * 70)
    print("EXAMPLE: XRP Price Verification")
    print("=" * 70)
    
    # Special check for XRP (the reported issue)
    try:
        xrp_ticker = luno_client.get_ticker('XRPZAR')
        xrp_zar = xrp_ticker['last_trade']
        xrp_myr = converter.zar_to_myr(xrp_zar)
        
        print(f"\nYour notification showed: RM 33.51")
        print(f"Actual ZAR price: R {xrp_zar:,.2f}")
        print(f"Correct MYR price: RM {xrp_myr:,.2f}")
        print(f"\nThe issue: Bot was showing ZAR price as RM (no conversion)")
        print(f"The fix: Now properly converting ZAR → MYR")
        print(f"\nPrice difference: {abs(33.51 - xrp_myr) / 33.51 * 100:.1f}% correction")
        
    except Exception as e:
        print(f"\n✗ Could not verify XRP: {e}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_currency_conversion()
