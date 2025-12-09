from datetime import datetime, time
from decimal import Decimal, getcontext

# Set precision for critical financial calculations
getcontext().prec = 28

class RiskManager:
    def __init__(self, min_profit_pct=0.5, fee_rate=0.001, max_drawdown_pct=0.10):
        # Convert all inputs to Decimal immediately
        self.min_profit_pct = Decimal(str(min_profit_pct))
        self.fee_rate = Decimal(str(fee_rate))
        self.max_drawdown_pct = Decimal(str(max_drawdown_pct))
        self.peak_equity = None
        self.allowed_hours = (time(0, 0), time(23, 59)) # Default: 24/7

    def set_schedule(self, start_hour, end_hour):
        """Set trading hours"""
        self.allowed_hours = (time(start_hour, 0), time(end_hour, 59))

    def can_trade(self):
        """Check if current time is within allowed hours"""
        now = datetime.now().time()
        start, end = self.allowed_hours
        if start <= end:
            return start <= now <= end
        else: # Crosses midnight
            return start <= now or now <= end

    def check_profit_guard(self, current_price, buy_price):
        """
        Check if selling now yields a profit after fees (using Decimal).
        """
        # Ensure inputs are Decimal
        cp = Decimal(str(current_price))
        bp = Decimal(str(buy_price))
        
        # Cost to buy 1 unit
        buy_cost = bp * (Decimal('1') + self.fee_rate)
        
        # Net proceeds from selling 1 unit
        sell_proceeds = cp * (Decimal('1') - self.fee_rate)
        
        # Profit
        profit = sell_proceeds - buy_cost
        
        # Avoid division by zero
        if buy_cost == 0:
            return False, Decimal('0')
            
        profit_pct = (profit / buy_cost) * Decimal('100')
        
        is_profitable = profit_pct >= self.min_profit_pct
        
        return is_profitable, profit_pct
    
    def check_drawdown_limit(self, current_equity, logger):
        """
        Check if current drawdown exceeds maximum allowed.
        """
        ce = Decimal(str(current_equity))
        
        # Initialize peak equity on first call
        if self.peak_equity is None:
            self.peak_equity = ce
        
        # Update peak if we've grown
        if ce > self.peak_equity:
            self.peak_equity = ce
        
        # Avoid division by zero if peak is 0 (unlikely but safe)
        if self.peak_equity == 0:
             return True, Decimal('0')

        # Calculate drawdown from peak
        drawdown = (self.peak_equity - ce) / self.peak_equity
        drawdown_pct = drawdown * Decimal('100')
        
        # Check if we've exceeded the max drawdown limit
        if drawdown > self.max_drawdown_pct:
            return False, drawdown_pct
        
        return True, drawdown_pct
