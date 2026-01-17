#!/usr/bin/env python3
"""
Live Bot Monitor - Watch for trades and check blocker status
Run for 5 minutes to verify fixes are working
"""
import time
import subprocess
import sys

def tail_log(lines=50):
    """Get last N lines from bot.log"""
    try:
        result = subprocess.run(['tail', f'-{lines}', 'bot.log'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return ""

def check_for_issues(log_text):
    """Check for known blocker patterns"""
    issues = []

    # Check for blockers
    if "Daily loss limit reached" in log_text:
        issues.append("❌ DAILY LOSS LIMIT - Should be bypassed!")

    if "Portfolio Correlation Risk (EXTREME)" in log_text or "Portfolio Correlation Risk (HIGH)" in log_text:
        issues.append("❌ CORRELATION BLOCKING - Should be disabled!")

    if "Confluence V2 Reject" in log_text and "Score" in log_text:
        # Extract score if possible
        for line in log_text.split('\n'):
            if "Confluence V2 Reject" in line:
                issues.append(f"⚠️  CONFLUENCE: {line.strip()}")

    if "Position size" in log_text and "exceeds limit" in log_text:
        issues.append("❌ POSITION SIZE LIMIT - Should be 10% now!")

    # Check for good signs
    good_signs = []

    if "Paper mode detected (portfolio < $10k) - skipping correlation checks" in log_text:
        good_signs.append("✅ Correlation disabled (paper mode)")

    if "Daily loss calculation anomaly" in log_text and "bypassing" in log_text:
        good_signs.append("✅ Daily loss bypass active")

    if "Trade approved for" in log_text:
        # Count approvals
        approvals = log_text.count("Trade approved for")
        good_signs.append(f"✅ {approvals} trades approved")

    if "BUY signal" in log_text or "Grid Entry" in log_text or "Dip detected" in log_text:
        signals = log_text.count("BUY signal") + log_text.count("Grid Entry") + log_text.count("Dip detected")
        good_signs.append(f"✅ {signals} buy signals detected")

    return issues, good_signs

def main():
    print("=" * 80)
    print("🔍 LIVE BOT MONITOR - Watching for 5 minutes")
    print("=" * 80)
    print()
    print("This will check every 30 seconds for:")
    print("  ✅ Trades being approved")
    print("  ✅ Correlation disabled messages")
    print("  ✅ Buy signals")
    print("  ❌ Blocker errors (correlation, loss limit, etc.)")
    print()
    print("Press Ctrl+C to stop early")
    print("=" * 80)
    print()

    start_time = time.time()
    check_count = 0
    total_issues = []
    total_good = []

    try:
        while time.time() - start_time < 300:  # 5 minutes
            check_count += 1
            elapsed = int(time.time() - start_time)

            print(f"\n⏱️  Check #{check_count} (t+{elapsed}s)")
            print("-" * 80)

            log_text = tail_log(100)
            issues, good_signs = check_for_issues(log_text)

            # Show new good signs
            for sign in good_signs:
                if sign not in total_good:
                    print(sign)
                    total_good.append(sign)

            # Show new issues
            for issue in issues:
                if issue not in total_issues:
                    print(issue)
                    total_issues.append(issue)

            if not good_signs and not issues:
                print("⏳ No activity yet...")

            # Wait 30 seconds before next check
            if time.time() - start_time < 300:
                time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")

    # Final summary
    print("\n" + "=" * 80)
    print("📊 MONITORING SUMMARY")
    print("=" * 80)
    print()

    print(f"Duration: {int(time.time() - start_time)}s")
    print(f"Checks: {check_count}")
    print()

    if total_good:
        print("✅ POSITIVE SIGNS:")
        for sign in total_good:
            print(f"  {sign}")
    else:
        print("⚠️  No positive signs detected yet")

    print()

    if total_issues:
        print("❌ ISSUES DETECTED:")
        for issue in total_issues:
            print(f"  {issue}")
        print()
        print("🔧 ACTION NEEDED: Check FIXES_REQUIRED.md for solutions")
    else:
        print("✅ No blockers detected!")

    print()
    print("=" * 80)
    print()
    print("Next steps:")
    print("  • View full logs:     tail -f bot.log")
    print("  • Check positions:    python3 check_position_sell_targets.py")
    print("  • Performance report: python3 check_all_bots.py")
    print()

if __name__ == "__main__":
    main()
