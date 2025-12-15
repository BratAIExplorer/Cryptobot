"""
Currency Converter Module
Handles MYR formatting for Malaysian Luno market
"""

class CurrencyConverter:
    """Format MYR currency for display"""
    
    def __init__(self):
        """Initialize currency converter"""
        pass
    
    def update_exchange_rate(self) -> bool:
        """
        No-op for MYR (no conversion needed)
        Kept for backward compatibility
        """
        return True
    
    def format_myr(self, amount_myr: float) -> str:
        """Format MYR amount"""
        return f"RM {amount_myr:,.2f}"
    
    def format_myr_primary(self, amount_myr: float) -> str:
        """
        Format amount in MYR (primary display)
        
        Args:
            amount_myr: Amount in MYR
        
        Returns:
            Formatted MYR string
        """
        return f"RM {amount_myr:,.2f}"
    
    def format_dual(self, amount_myr: float) -> str:
        """
        Format amount (MYR only)
        Kept for backward compatibility
        """
        return f"RM {amount_myr:,.2f}"


if __name__ == "__main__":
    # Test currency converter
    converter = CurrencyConverter()
    
    print("Testing Currency Converter...")
    print("Using MYR (Malaysian Ringgit) natively - no conversion needed")
    
    # Test formatting
    test_amount = 201141.04
    print(f"\nTest formatting:")
    print(f"MYR: {converter.format_myr(test_amount)}")
    print(f"MYR Primary: {converter.format_myr_primary(test_amount)}")
    print(f"Dual: {converter.format_dual(test_amount)}")

