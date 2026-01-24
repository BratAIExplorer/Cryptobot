#!/usr/bin/env python3
"""
Analyze Confluence Score Impact on Trade Performance
Run this after 48 hours of trading with min_confluence=0
"""

import sqlite3
import pandas as pd
import sys
import os

def analyze_confluence_impact():
    """
    Analyzes trade outcomes grouped by confluence score ranges
    to determine optimal threshold
    """

    db_path = 'data/multi/trades_paper.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)

    # Fetch all completed trades with confluence scores
    query = """
        SELECT
            symbol,
            entry_price,
            exit_price,
            pnl,
            confluence_score,
            timestamp,
            strategy
        FROM trades
        WHERE exit_price IS NOT NULL
        AND confluence_score IS NOT NULL
        ORDER BY timestamp DESC
    """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"❌ Error reading trades: {e}")
        print("Note: If 'confluence_score' column doesn't exist, you need to update the database schema")
        conn.close()
        return

    conn.close()

    if df.empty:
        print("❌ No trades with confluence scores found")
        print("Make sure the bot is logging confluence_score in the trades table")
        return

    print("=" * 80)
    print("📊 CONFLUENCE SCORE IMPACT ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Trades Analyzed: {len(df)}")
    print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print()

    # Define confluence bins
    bins = [0, 20, 40, 50, 60, 80, 100]
    labels = ['0-20', '21-40', '41-50', '51-60', '61-80', '81-100']

    df['confluence_bin'] = pd.cut(df['confluence_score'], bins=bins, labels=labels, include_lowest=True)

    # Group by confluence range
    grouped = df.groupby('confluence_bin', observed=True).agg({
        'pnl': ['count', 'sum', 'mean', lambda x: (x > 0).sum()],
        'confluence_score': 'mean'
    }).round(2)

    grouped.columns = ['Trade Count', 'Total PnL', 'Avg PnL', 'Wins', 'Avg Confluence']
    grouped['Win Rate %'] = ((grouped['Wins'] / grouped['Trade Count']) * 100).round(1)
    grouped['Profit Factor'] = (grouped['Total PnL'] / grouped['Trade Count']).round(2)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Performance by Confluence Range:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(grouped.to_string())
    print()

    # Recommendation based on data
    print("=" * 80)
    print("🎯 RECOMMENDATIONS")
    print("=" * 80)

    # Find optimal threshold (highest profit factor with reasonable trade count)
    profitable_ranges = grouped[grouped['Total PnL'] > 0]

    if profitable_ranges.empty:
        print("❌ No profitable confluence ranges found!")
        print("⚠️  Strategy may need fundamental changes, not just threshold tuning")
    else:
        print("\n✅ Profitable Ranges:")
        for idx in profitable_ranges.index:
            row = profitable_ranges.loc[idx]
            print(f"   {idx}: {row['Trade Count']} trades, ${row['Total PnL']:.2f} total, "
                  f"{row['Win Rate %']}% win rate")

        # Determine recommended threshold
        best_range = profitable_ranges['Total PnL'].idxmax()
        best_data = profitable_ranges.loc[best_range]

        print(f"\n🏆 Best Performing Range: {best_range}")
        print(f"   - Total P&L: ${best_data['Total PnL']:.2f}")
        print(f"   - Win Rate: {best_data['Win Rate %']}%")
        print(f"   - Trade Count: {int(best_data['Trade Count'])}")

        # Extract lower bound of best range
        if '-' in str(best_range):
            threshold = int(str(best_range).split('-')[0])
            print(f"\n💡 RECOMMENDED min_confluence: {threshold}")
            print(f"   This filters out lower-quality trades while preserving profitable ones")

        # Trade frequency analysis
        total_trades = len(df)
        print(f"\n📈 Trade Frequency Impact:")
        for threshold in [0, 20, 40, 50, 60, 70]:
            count = len(df[df['confluence_score'] >= threshold])
            pct = (count / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = df[df['confluence_score'] >= threshold]['pnl'].mean() if count > 0 else 0
            print(f"   Threshold {threshold}: {count} trades ({pct:.1f}%), Avg PnL: ${avg_pnl:.2f}")

    # Additional insights
    print("\n📊 Additional Insights:")
    print(f"   Overall Win Rate: {(df['pnl'] > 0).sum() / len(df) * 100:.1f}%")
    print(f"   Total P&L: ${df['pnl'].sum():.2f}")
    print(f"   Average P&L per Trade: ${df['pnl'].mean():.2f}")
    print(f"   Best Single Trade: ${df['pnl'].max():.2f}")
    print(f"   Worst Single Trade: ${df['pnl'].min():.2f}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    analyze_confluence_impact()
