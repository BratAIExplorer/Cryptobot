#!/usr/bin/env python3
"""
Binance Latency Monitoring Script
Continuously monitors Binance API latency and provides health status.
Can be run standalone or as a background service.
"""
import os
import sys
import time
import json
from datetime import datetime
from statistics import mean, stdev
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exchanges.binance_adapter import BinanceAdapter

class LatencyMonitor:
    """Real-time Binance latency monitor with statistics and alerting."""

    # Thresholds (milliseconds)
    EXCELLENT = 200
    GOOD = 500
    ACCEPTABLE = 1000
    SLOW = 2000
    CRITICAL = 3000

    def __init__(self, samples: int = 10, interval: int = 2):
        """
        Args:
            samples: Number of ping samples to collect
            interval: Seconds between samples
        """
        self.samples = samples
        self.interval = interval
        self.adapter = BinanceAdapter(mode='paper')
        self.results: List[int] = []

    def run_test(self) -> Dict[str, Any]:
        """Run latency test and return statistics."""
        print(f"🔍 Testing Binance latency ({self.samples} samples, {self.interval}s interval)...")
        print("=" * 60)

        self.results = []
        for i in range(self.samples):
            latency = self.adapter.ping()
            if latency is not None:
                self.results.append(latency)
                status_emoji = self._get_status_emoji(latency)
                print(f"  Sample {i+1:2d}/{self.samples}: {latency:4d}ms {status_emoji}")

                if i < self.samples - 1:  # Don't sleep after last sample
                    time.sleep(self.interval)
            else:
                print(f"  Sample {i+1:2d}/{self.samples}: FAILED ❌")
                time.sleep(self.interval)

        return self._calculate_stats()

    def _calculate_stats(self) -> Dict[str, Any]:
        """Calculate statistics from collected samples."""
        if not self.results:
            return {
                'status': 'FAILED',
                'message': 'All ping attempts failed',
                'min': None,
                'max': None,
                'avg': None,
                'stdev': None,
                'success_rate': 0.0
            }

        avg = mean(self.results)
        min_lat = min(self.results)
        max_lat = max(self.results)
        std_dev = stdev(self.results) if len(self.results) > 1 else 0
        success_rate = (len(self.results) / self.samples) * 100

        # Determine overall status based on average
        status = self._get_status(avg)
        message = self._get_status_message(avg)

        return {
            'status': status,
            'message': message,
            'min': min_lat,
            'max': max_lat,
            'avg': round(avg, 1),
            'stdev': round(std_dev, 1),
            'success_rate': round(success_rate, 1),
            'samples': self.results,
            'timestamp': datetime.now().isoformat()
        }

    def _get_status(self, latency: float) -> str:
        """Get status label for latency value."""
        if latency < self.EXCELLENT:
            return 'EXCELLENT'
        elif latency < self.GOOD:
            return 'GOOD'
        elif latency < self.ACCEPTABLE:
            return 'ACCEPTABLE'
        elif latency < self.SLOW:
            return 'SLOW'
        elif latency < self.CRITICAL:
            return 'CRITICAL'
        else:
            return 'UNACCEPTABLE'

    def _get_status_emoji(self, latency: float) -> str:
        """Get emoji for latency value."""
        if latency < self.EXCELLENT:
            return '🟢'
        elif latency < self.GOOD:
            return '✅'
        elif latency < self.ACCEPTABLE:
            return '🟡'
        elif latency < self.SLOW:
            return '🟠'
        elif latency < self.CRITICAL:
            return '🔴'
        else:
            return '🛑'

    def _get_status_message(self, latency: float) -> str:
        """Get detailed status message."""
        if latency < self.EXCELLENT:
            return 'Perfect for all trading strategies including HFT'
        elif latency < self.GOOD:
            return 'Excellent for all strategies including scalping and grid bots'
        elif latency < self.ACCEPTABLE:
            return 'Good for swing trading and dip buying. Monitor for grid bots.'
        elif latency < self.SLOW:
            return 'Marginal for grid bots. Only suitable for swing/position trading.'
        elif latency < self.CRITICAL:
            return 'TOO SLOW for grid bots. High slippage risk. Fix before live trading.'
        else:
            return 'UNACCEPTABLE. Do not trade live. Investigate immediately.'

    def print_report(self, stats: Dict[str, Any]):
        """Print formatted report."""
        print("\n" + "=" * 60)
        print("📊 LATENCY TEST RESULTS")
        print("=" * 60)

        if stats['avg'] is None:
            print(f"❌ Status: {stats['status']}")
            print(f"   {stats['message']}")
            return

        emoji = self._get_status_emoji(stats['avg'])
        print(f"{emoji} Status: {stats['status']}")
        print(f"   {stats['message']}")
        print()
        print(f"  Average:      {stats['avg']:.1f}ms")
        print(f"  Min:          {stats['min']}ms")
        print(f"  Max:          {stats['max']}ms")
        print(f"  Std Dev:      {stats['stdev']:.1f}ms")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print()

        # Trading recommendations
        print("🎯 TRADING READINESS:")
        print("=" * 60)
        avg = stats['avg']

        strategies = [
            ('Scalping/HFT', self.EXCELLENT, avg < self.EXCELLENT),
            ('Grid Bots', self.GOOD, avg < self.GOOD),
            ('Buy-the-Dip', self.ACCEPTABLE, avg < self.ACCEPTABLE),
            ('Swing Trading', self.SLOW, avg < self.SLOW),
        ]

        for strategy, threshold, ready in strategies:
            status = '✅ READY' if ready else '❌ NOT READY'
            print(f"  {strategy:20s} (<{threshold:4d}ms): {status}")

        print("=" * 60)

        # Recommendations
        if avg >= self.CRITICAL:
            print("\n🚨 CRITICAL ACTIONS REQUIRED:")
            print("  1. DO NOT go live with real money")
            print("  2. Check VPS location (should be Singapore/Tokyo/Frankfurt)")
            print("  3. Run diagnostic: ping api.binance.com")
            print("  4. Consider VPS migration to region closer to Binance")
        elif avg >= self.SLOW:
            print("\n⚠️  ACTIONS RECOMMENDED:")
            print("  1. Continue paper trading only")
            print("  2. Disable grid bots for live trading")
            print("  3. Consider VPS optimization or relocation")
            print("  4. Monitor latency trends over 24-48 hours")
        elif avg >= self.ACCEPTABLE:
            print("\n📋 ACTIONS SUGGESTED:")
            print("  1. Continue paper trading for 2-4 weeks")
            print("  2. Monitor latency during peak trading hours")
            print("  3. Grid bots may experience suboptimal performance")
            print("  4. Consider optimization before scaling up")

        print()

    def save_to_log(self, stats: Dict[str, Any], log_file: str = 'logs/latency_history.jsonl'):
        """Append results to log file."""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(stats) + '\n')
            print(f"💾 Results saved to {log_file}")
        except Exception as e:
            print(f"⚠️  Could not save to log: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor Binance API latency')
    parser.add_argument('-s', '--samples', type=int, default=10,
                       help='Number of ping samples (default: 10)')
    parser.add_argument('-i', '--interval', type=int, default=2,
                       help='Interval between samples in seconds (default: 2)')
    parser.add_argument('-c', '--continuous', action='store_true',
                       help='Run continuously (repeat every 5 minutes)')
    parser.add_argument('--no-log', action='store_true',
                       help='Do not save results to log file')

    args = parser.parse_args()

    monitor = LatencyMonitor(samples=args.samples, interval=args.interval)

    try:
        if args.continuous:
            print("🔄 Continuous monitoring mode (Ctrl+C to stop)")
            print()
            while True:
                stats = monitor.run_test()
                monitor.print_report(stats)

                if not args.no_log:
                    monitor.save_to_log(stats)

                print(f"\n⏰ Next check in 5 minutes...\n")
                time.sleep(300)  # 5 minutes
        else:
            stats = monitor.run_test()
            monitor.print_report(stats)

            if not args.no_log:
                monitor.save_to_log(stats)

    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
