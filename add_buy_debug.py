with open('strategies/grid_strategy_v2.py', 'r') as f:
    lines = f.readlines()

# Find the BUY opportunity section and add debug
for i, line in enumerate(lines):
    if '# 2. Check for BUY opportunities' in line:
        # Add debug after this comment
        indent = '        '
        debug = f'{indent}print(f"[GRID] {{self.symbol}}: Checking BUY opportunities, grids={{len(self.grids) if self.grids is not None else 0}}")\n'
        lines.insert(i+1, debug)
        break

with open('strategies/grid_strategy_v2.py', 'w') as f:
    f.writelines(lines)
print("✅ BUY debug added")
