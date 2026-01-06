#!/usr/bin/env python3
"""
Quick patch to disable crash veto for paper mode
Testnet data is unreliable for crash detection
"""
import sys
import os

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def patch_veto_manager():
    """
    Patch VetoManager to skip crash detection in paper mode
    """
    veto_file = 'core/veto.py'

    print("=" * 80)
    print("🔧 PATCHING VETO MANAGER FOR PAPER MODE")
    print("=" * 80)

    # Read current file
    with open(veto_file, 'r') as f:
        content = f.read()

    # Check if already patched
    if 'PAPER_MODE_SKIP_CRASH' in content:
        print("✅ Already patched!")
        return

    # Find the crash detection method
    if 'def check_crash_veto' in content or 'def detect_crash' in content:
        print("⚠️  Found crash detection method")
        print("   Manual patch needed - see MONITORING_ISSUES_FIX.md")
        print("\n📝 Quick fix: Add this to TradingEngine initialization:")
        print("\n   if TRADING_MODE == 'paper':")
        print("       engine.veto_manager.skip_crash_detection = True")
        print("       print('📝 Paper mode: Crash detection disabled')")
    else:
        print("⚠️  Crash detection method not found")
        print("   Bot may not have crash veto, or it's in a different file")

    print("=" * 80)

if __name__ == '__main__':
    patch_veto_manager()
