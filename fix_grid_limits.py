with open('strategies/grid_strategy_v2.py', 'r') as f:
    content = f.read()

# Find the static fallback and add limit setting
old_code = """             elif self.grids is None:
                 # Fallback to static if calc failed and no grids exist
                 self.grids = np.linspace(self.lower_limit_static, self.upper_limit_static, self.grid_levels)
                 self.grid_step = (self.upper_limit_static - self.lower_limit_static) / (self.grid_levels - 1)"""

new_code = """             elif self.grids is None:
                 # Fallback to static if calc failed and no grids exist
                 self.lower_limit = self.lower_limit_static
                 self.upper_limit = self.upper_limit_static
                 self.grids = np.linspace(self.lower_limit_static, self.upper_limit_static, self.grid_levels)
                 self.grid_step = (self.upper_limit_static - self.lower_limit_static) / (self.grid_levels - 1)
                 print(f"[Grid] Using static range ${self.lower_limit:.0f}-${self.upper_limit:.0f}")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('strategies/grid_strategy_v2.py', 'w') as f:
        f.write(content)
    print("✅ Fixed!")
else:
    print("Pattern not found")
