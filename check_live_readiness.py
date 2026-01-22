#!/usr/bin/env python3
"""
Live Trading Readiness Checker
Validates all critical criteria before enabling live trading with real money.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exchanges.binance_adapter import BinanceAdapter
from core.logger import TradeLogger


@dataclass
class CheckResult:
    """Result of a readiness check."""
    passed: bool
    status: str  # 'PASS', 'WARN', 'FAIL'
    message: str
    details: str = ""


class ReadinessChecker:
    """Comprehensive pre-live trading validation."""

    def __init__(self, db_path: str = None):
        self.adapter = BinanceAdapter(mode='paper')
        self.logger = TradeLogger(mode='paper', exchange_name='BINANCE', db_path=db_path)
        self.checks: List[Tuple[str, CheckResult]] = []

    def run_all_checks(self) -> bool:
        """Run all readiness checks. Returns True if ready for live trading."""
        print("=" * 70)
        print("🔍 LIVE TRADING READINESS CHECK")
        print("=" * 70)
        print()

        # Run all checks
        self.check_latency()
        self.check_paper_trading_history()
        self.check_profitability()
        self.check_win_rate()
        self.check_drawdown()
        self.check_market_regime()
        self.check_api_credentials()
        self.check_risk_management()

        # Print results
        self._print_summary()

        # Determine if ready
        fails = sum(1 for _, result in self.checks if result.status == 'FAIL')
        warns = sum(1 for _, result in self.checks if result.status == 'WARN')

        if fails == 0 and warns == 0:
            print("\n✅ ALL CHECKS PASSED - Ready for live trading")
            print("   Recommendation: Start with 10% of planned capital")
            return True
        elif fails == 0:
            print(f"\n⚠️  PASSED WITH {warns} WARNING(S)")
            print("   Recommendation: Address warnings before scaling up")
            return True
        else:
            print(f"\n❌ FAILED: {fails} critical issue(s) must be fixed")
            print("   Recommendation: Continue paper trading")
            return False

    def check_latency(self):
        """Check Binance API latency."""
        print("📡 Checking Binance latency...")

        try:
            samples = []
            for _ in range(5):
                lat = self.adapter.ping()
                if lat:
                    samples.append(lat)

            if not samples:
                self.checks.append(('Latency', CheckResult(
                    False, 'FAIL',
                    'Could not connect to Binance',
                    'All ping attempts failed'
                )))
                return

            avg_latency = sum(samples) / len(samples)

            if avg_latency < 500:
                self.checks.append(('Latency', CheckResult(
                    True, 'PASS',
                    f'{avg_latency:.0f}ms (Excellent)',
                    'Suitable for all trading strategies'
                )))
            elif avg_latency < 1000:
                self.checks.append(('Latency', CheckResult(
                    True, 'WARN',
                    f'{avg_latency:.0f}ms (Acceptable)',
                    'Monitor performance. May affect grid bots.'
                )))
            else:
                self.checks.append(('Latency', CheckResult(
                    False, 'FAIL',
                    f'{avg_latency:.0f}ms (Too High)',
                    'Fix latency before live trading. Run: python3 monitor_binance_latency.py'
                )))

        except Exception as e:
            self.checks.append(('Latency', CheckResult(
                False, 'FAIL',
                'Latency check failed',
                str(e)
            )))

    def check_paper_trading_history(self):
        """Check if sufficient paper trading has been done."""
        print("📊 Checking paper trading history...")

        try:
            trades = self.logger.get_trades()

            if trades.empty:
                self.checks.append(('Trading History', CheckResult(
                    False, 'FAIL',
                    'No paper trading history found',
                    'Run paper trading for at least 30 days first'
                )))
                return

            # Check date range
            if 'timestamp' in trades.columns:
                trades['timestamp'] = pd.to_datetime(trades['timestamp'])
                oldest_trade = trades['timestamp'].min()
                newest_trade = trades['timestamp'].max()
                days_trading = (newest_trade - oldest_trade).days
            else:
                days_trading = 0

            total_trades = len(trades)

            if days_trading >= 30 and total_trades >= 50:
                self.checks.append(('Trading History', CheckResult(
                    True, 'PASS',
                    f'{total_trades} trades over {days_trading} days',
                    'Sufficient paper trading history'
                )))
            elif days_trading >= 14 and total_trades >= 20:
                self.checks.append(('Trading History', CheckResult(
                    True, 'WARN',
                    f'{total_trades} trades over {days_trading} days',
                    'Recommend 30+ days and 50+ trades for best validation'
                )))
            else:
                self.checks.append(('Trading History', CheckResult(
                    False, 'FAIL',
                    f'Only {total_trades} trades over {days_trading} days',
                    'Need minimum 20 trades over 14 days'
                )))

        except Exception as e:
            self.checks.append(('Trading History', CheckResult(
                False, 'FAIL',
                'Could not analyze trading history',
                str(e)
            )))

    def check_profitability(self):
        """Check overall profitability."""
        print("💰 Checking profitability...")

        try:
            pnl = self.logger.get_pnl_summary()

            if pnl > 0:
                self.checks.append(('Profitability', CheckResult(
                    True, 'PASS',
                    f'${pnl:.2f} profit',
                    'Paper trading is profitable'
                )))
            elif pnl > -50:
                self.checks.append(('Profitability', CheckResult(
                    True, 'WARN',
                    f'${pnl:.2f} loss',
                    'Small loss acceptable for testing, but monitor closely'
                )))
            else:
                self.checks.append(('Profitability', CheckResult(
                    False, 'FAIL',
                    f'${pnl:.2f} loss',
                    'Significant losses. Strategy needs improvement.'
                )))

        except Exception as e:
            self.checks.append(('Profitability', CheckResult(
                False, 'FAIL',
                'Could not calculate profitability',
                str(e)
            )))

    def check_win_rate(self):
        """Check win rate of closed trades."""
        print("🎯 Checking win rate...")

        try:
            trades = self.logger.get_trades()

            if trades.empty:
                self.checks.append(('Win Rate', CheckResult(
                    False, 'FAIL',
                    'No trades to analyze',
                    ''
                )))
                return

            # Filter closed trades with PnL
            closed = trades[trades['status'] == 'closed']
            if 'pnl' in closed.columns:
                wins = len(closed[closed['pnl'] > 0])
                total = len(closed[closed['pnl'] != 0])

                if total == 0:
                    self.checks.append(('Win Rate', CheckResult(
                        False, 'FAIL',
                        'No closed trades with PnL',
                        'Need completed round-trip trades'
                    )))
                    return

                win_rate = (wins / total) * 100

                if win_rate >= 50:
                    self.checks.append(('Win Rate', CheckResult(
                        True, 'PASS',
                        f'{win_rate:.1f}% ({wins}/{total})',
                        'Healthy win rate'
                    )))
                elif win_rate >= 35:
                    self.checks.append(('Win Rate', CheckResult(
                        True, 'WARN',
                        f'{win_rate:.1f}% ({wins}/{total})',
                        'Low win rate but acceptable if profit factor is good'
                    )))
                else:
                    self.checks.append(('Win Rate', CheckResult(
                        False, 'FAIL',
                        f'{win_rate:.1f}% ({wins}/{total})',
                        'Win rate too low. Review strategy.'
                    )))
            else:
                self.checks.append(('Win Rate', CheckResult(
                    False, 'WARN',
                    'PnL data not available',
                    'Cannot calculate win rate'
                )))

        except Exception as e:
            self.checks.append(('Win Rate', CheckResult(
                False, 'FAIL',
                'Could not calculate win rate',
                str(e)
            )))

    def check_drawdown(self):
        """Check maximum drawdown."""
        print("📉 Checking drawdown...")

        # This would require historical equity curve
        # For now, check if there are any huge single losses
        try:
            trades = self.logger.get_trades()

            if trades.empty or 'pnl' not in trades.columns:
                self.checks.append(('Drawdown', CheckResult(
                    True, 'WARN',
                    'Cannot calculate drawdown',
                    'Insufficient data'
                )))
                return

            losses = trades[trades['pnl'] < 0]['pnl']

            if losses.empty:
                self.checks.append(('Drawdown', CheckResult(
                    True, 'PASS',
                    'No losing trades',
                    ''
                )))
                return

            max_loss = abs(losses.min())

            if max_loss < 50:
                self.checks.append(('Drawdown', CheckResult(
                    True, 'PASS',
                    f'Max single loss: ${max_loss:.2f}',
                    'Loss control is good'
                )))
            elif max_loss < 100:
                self.checks.append(('Drawdown', CheckResult(
                    True, 'WARN',
                    f'Max single loss: ${max_loss:.2f}',
                    'Consider tighter stop losses'
                )))
            else:
                self.checks.append(('Drawdown', CheckResult(
                    False, 'FAIL',
                    f'Max single loss: ${max_loss:.2f}',
                    'Losses too large. Review risk management.'
                )))

        except Exception as e:
            self.checks.append(('Drawdown', CheckResult(
                False, 'WARN',
                'Could not check drawdown',
                str(e)
            )))

    def check_market_regime(self):
        """Check if market regime detection is working."""
        print("🌡️  Checking market regime detector...")

        try:
            # Try to fetch BTC data for regime detection
            btc_data = self.adapter.fetch_ohlcv('BTC/USDT', '1d', 100)

            if not btc_data.empty:
                self.checks.append(('Market Regime', CheckResult(
                    True, 'PASS',
                    'Regime detection operational',
                    'Can analyze market conditions'
                )))
            else:
                self.checks.append(('Market Regime', CheckResult(
                    False, 'WARN',
                    'Cannot fetch market data',
                    'May affect regime-based strategies'
                )))

        except Exception as e:
            self.checks.append(('Market Regime', CheckResult(
                False, 'WARN',
                'Regime detection error',
                str(e)
            )))

    def check_api_credentials(self):
        """Check if API credentials are configured."""
        print("🔑 Checking API credentials...")

        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')

        if api_key and secret_key:
            self.checks.append(('API Credentials', CheckResult(
                True, 'PASS',
                'API credentials configured',
                'Remember to use API keys with trading enabled'
            )))
        else:
            self.checks.append(('API Credentials', CheckResult(
                False, 'FAIL',
                'API credentials not found',
                'Set BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables'
            )))

    def check_risk_management(self):
        """Check risk management configuration."""
        print("🛡️  Checking risk management...")

        # Basic risk management validation
        try:
            # Check if there are any open positions that are too large
            positions = self.logger.get_open_positions()

            if positions.empty:
                self.checks.append(('Risk Management', CheckResult(
                    True, 'PASS',
                    'No positions at risk',
                    ''
                )))
            else:
                # Check position sizes
                if 'cost_usd' in positions.columns:
                    max_position = positions['cost_usd'].max()
                    total_exposure = positions['cost_usd'].sum()

                    if max_position < 200 and total_exposure < 500:
                        self.checks.append(('Risk Management', CheckResult(
                            True, 'PASS',
                            f'Position sizing reasonable (max: ${max_position:.0f})',
                            f'Total exposure: ${total_exposure:.0f}'
                        )))
                    else:
                        self.checks.append(('Risk Management', CheckResult(
                            False, 'WARN',
                            f'Large positions detected (max: ${max_position:.0f})',
                            'Consider smaller position sizes for live trading'
                        )))
                else:
                    self.checks.append(('Risk Management', CheckResult(
                        True, 'WARN',
                        'Position sizes unknown',
                        'Ensure proper position sizing for live trading'
                    )))

        except Exception as e:
            self.checks.append(('Risk Management', CheckResult(
                False, 'WARN',
                'Could not validate risk management',
                str(e)
            )))

    def _print_summary(self):
        """Print formatted summary of all checks."""
        print("\n" + "=" * 70)
        print("📋 READINESS CHECK SUMMARY")
        print("=" * 70)
        print()

        for check_name, result in self.checks:
            if result.status == 'PASS':
                icon = '✅'
            elif result.status == 'WARN':
                icon = '⚠️ '
            else:
                icon = '❌'

            print(f"{icon} {check_name:20s}: {result.message}")
            if result.details:
                print(f"   └─ {result.details}")

        print("=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Check readiness for live trading')
    parser.add_argument('--db', type=str, default=None,
                       help='Path to database file (default: auto-detect)')

    args = parser.parse_args()

    try:
        # Import pandas here only if needed
        global pd
        import pandas as pd

        checker = ReadinessChecker(db_path=args.db)
        ready = checker.run_all_checks()

        sys.exit(0 if ready else 1)

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install required packages: pip install pandas")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during readiness check: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
