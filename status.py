#!/usr/bin/env python3
"""
Quick Status Dashboard
Shows current system health at a glance.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exchanges.binance_adapter import BinanceAdapter
from core.logger import TradeLogger


def get_status_icon(value, thresholds):
    """Get status icon based on value and thresholds (lower is better)."""
    excellent, good, acceptable = thresholds
    if value < excellent:
        return '🟢'
    elif value < good:
        return '✅'
    elif value < acceptable:
        return '🟡'
    else:
        return '🔴'


def main():
    """Display quick status dashboard."""
    print("=" * 60)
    print(f"⚡ CRYPTOBOT STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 1. Exchange Connectivity
    print("📡 EXCHANGE CONNECTIVITY")
    print("-" * 60)
    try:
        adapter = BinanceAdapter(mode='paper')

        # Ping test
        latency = adapter.ping()
        if latency:
            icon = get_status_icon(latency, (200, 500, 1000))
            print(f"  Binance:  {icon} {latency}ms")

            if latency < 200:
                print("  Status:   ✅ Excellent - Ready for all strategies")
            elif latency < 500:
                print("  Status:   ✅ Good - Ready for live trading")
            elif latency < 1000:
                print("  Status:   🟡 Acceptable - Monitor grid bots")
            else:
                print("  Status:   🔴 Slow - Fix before live trading")
        else:
            print("  Binance:  ❌ OFFLINE")
    except Exception as e:
        print(f"  Binance:  ❌ Error: {e}")

    print()

    # 2. Paper Trading Performance
    print("📊 PAPER TRADING PERFORMANCE")
    print("-" * 60)
    try:
        logger = TradeLogger(mode='paper', exchange_name='BINANCE')

        # Overall PnL
        pnl = logger.get_pnl_summary()
        pnl_icon = '✅' if pnl > 0 else '🔴'
        print(f"  Total PnL:       {pnl_icon} ${pnl:.2f}")

        # Trade count
        trades = logger.get_trades()
        trade_count = len(trades) if not trades.empty else 0
        print(f"  Total Trades:    {trade_count}")

        # Open positions
        positions = logger.get_open_positions()
        open_count = len(positions) if not positions.empty else 0
        print(f"  Open Positions:  {open_count}")

        # Calculate win rate if possible
        if not trades.empty and 'pnl' in trades.columns:
            closed = trades[trades['status'] == 'closed']
            if not closed.empty and 'pnl' in closed.columns:
                wins = len(closed[closed['pnl'] > 0])
                total = len(closed[closed['pnl'] != 0])
                if total > 0:
                    win_rate = (wins / total) * 100
                    wr_icon = '✅' if win_rate >= 50 else '🟡' if win_rate >= 35 else '🔴'
                    print(f"  Win Rate:        {wr_icon} {win_rate:.1f}% ({wins}/{total})")

    except Exception as e:
        print(f"  Error: {e}")

    print()

    # 3. Quick Recommendations
    print("🎯 QUICK ASSESSMENT")
    print("-" * 60)

    try:
        adapter = BinanceAdapter(mode='paper')
        latency = adapter.ping()
        logger = TradeLogger(mode='paper', exchange_name='BINANCE')
        pnl = logger.get_pnl_summary()
        trades = logger.get_trades()
        trade_count = len(trades) if not trades.empty else 0

        # Determine readiness
        issues = []
        warnings = []

        if not latency or latency > 1000:
            issues.append("High latency - Fix before live trading")
        elif latency > 500:
            warnings.append("Elevated latency - Monitor closely")

        if trade_count < 20:
            issues.append("Insufficient trading history (need 20+ trades)")
        elif trade_count < 50:
            warnings.append("Limited trading history (recommend 50+ trades)")

        if pnl < -50:
            issues.append("Significant losses - Strategy needs work")
        elif pnl < 0:
            warnings.append("Currently unprofitable - Monitor closely")

        if issues:
            print("  ❌ NOT READY FOR LIVE TRADING")
            for issue in issues:
                print(f"     • {issue}")
        elif warnings:
            print("  ⚠️  PROCEED WITH CAUTION")
            for warning in warnings:
                print(f"     • {warning}")
            print()
            print("  💡 Recommendation: Continue paper trading")
        else:
            print("  ✅ SYSTEM LOOKS HEALTHY")
            print("     • Latency is good")
            print("     • Has trading history")
            print("     • Paper trading profitable")
            print()
            print("  💡 Next step: Run detailed readiness check:")
            print("     python3 check_live_readiness.py")

    except Exception as e:
        print(f"  ❌ Cannot assess readiness: {e}")

    print()
    print("=" * 60)
    print("💡 TIP: Run 'python3 monitor_binance_latency.py' for detailed latency analysis")
    print("=" * 60)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
