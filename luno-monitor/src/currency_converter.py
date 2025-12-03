"""
Currency Converter Module
Handles ZAR to MYR conversion with live exchange rates
"""
import requests
from typing import Optional
import config

class CurrencyConverter:
    """Convert between ZAR and MYR"""
    
    def __init__(self):
        """Initialize currency converter"""
        self.zar_to_myr_rate = config.ZAR_TO_MYR_RATE
        self.last_update = None
    
    def update_exchange_rate(self) -> bool:
        """
        No update needed as we are using native MYR
        """
        return True
    
    def zar_to_myr(self, amount: float) -> float:
        """
        Pass-through as amount is already in MYR
        """
        return amount
    
    def format_zar(self, amount: float) -> str:
        """Format as MYR (replaces ZAR)"""
        return f"RM {amount:,.2f}"
    
    def format_myr(self, amount: float) -> str:
        """Format MYR amount"""
        return f"RM {amount:,.2f}"
    
    def format_dual(self, amount: float) -> str:
        """
        Format amount in MYR
        """
        return f"RM {amount:,.2f}"
    
    def format_myr_primary(self, amount: float) -> str:
        """
        Format amount in MYR
        """
        return f"RM {amount:,.2f}"
    
    def get_rate(self) -> float:
        """Get current exchange rate"""
        return self.zar_to_myr_rate


if __name__ == "__main__":
    # Test currency converter
    converter = CurrencyConverter()
    
    print("Testing Currency Converter...")
    print(f"Current rate: 1 ZAR = {converter.get_rate()} MYR")
    
    # Update rate
    if converter.update_exchange_rate():
        print(f"✓ Updated rate: 1 ZAR = {converter.get_rate()} MYR")
    
    # Test conversions
    test_amount = 209279.49
    print(f"\nTest conversion:")
    print(f"ZAR: {converter.format_zar(test_amount)}")
    print(f"MYR: {converter.format_myr(converter.zar_to_myr(test_amount))}")
    print(f"Dual: {converter.format_dual(test_amount)}")
    print(f"MYR Primary: {converter.format_myr_primary(test_amount)}")
