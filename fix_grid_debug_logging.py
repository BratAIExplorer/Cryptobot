#!/usr/bin/env python3
"""
Quick fix to add better debug logging for Grid bot strategy instance issues
This will help diagnose why ETH Grid Bot isn't creating positions
"""

import re

def fix_grid_debug_logging():
    """Add error logging when Grid strategy instance is None"""

    file_path = 'core/engine.py'

    with open(file_path, 'r') as f:
        content = f.read()

    # Find the Grid bot handling section
    old_code = """                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions, df=df)"""

    new_code = """                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions, df=df)"""

    # Actually, let's add an else clause
    old_code_with_context = """                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions, df=df)

                        if signal:"""

    new_code_with_else = """                if strategy_type == 'Grid':
                    strategy_instance = self.strategies.get(bot['name'])
                    if strategy_instance:
                        open_positions = self.logger.get_open_positions(symbol)
                        signal = strategy_instance.get_signal(current_price, open_positions, df=df)

                        if signal:"""

    # Different approach - let's add logging right after strategy instance retrieval
    search_pattern = r"(                if strategy_type == 'Grid':\n                    strategy_instance = self\.strategies\.get\(bot\['name'\]\)\n)(                    if strategy_instance:)"

    replacement = r"\1                    # DEBUG: Check if strategy instance exists\n                    if not strategy_instance:\n                        print(f\"❌ [GRID ERROR] Strategy instance NOT FOUND for {bot['name']}!\")\n                        print(f\"   Available strategies: {list(self.strategies.keys())}\")\n                        continue\n                    \n\2"

    if re.search(search_pattern, content):
        content = re.sub(search_pattern, replacement, content)
        print("✅ Added error logging for missing Grid strategy instances")

        with open(file_path, 'w') as f:
            f.write(content)

        print(f"✅ Updated {file_path}")
        return True
    else:
        print("⚠️  Could not find exact pattern to replace")
        print("Manual fix needed:")
        print("""
Add this after line 'strategy_instance = self.strategies.get(bot['name'])':

                    # DEBUG: Check if strategy instance exists
                    if not strategy_instance:
                        print(f"❌ [GRID ERROR] Strategy instance NOT FOUND for {bot['name']}!")
                        print(f"   Available strategies: {list(self.strategies.keys())}")
                        continue
""")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Grid Bot Debug Logging Fix")
    print("=" * 60)
    print()

    success = fix_grid_debug_logging()

    if success:
        print("\n✅ Fix applied successfully!")
        print("\nNext steps:")
        print("1. Review the changes in core/engine.py")
        print("2. Copy updated file to VPS")
        print("3. Restart test to see better error messages")
    else:
        print("\n⚠️  Manual fix required - see instructions above")
