with open('strategies/grid_strategy_v2.py', 'r') as f:
    lines = f.readlines()

# Find get_signal method and add initialization right after the DEBUG line
for i, line in enumerate(lines):
    if '[GRID DEBUG]' in line and 'print(' in line:
        # Add initialization right after debug line
        indent = '        '
        init_code = [
            '\n',
            f'{indent}# Initialize limits if None (use static fallback)\n',
            f'{indent}if self.lower_limit is None:\n',
            f'{indent}    self.lower_limit = self.lower_limit_static\n',
            f'{indent}    self.upper_limit = self.upper_limit_static\n',
            f'{indent}    self.grids = np.linspace(self.lower_limit_static, self.upper_limit_static, self.grid_levels)\n',
            f'{indent}    self.grid_step = (self.upper_limit_static - self.lower_limit_static) / (self.grid_levels - 1)\n',
            f'{indent}    print(f"[Grid] {{self.symbol}}: Initialized with static range ${{self.lower_limit:.0f}}-${{self.upper_limit:.0f}}")\n',
            '\n'
        ]
        lines = lines[:i+1] + init_code + lines[i+1:]
        break

with open('strategies/grid_strategy_v2.py', 'w') as f:
    f.writelines(lines)

print("✅ Grid initialization fixed!")
