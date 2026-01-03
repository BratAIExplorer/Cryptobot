import sys

with open('core/engine.py', 'r') as f:
    lines = f.readlines()

# Find line 608 area and add debug logging
modified = False
for i, line in enumerate(lines):
    if i == 607 and not modified:  # Line before "if strategy_type == 'Grid':"
        # Check if debug already added
        if 'DEBUG: Evaluating' not in lines[i-1]:
            indent = len(line) - len(line.lstrip())
            debug_line = ' ' * indent + 'print(f"[DEBUG] Evaluating {bot[\'name\']} - Type: {strategy_type}")\n'
            lines.insert(i, debug_line)
            modified = True
            break

if modified:
    with open('core/engine.py', 'w') as f:
        f.writelines(lines)
    print("✅ Debug logging added at line 608")
else:
    print("⚠️ Debug logging already exists or line not found")
