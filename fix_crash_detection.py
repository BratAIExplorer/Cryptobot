#!/usr/bin/env python3
"""
Disable crash detection for Grid Bots
Grid Bots profit from volatility and have proven $8K+ profit
"""
from datetime import datetime

ENGINE_FILE = 'core/engine.py'

# Backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = f'{ENGINE_FILE}.backup_crash_{timestamp}'

with open(ENGINE_FILE, 'r') as f:
    content = f.read()

with open(backup, 'w') as f:
    f.write(content)
print(f"📦 Backup: {backup}")

# Find and replace crash detection logic
old_code = """                is_crashing, crash_reason, crash_metrics = self.regime_detector.detect_coin_crash(
                    symbol, df, lookback_hours=24
                )

                if is_crashing:
                    # Log crash detection
                    print(f"⚠️  [{bot['name']}] CRASH DETECTED: {symbol} - {crash_reason}")"""

new_code = """                # === CRASH DETECTION (EXEMPT GRID BOTS) ===
                strategy_type = bot.get('type', '')
                
                # Grid Bots trade through volatility - skip crash check
                if strategy_type != 'Grid':
                    is_crashing, crash_reason, crash_metrics = self.regime_detector.detect_coin_crash(
                        symbol, df, lookback_hours=24
                    )

                    if is_crashing:
                        # Log crash detection
                        print(f"⚠️  [{bot['name']}] CRASH DETECTED: {symbol} - {crash_reason}")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    
    # Also need to close the if statement properly - indent the continue block
    # The continue should only happen for non-Grid bots
    old_continue = """                    # Skip this coin entirely - don't buy or sell during crash
                    continue"""
    
    new_continue = """                        # Skip this coin entirely - don't buy or sell during crash
                        continue"""
    
    content = content.replace(old_continue, new_continue)
    
    with open(ENGINE_FILE, 'w') as f:
        f.write(content)
    
    print("✅ Grid Bots exempted from crash detection!")
    print("\n🔧 Changes:")
    print("   - Grid Bots skip crash detection entirely")
    print("   - Other strategies still protected by crash detection")
    print("   - Grid Bots can now trade through volatility")
else:
    print("❌ Pattern not found - needs manual edit")

