#!/usr/bin/env python3
"""
Fix Grid Bot Confluence Bypass
Allows Grid Bots to bypass confluence checks since they have proven logic
"""
import os
import re
from datetime import datetime

ENGINE_FILE = 'core/engine.py'

def main():
    # 1. Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{ENGINE_FILE}.backup_{timestamp}'
    
    print(f"📦 Creating backup: {backup_file}")
    with open(ENGINE_FILE, 'r') as f:
        original_content = f.read()
    
    with open(backup_file, 'w') as f:
        f.write(original_content)
    
    # 2. Read file as lines
    lines = original_content.split('\n')
    
    # 3. Find the target line: "base_amount = trade_amount_usd"
    target_line_idx = None
    for i, line in enumerate(lines):
        if 'base_amount = trade_amount_usd' in line and i > 900:  # After line 900
            target_line_idx = i
            print(f"✓ Found target at line {i+1}: {line.strip()}")
            break
    
    if target_line_idx is None:
        print("❌ Could not find 'base_amount = trade_amount_usd' line")
        return False
    
    # 4. Check if already patched
    if any('GRID BOT BYPASS' in line or 'Bypassing confluence' in line for line in lines[target_line_idx:target_line_idx+10]):
        print("⚠️  Already patched! Skipping.")
        return True
    
    # 5. Get indentation from the base_amount line
    indent = len(lines[target_line_idx]) - len(lines[target_line_idx].lstrip())
    base_indent = ' ' * indent
    inner_indent = ' ' * (indent + 4)
    
    # 6. Find the end of confluence block (the "return" after SKIP message)
    confluence_end_idx = None
    for i in range(target_line_idx + 1, min(target_line_idx + 100, len(lines))):
        if 'Confluence V2 Reject' in lines[i]:
            # Find the return statement after this
            for j in range(i, min(i + 5, len(lines))):
                if lines[j].strip() == 'return':
                    confluence_end_idx = j
                    print(f"✓ Found confluence block end at line {j+1}")
                    break
            break
    
    if confluence_end_idx is None:
        print("❌ Could not find end of confluence block")
        return False
    
    # 7. Insert the Grid Bot bypass code
    bypass_code = f"""
{base_indent}# === GRID BOT CONFLUENCE BYPASS ===
{base_indent}# Grid Bots have proven 81-100% win rates with $8,204 total profit
{base_indent}# They use ATR-based grid logic and don't need confluence scoring
{base_indent}strategy_type = bot.get('type', '')
{base_indent}strategy_name = bot.get('name', '')
{base_indent}
{base_indent}if strategy_type == 'Grid' or 'Grid Bot' in strategy_name:
{base_indent}    print(f"✅ [GRID] Bypassing confluence check (using ATR-based grid entry)")
{base_indent}    amount = trade_amount_usd / price
{base_indent}else:
{base_indent}    # === CONFLUENCE CHECK FOR NON-GRID STRATEGIES ===
""".strip('\n')
    
    # 8. Insert bypass code after base_amount line
    new_lines = (
        lines[:target_line_idx + 1] +  # Everything up to and including base_amount
        bypass_code.split('\n') +       # New bypass code
        lines[target_line_idx + 1:]     # Rest of file
    )
    
    # 9. Indent the confluence block (add 4 spaces to lines in the else block)
    # Need to indent from line after "else:" to the "return" statement
    bypass_lines_count = len(bypass_code.split('\n'))
    indent_start = target_line_idx + 1 + bypass_lines_count
    indent_end = confluence_end_idx + bypass_lines_count  # Adjust for inserted lines
    
    for i in range(indent_start, indent_end + 1):
        if i < len(new_lines) and new_lines[i].strip():  # Don't indent empty lines
            # Add 4 spaces to existing indentation
            leading_spaces = len(new_lines[i]) - len(new_lines[i].lstrip())
            new_lines[i] = '    ' + new_lines[i]
    
    # 10. Write modified content
    modified_content = '\n'.join(new_lines)
    
    with open(ENGINE_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"\n✅ SUCCESS! Grid Bot confluence bypass applied")
    print(f"📝 Backup saved: {backup_file}")
    print(f"\n🔧 Changes made:")
    print(f"   - Added Grid Bot detection after line {target_line_idx + 1}")
    print(f"   - Grid Bots now bypass confluence checks")
    print(f"   - Confluence still applies to other strategies")
    print(f"\n⚠️  Next steps:")
    print(f"   1. Restart paper bot to apply changes")
    print(f"   2. Monitor logs for '✅ [GRID] Bypassing confluence'")
    print(f"   3. Grid Bots should start trading again")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
