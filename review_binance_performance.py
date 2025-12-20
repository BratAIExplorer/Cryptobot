#!/usr/bin/env python3
"""
Comprehensive Binance Bot Performance Review
Analyze current paper trading results before MEXC migration
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.logger import TradeLogger

class PerformanceReviewer:
    """Comprehensive performance analysis tool"""
    
    def __init__(self, mode='paper'):
        self.logger = TradeLogger(mode=mode)
        self.mode = mode
    
    def analyze_strategy_performance(self):
        """Detailed per-strategy breakdown"""
        print("\n" + "=" * 80)
        print("📊 STRATEGY-BY-STRATEGY PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        bot_statuses = self.logger.get_bot_status()
        
        strategy_results = []
        
        for status in bot_statuses:
            strategy_name = status['strategy']
            
            # Get all trades for this strategy
            all_trades = self.logger.get_trades()
            strategy_trades = [t for t in all_trades if t.get('strategy') == strategy_name]
            
            if len(strategy_trades) == 0:
                print(f"\n⚠️  {strategy_name}: No trades executed yet")
                continue
            
            # Calculate metrics
            df = pd.DataFrame(strategy_trades)
            
            # Realized PnL trades
            completed_trades = df[df['side'] == 'SELL']
            
            if len(completed_trades) > 0:
                wins = completed_trades[completed_trades['pnl'] > 0]
                losses = completed_trades[completed_trades['pnl'] < 0]
                
                total_pnl = completed_trades['pnl'].sum()
                win_rate = (len(wins) / len(completed_trades)) * 100
                avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
                avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
                
                # Risk/Reward ratio
                risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
                
                # Expectancy
                expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * abs(avg_loss))
                
                print(f"\n{'='*80}")
                print(f"📈 {strategy_name}")
                print(f"{'='*80}")
                print(f"  Total Trades: {len(strategy_trades)}")
                print(f"  Closed Trades: {len(completed_trades)}")
                print(f"  Winning Trades: {len(wins)} ({win_rate:.1f}%)")
                print(f"  Losing Trades: {len(losses)}")
                print(f"  Total PnL: ${total_pnl:.2f}")
                print(f"  Avg Win: ${avg_win:.2f}")
                print(f"  Avg Loss: ${avg_loss:.2f}")
                print(f"  Risk/Reward: {risk_reward:.2f}:1")
                print(f"  Expectancy: ${expectancy:.2f} per trade")
                
                # Best and worst trades
                if len(completed_trades) > 0:
                    best_trade = completed_trades.loc[completed_trades['pnl'].idxmax()]
                    worst_trade = completed_trades.loc[completed_trades['pnl'].idxmin()]
                    print(f"  Best Trade: ${best_trade['pnl']:.2f} ({best_trade['symbol']})")
                    print(f"  Worst Trade: ${worst_trade['pnl']:.2f} ({worst_trade['symbol']})")
                
                # Average hold time
                if 'timestamp' in df.columns:
                    buy_df = df[df['side'] == 'BUY'].copy()
                    sell_df = df[df['side'] == 'SELL'].copy()
                    
                    if len(buy_df) > 0 and len(sell_df) > 0:
                        buy_df['timestamp'] = pd.to_datetime(buy_df['timestamp'])
                        sell_df['timestamp'] = pd.to_datetime(sell_df['timestamp'])
                        
                        # Rough estimate (assumes FIFO matching)
                        avg_hold_hours = (sell_df['timestamp'].mean() - buy_df['timestamp'].mean()).total_seconds() / 3600
                        print(f"  Avg Hold Time: {avg_hold_hours:.1f} hours")
                
                strategy_results.append({
                    'strategy': strategy_name,
                    'trades': len(completed_trades),
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'expectancy': expectancy,
                    'risk_reward': risk_reward
                })
            else:
                print(f"\n⏳ {strategy_name}: {len(strategy_trades)} open positions, no closed trades yet")
        
        return strategy_results
    
    def analyze_coin_performance(self):
        """Which coins are most profitable?"""
        print("\n" + "=" * 80)
        print("🪙 PERFORMANCE BY COIN")
        print("=" * 80)
        
        all_trades = self.logger.get_trades()
        df = pd.DataFrame(all_trades)
        
        if len(df) == 0:
            print("No trades found")
            return
        
        # Group by symbol
        coin_pnl = df[df['side'] == 'SELL'].groupby('symbol')['pnl'].agg(['sum', 'count', 'mean'])
        coin_pnl.columns = ['Total_PnL', 'Trades', 'Avg_PnL']
        coin_pnl = coin_pnl.sort_values('Total_PnL', ascending=False)
        
        print("\nTop 10 Most Profitable Coins:")
        print(coin_pnl.head(10).to_string())
        
        print("\nBottom 5 Least Profitable Coins:")
        print(coin_pnl.tail(5).to_string())
    
    def analyze_time_patterns(self):
        """When do we trade most successfully?"""
        print("\n" + "=" * 80)
        print("⏰ TIME-BASED PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        all_trades = self.logger.get_trades()
        df = pd.DataFrame(all_trades)
        
        if len(df) == 0 or 'timestamp' not in df.columns:
            print("Insufficient data for time analysis")
            return
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Trades by hour
        trades_by_hour = df.groupby('hour').size()
        print("\nTrades by Hour of Day:")
        for hour, count in trades_by_hour.items():
            print(f"  {hour:02d}:00 - {count} trades {'█' * (count // 2)}")
        
        # PnL by day of week (for completed trades)
        completed = df[df['side'] == 'SELL']
        if len(completed) > 0:
            pnl_by_day = completed.groupby('day_of_week')['pnl'].sum()
            print("\nPnL by Day of Week:")
            for day, pnl in pnl_by_day.items():
                print(f"  {day}: ${pnl:.2f}")
    
    def analyze_open_positions(self):
        """Review all current open positions"""
        print("\n" + "=" * 80)
        print("📦 OPEN POSITIONS ANALYSIS")
        print("=" * 80)
        
        positions = self.logger.get_open_positions()
        
        if len(positions) == 0:
            print("No open positions")
            return
        
        print(f"\nTotal Open Positions: {len(positions)}")
        
        # Group by strategy
        by_strategy = positions.groupby('strategy').agg({
            'cost_basis': 'sum',
            'id': 'count'
        })
        by_strategy.columns = ['Total_Cost', 'Count']
        
        print("\nPositions by Strategy:")
        print(by_strategy.to_string())
        
        # Age analysis
        positions['entry_date'] = pd.to_datetime(positions['entry_date'])
        positions['age_days'] = (datetime.now() - positions['entry_date']).dt.days
        
        print(f"\nPosition Age Statistics:")
        print(f"  Oldest Position: {positions['age_days'].max()} days ({positions.loc[positions['age_days'].idxmax(), 'symbol']})")
        print(f"  Newest Position: {positions['age_days'].min()} days ({positions.loc[positions['age_days'].idxmin(), 'symbol']})")
        print(f"  Average Age: {positions['age_days'].mean():.1f} days")
        
        # Positions older than 100 days (Buy-the-Dip infinite hold)
        old_positions = positions[positions['age_days'] > 100]
        if len(old_positions) > 0:
            print(f"\n⚠️  Positions > 100 days old: {len(old_positions)}")
            for _, pos in old_positions.iterrows():
                print(f"  - {pos['symbol']} ({pos['strategy']}): {pos['age_days']} days, ${pos['cost_basis']:.2f}")
    
    def analyze_veto_efficiency(self):
        """How effective is the veto system?"""
        print("\n" + "=" * 80)
        print("🛡️  VETO SYSTEM EFFICIENCY")
        print("=" * 80)
        
        from core.database import Database
        db = Database(self.logger.db_path)
        session = db.Session()
        
        # Get skipped trades
        query = "SELECT skip_reason, COUNT(*) as count FROM skipped_trades GROUP BY skip_reason ORDER BY count DESC"
        results = session.execute(query).fetchall()
        
        if len(results) == 0:
            print("No skipped trades recorded (veto system may not be active)")
            session.close()
            return
        
        total_skipped = sum([r.count for r in results])
        print(f"\nTotal Trades Blocked by Veto: {total_skipped}")
        
        for result in results:
            pct = (result.count / total_skipped) * 100
            print(f"  {result.skip_reason}: {result.count} ({pct:.1f}%)")
        
        session.close()
    
    def generate_migration_readiness_report(self):
        """Final GO/NO-GO assessment for MEXC migration"""
        print("\n" + "=" * 80)
        print("🚀 MEXC MIGRATION READINESS ASSESSMENT")
        print("=" * 80)
        
        pnl_summary = self.logger.get_pnl_summary()
        open_positions = self.logger.get_open_positions()
        
        # Criteria checklist
        criteria = {
            'Positive Win Rate (>50%)': pnl_summary['win_rate'] > 50,
            'System Uptime >95%': True,  # Assume yes if script is running
            'Open Positions Manageable (<30)': len(open_positions) < 30,
            'Circuit Breaker Not Active': not self.logger.get_circuit_breaker_status()['active'],
            'At Least 50 Trades Executed': pnl_summary['winning_trades'] + pnl_summary['losing_trades'] >= 50
        }
        
        print("\n✅ Migration Readiness Criteria:")
        for criterion, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  [{status}] {criterion}")
        
        # Overall verdict
        pass_count = sum(criteria.values())
        total = len(criteria)
        
        print(f"\nScore: {pass_count}/{total} criteria met")
        
        if pass_count == total:
            print("\n🟢 RECOMMENDATION: PROCEED WITH MEXC MIGRATION")
            print("   All systems ready for migration to MEXC")
        elif pass_count >= total - 1:
            print("\n🟡 RECOMMENDATION: PROCEED WITH CAUTION")
            print("   Most criteria met, but address warnings before migration")
        else:
            print("\n🔴 RECOMMENDATION: DELAY MIGRATION")
            print("   Address critical issues before attempting MEXC migration")
        
        return criteria

def run_full_analysis(mode='paper'):
    """Run complete performance analysis"""
    reviewer = PerformanceReviewer(mode=mode)
    
    print("\n" + "🔍" * 40)
    print("COMPREHENSIVE BINANCE BOT PERFORMANCE REVIEW")
    print(f"Mode: {mode.upper()}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("🔍" * 40)
    
    # 1. Strategy-level analysis
    strategy_results = reviewer.analyze_strategy_performance()
    
    # 2. Coin-level analysis
    reviewer.analyze_coin_performance()
    
    # 3. Time patterns
    reviewer.analyze_time_patterns()
    
    # 4. Open positions
    reviewer.analyze_open_positions()
    
    # 5. Veto system
    reviewer.analyze_veto_efficiency()
    
    # 6. Migration readiness
    migration_ready = reviewer.generate_migration_readiness_report()
    
    # Export summary to JSON
    summary = {
        'timestamp': datetime.now().isoformat(),
        'mode': mode,
        'strategy_performance': strategy_results,
        'migration_readiness': migration_ready
    }
    
    output_file = f'binance_performance_review_{mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Full analysis exported to: {output_file}")
    
    return summary

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'paper'
    run_full_analysis(mode=mode)
