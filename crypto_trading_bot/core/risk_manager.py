from datetime import datetime, time

class RiskManager:
    def __init__(self, min_profit_pct=0.5, fee_rate=0.001):
        self.min_profit_pct = min_profit_pct
        self.fee_rate = fee_rate
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
        Check if selling now yields a profit after fees.
        Sell Price > Buy Price + Buy Fee + Sell Fee + Min Profit
        """
        # Cost to buy 1 unit
        buy_cost = buy_price * (1 + self.fee_rate)
        
        # Net proceeds from selling 1 unit
        sell_proceeds = current_price * (1 - self.fee_rate)
        
        # Profit
        profit = sell_proceeds - buy_cost
        profit_pct = (profit / buy_cost) * 100
        
        is_profitable = profit_pct >= self.min_profit_pct
        
        return is_profitable, profit_pct
