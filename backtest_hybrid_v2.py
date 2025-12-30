#!/usr/bin/env python3
"""
🧪 HYBRID V2.0 BACKTEST FRAMEWORK
Validates dynamic time-weighted TP strategy against historical data

Strategy to test:
- 0-60 days: 5% TP
- 60-120 days: 8% TP
- 120-180 days: 12% TP + trailing stop
- 180+ days: 15% TP + 10% trailing stop
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal

class HybridV2Backtester:
    """
    Backtest the Hybrid v2.0 strategy against historical trade data
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.results = []

    def get_historical_positions(self):
        """Get all Buy-the-Dip positions from database"""
        conn = sqlite3.connect(self.db_path)

        # Get all buys
        buys = pd.read_sql_query("""
            SELECT * FROM trades
            WHERE strategy='Buy-the-Dip Strategy' AND side='BUY'
            ORDER BY timestamp
        """, conn)

        # Get all sells
        sells = pd.read_sql_query("""
            SELECT * FROM trades
            WHERE strategy='Buy-the-Dip Strategy' AND side='SELL'
            ORDER BY timestamp
        """, conn)

        conn.close()
        return buys, sells

    def simulate_dynamic_tp(self, entry_price, entry_time, price_history):
        """
        Simulate what would have happened with dynamic TP

        Args:
            entry_price: Buy price
            entry_time: Buy timestamp
            price_history: DataFrame of hourly prices after entry

        Returns:
            exit_price, exit_time, hold_days, tp_used
        """
        current_peak = entry_price
        trailing_stop_price = None

        for idx, row in price_history.iterrows():
            current_price = row['price']
            current_time = row['timestamp']

            # Calculate hold duration
            hold_hours = (current_time - entry_time).total_seconds() / 3600
            hold_days = hold_hours / 24

            # Determine TP threshold based on hold time
            if hold_days < 60:
                tp_pct = 0.05  # 5%
                use_trailing = False
            elif hold_days < 120:
                tp_pct = 0.08  # 8%
                use_trailing = False
            elif hold_days < 180:
                tp_pct = 0.12  # 12%
                use_trailing = True
                trailing_pct = 0.08  # 8% trail
            else:
                tp_pct = 0.15  # 15%
                use_trailing = True
                trailing_pct = 0.10  # 10% trail

            # Calculate current profit
            profit_pct = (current_price - entry_price) / entry_price

            # Update peak price
            if current_price > current_peak:
                current_peak = current_price

                # Update trailing stop if active
                if use_trailing and profit_pct > 0:
                    trailing_stop_price = current_peak * (1 - trailing_pct)

            # Check exit conditions

            # 1. Take profit hit
            if profit_pct >= tp_pct:
                return {
                    'exit_price': current_price,
                    'exit_time': current_time,
                    'hold_days': hold_days,
                    'tp_used': f"{tp_pct*100}%",
                    'exit_reason': 'Take Profit',
                    'profit_pct': profit_pct * 100
                }

            # 2. Trailing stop hit
            if trailing_stop_price and current_price <= trailing_stop_price:
                return {
                    'exit_price': current_price,
                    'exit_time': current_time,
                    'hold_days': hold_days,
                    'tp_used': f"{tp_pct*100}% + {trailing_pct*100}% trail",
                    'exit_reason': 'Trailing Stop',
                    'profit_pct': profit_pct * 100
                }

        # Position still open
        return None

    def run_backtest(self):
        """
        Main backtest execution
        """
        print("=" * 80)
        print("🧪 BACKTESTING HYBRID V2.0 STRATEGY")
        print("=" * 80)

        buys, sells = self.get_historical_positions()

        print(f"\nHistorical Data:")
        print(f"  Total Buys: {len(buys)}")
        print(f"  Total Sells: {len(sells)}")

        # For each buy, simulate what would have happened with dynamic TP
        results = []

        for _, buy in buys.iterrows():
            symbol = buy['symbol']
            entry_price = buy['price']
            entry_time = pd.to_datetime(buy['timestamp'])
            position_id = buy.get('position_id')

            # Find if this position was sold
            actual_sell = sells[sells['position_id'] == position_id]

            if not actual_sell.empty:
                # Position was closed
                actual_exit = actual_sell.iloc[0]
                actual_exit_price = actual_exit['price']
                actual_exit_time = pd.to_datetime(actual_exit['timestamp'])
                actual_hold_days = (actual_exit_time - entry_time).total_seconds() / 86400
                actual_profit_pct = (actual_exit_price - entry_price) / entry_price * 100

                # Simulate what Option B would have done
                # (This requires minute-by-minute price data which we don't have)
                # For now, use simplified logic

                if actual_hold_days < 60:
                    simulated_tp = 0.05
                elif actual_hold_days < 120:
                    simulated_tp = 0.08
                elif actual_hold_days < 180:
                    simulated_tp = 0.12
                else:
                    simulated_tp = 0.15

                # Simple simulation: Would TP have been hit?
                if actual_profit_pct >= simulated_tp * 100:
                    option_b_profit = simulated_tp * 100
                    option_b_exit = "Would have sold at TP"
                else:
                    option_b_profit = actual_profit_pct
                    option_b_exit = "Same as actual"

                results.append({
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'actual_exit_price': actual_exit_price,
                    'actual_hold_days': actual_hold_days,
                    'actual_profit_pct': actual_profit_pct,
                    'option_b_tp': simulated_tp * 100,
                    'option_b_profit': option_b_profit,
                    'difference': option_b_profit - actual_profit_pct
                })
            else:
                # Position still open
                results.append({
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'status': 'OPEN',
                    'days_open': (datetime.now() - entry_time).total_seconds() / 86400
                })

        # Analysis
        df_results = pd.DataFrame(results)

        print("\n" + "=" * 80)
        print("📊 BACKTEST RESULTS")
        print("=" * 80)

        closed = df_results[df_results.get('actual_profit_pct').notna()]

        if not closed.empty:
            print(f"\nClosed Positions: {len(closed)}")
            print(f"  Actual Avg Profit: {closed['actual_profit_pct'].mean():.2f}%")
            print(f"  Option B Avg Profit: {closed['option_b_profit'].mean():.2f}%")
            print(f"  Improvement: {closed['difference'].mean():.2f}%")

            print("\nTop 5 Biggest Improvements:")
            print(closed.nlargest(5, 'difference')[['symbol', 'actual_profit_pct', 'option_b_profit', 'difference']])

            print("\nTop 5 Biggest Losses (where Option B worse):")
            print(closed.nsmallest(5, 'difference')[['symbol', 'actual_profit_pct', 'option_b_profit', 'difference']])

        open_positions = df_results[df_results.get('status') == 'OPEN']
        print(f"\nStill Open: {len(open_positions)}")

        return df_results

if __name__ == '__main__':
    # Run backtest
    backtester = HybridV2Backtester('data/trades_v3_paper.db')
    results = backtester.run_backtest()

    # Save results
    results.to_csv('backtest_results_hybrid_v2.csv', index=False)
    print("\n✅ Results saved to backtest_results_hybrid_v2.csv")
