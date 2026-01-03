import sys

with open('strategies/grid_strategy_v2.py', 'r') as f:
    content = f.read()

# Add debug at the start of get_signal
old_start = '''    def get_signal(self, current_price, open_positions, df=None):
        """
        Determine if we should BUY or SELL based on grid levels.
        Accepts full DataFrame to calculate dynamic grids.
        """

        # 0. Check Grid State'''

new_start = '''    def get_signal(self, current_price, open_positions, df=None):
        """
        Determine if we should BUY or SELL based on grid levels.
        Accepts full DataFrame to calculate dynamic grids.
        """
        
        # DEBUG: Show grid evaluation
        print(f"[GRID DEBUG] {self.symbol}: Price=${current_price:.2f}, Range=${self.lower_limit:.2f}-${self.upper_limit:.2f}, Grids={'Locked' if getattr(self, 'is_locked', False) else 'Unlocked'}")

        # 0. Check Grid State'''

if old_start in content:
    content = content.replace(old_start, new_start)
    
    # Add debug for stop-grid protection
    old_stop = '''        # Stop-Grid Protection: Don't buy if price is below lower limit (falling knife)
        if self.lower_limit and current_price < self.lower_limit * 0.98: # 2% buffer below range
            return None'''
    
    new_stop = '''        # Stop-Grid Protection: Don't buy if price is below lower limit (falling knife)
        if self.lower_limit and current_price < self.lower_limit * 0.98: # 2% buffer below range
            print(f"[GRID] {self.symbol}: STOP-GRID Protection - Price ${current_price:.2f} below range ${self.lower_limit:.2f}")
            return None'''
    
    content = content.replace(old_stop, new_stop)
    
    with open('strategies/grid_strategy_v2.py', 'w') as f:
        f.write(content)
    
    print("✅ Grid strategy debug logging added")
else:
    print("⚠️ Pattern not found")

