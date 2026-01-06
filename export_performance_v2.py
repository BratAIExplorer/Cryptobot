#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database-Agnostic Performance Export Script
Works with both old and new database schemas
"""
import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def export_performance_report(db_path='data/trades_v3.db', output_dir='performance_reports'):
    """Export performance data using raw SQL (schema-independent)"""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.utcnow()
    report_date = timestamp.strftime('%Y-%m-%d')

    print(f"Performance Report Generator - {report_date}")
    print("=" * 60)
    print(f"Database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check database schema
    cursor.execute("PRAGMA table_info(positions)")
    columns = [col[1] for col in cursor.fetchall()]
    has_exchange_col = 'exchange' in columns

    print(f"Database schema: {'NEW (with exchange)' if has_exchange_col else 'OLD (legacy)'}")
    print("=" * 60)

    # ==========================================
    # 1. OPEN POSITIONS
    # ==========================================
    if has_exchange_col:
        cursor.execute("""
            SELECT id, bot_id, symbol, entry_date, entry_price, current_price,
                   position_size_usd, amount, unrealized_pnl_pct, unrealized_pnl_usd, exchange
            FROM positions WHERE status = 'OPEN'
        """)
    else:
        cursor.execute("""
            SELECT id, bot_id, symbol, entry_date, entry_price, current_price,
                   position_size_usd, amount, unrealized_pnl_pct, unrealized_pnl_usd
            FROM positions WHERE status = 'OPEN'
        """)

    open_positions = cursor.fetchall()
    positions_data = []
    total_unrealized_pnl = 0
    total_position_value = 0

    for pos in open_positions:
        entry_date = datetime.fromisoformat(pos[3]) if pos[3] else None
        days_held = (timestamp - entry_date).days if entry_date else 0

        pos_data = {
            'position_id': pos[0],
            'bot_id': pos[1],
            'symbol': pos[2],
            'entry_date': pos[3],
            'entry_price': pos[4],
            'current_price': pos[5],
            'position_size_usd': pos[6],
            'amount': pos[7],
            'unrealized_pnl_pct': pos[8],
            'unrealized_pnl_usd': pos[9],
            'days_held': days_held,
            'exchange': pos[10] if has_exchange_col else 'MEXC'
        }
        positions_data.append(pos_data)

        if pos[9]:  # unrealized_pnl_usd
            total_unrealized_pnl += pos[9]
        if pos[6]:  # position_size_usd
            total_position_value += pos[6]

    print(f"Open Positions: {len(open_positions)}")
    print(f"  Total Value: ${total_position_value:.2f}")
    print(f"  Unrealized P&L: ${total_unrealized_pnl:.2f}")

    # ==========================================
    # 2. RECENT TRADES (Last 7 days)
    # ==========================================
    seven_days_ago = (timestamp - timedelta(days=7)).strftime('%Y-%m-%d')

    if has_exchange_col:
        cursor.execute(f"""
            SELECT timestamp, strategy, symbol, side, price, amount, cost, fee, exchange
            FROM trades WHERE timestamp > '{seven_days_ago}'
            ORDER BY timestamp DESC LIMIT 100
        """)
    else:
        cursor.execute(f"""
            SELECT timestamp, strategy, symbol, side, price, amount, cost, fee
            FROM trades WHERE timestamp > '{seven_days_ago}'
            ORDER BY timestamp DESC LIMIT 100
        """)

    recent_trades = cursor.fetchall()
    trades_data = []

    for trade in recent_trades:
        trades_data.append({
            'timestamp': trade[0],
            'strategy': trade[1],
            'symbol': trade[2],
            'side': trade[3],
            'price': trade[4],
            'amount': trade[5],
            'cost': trade[6],
            'fee': trade[7],
            'exchange': trade[8] if has_exchange_col else 'MEXC'
        })

    print(f"Recent Trades (7 days): {len(recent_trades)}")

    # ==========================================
    # 3. BOT STATUS
    # ==========================================
    try:
        cursor.execute("SELECT strategy, status, total_trades, total_pnl FROM bot_status")
        bot_statuses = cursor.fetchall()

        bots_data = []
        total_pnl_all_bots = 0

        for bot in bot_statuses:
            bot_data = {
                'strategy': bot[0],
                'status': bot[1],
                'total_trades': bot[2],
                'total_pnl': bot[3]
            }
            bots_data.append(bot_data)
            if bot[3]:
                total_pnl_all_bots += bot[3]

        print(f"Active Bots: {len(bot_statuses)}")
        print(f"  Total P&L: ${total_pnl_all_bots:.2f}")
    except:
        bots_data = []
        total_pnl_all_bots = 0
        print("Bot Status: Not available")

    # ==========================================
    # 4. CLOSED TRADES (Last 30 days)
    # ==========================================
    thirty_days_ago = (timestamp - timedelta(days=30)).strftime('%Y-%m-%d')

    cursor.execute(f"""
        SELECT COUNT(*), SUM(CASE WHEN side='SELL' THEN cost ELSE -cost END) as net_pnl
        FROM trades WHERE timestamp > '{thirty_days_ago}'
    """)
    closed_stats = cursor.fetchone()
    total_closed_trades = closed_stats[0] if closed_stats[0] else 0
    realized_pnl_30d = closed_stats[1] if closed_stats[1] else 0

    print(f"Trades (30 days): {total_closed_trades}")
    print(f"  Realized P&L: ${realized_pnl_30d:.2f}")

    # ==========================================
    # 5. BUILD REPORT
    # ==========================================
    report = {
        'report_date': report_date,
        'generated_at': timestamp.isoformat(),
        'database_path': db_path,
        'database_type': 'NEW (MEXC)' if has_exchange_col else 'OLD (Legacy)',
        'summary': {
            'open_positions_count': len(open_positions),
            'total_position_value': total_position_value,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl_30d': realized_pnl_30d,
            'total_pnl_all_time': total_pnl_all_bots,
            'recent_trades_7d': len(recent_trades),
            'total_trades_30d': total_closed_trades
        },
        'open_positions': positions_data,
        'recent_trades_7d': trades_data,
        'bot_statuses': bots_data
    }

    # ==========================================
    # 6. SAVE FILES
    # ==========================================

    # JSON reports
    latest_file = output_path / 'latest_performance.json'
    with open(latest_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {latest_file}")

    archive_file = output_path / f'performance_{report_date}.json'
    with open(archive_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Saved: {archive_file}")

    # Human-readable summary
    summary_file = output_path / 'summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Crypto Bot Performance Summary\n")
        f.write(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Database: {db_path}\n")
        f.write(f"=" * 60 + "\n\n")

        f.write(f"PORTFOLIO OVERVIEW\n")
        f.write(f"-" * 60 + "\n")
        f.write(f"Open Positions:      {len(open_positions)}\n")
        f.write(f"Total Position Value: ${total_position_value:,.2f}\n")
        f.write(f"Unrealized P&L:      ${total_unrealized_pnl:,.2f}\n")
        f.write(f"Realized P&L (30d):  ${realized_pnl_30d:,.2f}\n")
        f.write(f"\n")

        if open_positions:
            f.write(f"OPEN POSITIONS\n")
            f.write(f"-" * 60 + "\n")
            for pos in positions_data:
                f.write(f"{pos['symbol']:<12} | Entry: ${pos['entry_price']:>8.2f} | ")
                f.write(f"P&L: ${pos['unrealized_pnl_usd'] or 0:>8.2f} | ")
                f.write(f"Days: {pos['days_held']:>3}\n")
            f.write(f"\n")

        if bots_data:
            f.write(f"BOT STATUS\n")
            f.write(f"-" * 60 + "\n")
            for bot in bots_data:
                f.write(f"{bot['strategy']:<30} | Trades: {bot['total_trades']:>4} | P&L: ${bot['total_pnl']:>8.2f}\n")

    print(f"Saved: {summary_file}")

    conn.close()

    print("\n" + "=" * 60)
    print("Performance export completed successfully!")
    print("=" * 60)

    return report

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/trades_v3.db'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'performance_reports'

    try:
        export_performance_report(db_path=db_path, output_dir=output_dir)
    except Exception as e:
        print(f"Error generating performance report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
