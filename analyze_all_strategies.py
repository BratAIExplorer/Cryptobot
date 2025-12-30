#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE STRATEGY PERFORMANCE ANALYSIS
Analyzes all strategies to identify top performers and productionization candidates
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

class StrategyAnalyzer:
    def __init__(self, db_path='data/trades_v3_paper.db'):
        self.db_path = db_path
        self.strategies = [
            'Grid Bot BTC',
            'Grid Bot ETH',
            'SMA Trend Bot',
            'Buy-the-Dip Strategy',
            'Momentum Swing Bot',
            'Hidden Gem Monitor',
            'Dip Sniper'  # Deactivated but check historical
        ]

    def get_strategy_metrics(self, strategy_name):
        """Get comprehensive metrics for a single strategy"""
        conn = sqlite3.connect(self.db_path)

        # Get all trades
        trades_df = pd.read_sql_query(f"""
            SELECT * FROM trades
            WHERE strategy = '{strategy_name}'
            ORDER BY timestamp
        """, conn)

        # Get open positions
        positions_df = pd.read_sql_query(f"""
            SELECT * FROM positions
            WHERE strategy = '{strategy_name}' AND status = 'OPEN'
            ORDER BY buy_timestamp
        """, conn)

        # Get closed positions
        closed_positions_df = pd.read_sql_query(f"""
            SELECT * FROM positions
            WHERE strategy = '{strategy_name}' AND status = 'CLOSED'
            ORDER BY buy_timestamp
        """, conn)

        conn.close()

        if trades_df.empty:
            return {
                'strategy': strategy_name,
                'status': 'NO_DATA',
                'total_trades': 0
            }

        # Calculate metrics
        buys = trades_df[trades_df['side'] == 'BUY']
        sells = trades_df[trades_df['side'] == 'SELL']

        total_trades = len(trades_df)
        total_buys = len(buys)
        total_sells = len(sells)

        # P&L calculation
        total_pnl = trades_df['profit_loss'].sum() if 'profit_loss' in trades_df.columns else 0

        # Win rate (only from sells with profit)
        if not sells.empty and 'profit_loss' in sells.columns:
            profitable_sells = sells[sells['profit_loss'] > 0]
            win_rate = len(profitable_sells) / len(sells) * 100 if len(sells) > 0 else 0
            avg_win = profitable_sells['profit_loss'].mean() if not profitable_sells.empty else 0
            losing_sells = sells[sells['profit_loss'] < 0]
            avg_loss = losing_sells['profit_loss'].mean() if not losing_sells.empty else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0

        # Open positions analysis
        open_positions_count = len(positions_df)
        if not positions_df.empty:
            total_locked_capital = positions_df['position_size_usd'].sum() if 'position_size_usd' in positions_df.columns else 0

            # Calculate unrealized P&L (need current prices - simplified)
            positions_df['buy_timestamp'] = pd.to_datetime(positions_df['buy_timestamp'])
            positions_df['days_open'] = (datetime.now() - positions_df['buy_timestamp']).dt.total_seconds() / 86400

            avg_days_open = positions_df['days_open'].mean()
            max_days_open = positions_df['days_open'].max()
            oldest_position_symbol = positions_df.loc[positions_df['days_open'].idxmax(), 'symbol'] if not positions_df.empty else None
        else:
            total_locked_capital = 0
            avg_days_open = 0
            max_days_open = 0
            oldest_position_symbol = None

        # Time analysis
        if not trades_df.empty:
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
            first_trade = trades_df['timestamp'].min()
            last_trade = trades_df['timestamp'].max()
            days_active = (last_trade - first_trade).total_seconds() / 86400 if last_trade != first_trade else 0
            trades_per_day = total_trades / days_active if days_active > 0 else 0
        else:
            first_trade = None
            last_trade = None
            days_active = 0
            trades_per_day = 0

        # Calculate Sharpe-like ratio (risk-adjusted return)
        if not sells.empty and 'profit_loss' in sells.columns and len(sells) > 1:
            returns_std = sells['profit_loss'].std()
            sharpe_ratio = (avg_win / returns_std) if returns_std > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            'strategy': strategy_name,
            'status': 'ACTIVE' if total_trades > 0 else 'INACTIVE',

            # Trade counts
            'total_trades': total_trades,
            'total_buys': total_buys,
            'total_sells': total_sells,
            'buy_sell_ratio': f"{total_buys}:{total_sells}",

            # P&L
            'total_pnl': float(total_pnl),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'win_rate': float(win_rate),
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,

            # Risk metrics
            'sharpe_ratio': float(sharpe_ratio),

            # Open positions
            'open_positions': open_positions_count,
            'locked_capital': float(total_locked_capital),
            'avg_days_open': float(avg_days_open),
            'max_days_open': float(max_days_open),
            'oldest_position': oldest_position_symbol,

            # Time metrics
            'first_trade': first_trade.strftime('%Y-%m-%d %H:%M') if first_trade else None,
            'last_trade': last_trade.strftime('%Y-%m-%d %H:%M') if last_trade else None,
            'days_active': float(days_active),
            'trades_per_day': float(trades_per_day),

            # Efficiency
            'capital_efficiency': float(total_pnl / total_locked_capital * 100) if total_locked_capital > 0 else 0
        }

    def rank_strategies(self, metrics_list):
        """Rank strategies by multiple criteria"""
        df = pd.DataFrame(metrics_list)
        df = df[df['status'] != 'NO_DATA']

        if df.empty:
            return df

        # Create composite score (0-100)
        # Factors: P&L (40%), Win Rate (20%), Profit Factor (20%), Sharpe (10%), Efficiency (10%)

        # Normalize each metric to 0-100 scale
        if df['total_pnl'].max() > 0:
            df['pnl_score'] = (df['total_pnl'] / df['total_pnl'].max() * 100).clip(0, 100)
        else:
            df['pnl_score'] = 0

        df['win_rate_score'] = df['win_rate'].clip(0, 100)

        if df['profit_factor'].max() > 0:
            df['profit_factor_score'] = (df['profit_factor'] / df['profit_factor'].max() * 100).clip(0, 100)
        else:
            df['profit_factor_score'] = 0

        if df['sharpe_ratio'].max() > 0:
            df['sharpe_score'] = (df['sharpe_ratio'] / df['sharpe_ratio'].max() * 100).clip(0, 100)
        else:
            df['sharpe_score'] = 0

        if df['capital_efficiency'].max() > 0:
            df['efficiency_score'] = (df['capital_efficiency'] / df['capital_efficiency'].max() * 100).clip(0, 100)
        else:
            df['efficiency_score'] = 0

        # Calculate composite score
        df['composite_score'] = (
            df['pnl_score'] * 0.40 +
            df['win_rate_score'] * 0.20 +
            df['profit_factor_score'] * 0.20 +
            df['sharpe_score'] * 0.10 +
            df['efficiency_score'] * 0.10
        )

        # Sort by composite score
        df = df.sort_values('composite_score', ascending=False)

        return df

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("=" * 100)
        print("🔍 COMPREHENSIVE STRATEGY PERFORMANCE ANALYSIS")
        print("=" * 100)
        print()

        # Collect metrics for all strategies
        all_metrics = []
        for strategy in self.strategies:
            print(f"📊 Analyzing: {strategy}...")
            metrics = self.get_strategy_metrics(strategy)
            all_metrics.append(metrics)

        print()
        print("=" * 100)
        print("📈 PERFORMANCE SUMMARY")
        print("=" * 100)
        print()

        # Display individual metrics
        for metrics in all_metrics:
            if metrics['status'] == 'NO_DATA':
                print(f"❌ {metrics['strategy']}: NO DATA")
                print()
                continue

            print(f"{'='*100}")
            print(f"🤖 {metrics['strategy']}")
            print(f"{'='*100}")
            print(f"Status: {metrics['status']}")
            print()

            print(f"📊 TRADING ACTIVITY:")
            print(f"   Total Trades: {metrics['total_trades']}")
            print(f"   Buy:Sell Ratio: {metrics['buy_sell_ratio']}")
            print(f"   Trades/Day: {metrics['trades_per_day']:.2f}")
            print(f"   Active Period: {metrics['days_active']:.1f} days")
            print(f"   First Trade: {metrics['first_trade']}")
            print(f"   Last Trade: {metrics['last_trade']}")
            print()

            print(f"💰 P&L METRICS:")
            print(f"   Total P&L: ${metrics['total_pnl']:.2f}")
            print(f"   Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   Avg Win: ${metrics['avg_win']:.2f}")
            print(f"   Avg Loss: ${metrics['avg_loss']:.2f}")
            print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
            print()

            print(f"📦 OPEN POSITIONS:")
            print(f"   Count: {metrics['open_positions']}")
            print(f"   Locked Capital: ${metrics['locked_capital']:.2f}")
            print(f"   Avg Days Open: {metrics['avg_days_open']:.1f}")
            print(f"   Max Days Open: {metrics['max_days_open']:.1f}")
            if metrics['oldest_position']:
                print(f"   Oldest: {metrics['oldest_position']}")
            print()

            print(f"⚡ EFFICIENCY:")
            print(f"   Capital Efficiency: {metrics['capital_efficiency']:.2f}% return on locked capital")
            print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print()

        # Ranking
        ranked_df = self.rank_strategies(all_metrics)

        if not ranked_df.empty:
            print("=" * 100)
            print("🏆 STRATEGY RANKINGS (Composite Score)")
            print("=" * 100)
            print()

            print(f"{'Rank':<6} {'Strategy':<30} {'Score':<8} {'P&L':<12} {'Win%':<8} {'PF':<8} {'Open':<6}")
            print("-" * 100)

            for idx, row in ranked_df.iterrows():
                rank = ranked_df.index.get_loc(idx) + 1
                print(f"{rank:<6} {row['strategy']:<30} {row['composite_score']:.1f}      ${row['total_pnl']:<10.2f} {row['win_rate']:<6.1f}% {row['profit_factor']:<6.2f}  {row['open_positions']}")

            print()

        # Productionization recommendations
        print("=" * 100)
        print("✅ PRODUCTIONIZATION RECOMMENDATIONS")
        print("=" * 100)
        print()

        if not ranked_df.empty:
            for idx, row in ranked_df.iterrows():
                rank = ranked_df.index.get_loc(idx) + 1
                strategy = row['strategy']
                score = row['composite_score']

                # Determine recommendation
                if score >= 70:
                    recommendation = "🟢 READY FOR PRODUCTION"
                    reason = "Excellent performance, proven track record"
                elif score >= 50:
                    recommendation = "🟡 OPTIMIZE BEFORE PRODUCTION"
                    reason = "Good potential, needs parameter tuning"
                elif score >= 30:
                    recommendation = "🟠 NEEDS MAJOR IMPROVEMENTS"
                    reason = "Underperforming, requires strategy overhaul"
                else:
                    recommendation = "🔴 DEACTIVATE OR REDESIGN"
                    reason = "Poor performance, not viable"

                print(f"{rank}. {strategy}")
                print(f"   Score: {score:.1f}/100")
                print(f"   Recommendation: {recommendation}")
                print(f"   Reason: {reason}")

                # Specific issues
                if row['win_rate'] < 30:
                    print(f"   ⚠️  Low win rate ({row['win_rate']:.1f}%) - improve entry signals")
                if row['open_positions'] > 10:
                    print(f"   ⚠️  Too many open positions ({row['open_positions']}) - capital locked")
                if row['avg_days_open'] > 60:
                    print(f"   ⚠️  Positions held too long ({row['avg_days_open']:.1f} days avg)")
                if row['total_pnl'] < 0:
                    print(f"   🚨 NEGATIVE P&L (${row['total_pnl']:.2f}) - major problem")

                print()

        # Save to CSV
        if not ranked_df.empty:
            output_file = 'strategy_analysis_report.csv'
            ranked_df.to_csv(output_file, index=False)
            print(f"📁 Detailed report saved to: {output_file}")

        return all_metrics, ranked_df

if __name__ == '__main__':
    analyzer = StrategyAnalyzer()
    metrics, rankings = analyzer.generate_report()

    print()
    print("=" * 100)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 100)
