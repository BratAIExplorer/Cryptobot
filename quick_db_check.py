#!/usr/bin/env python3
"""Quick database check script"""
import sqlite3
import os
from datetime import datetime

db_path = 'data/trades_v3_paper.db.backup_20251230_083843'
print(f'DATABASE ANALYSIS: {db_path}')
print(f'Size: {os.path.getsize(db_path) / (1024*1024):.1f} MB')
print('=' * 80)

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f'\nTables found: {len(tables)}')
    print(f'   {", ".join(tables)}')

    # Bot status
    if 'bot_status' in tables:
        print('\n' + '=' * 80)
        print('BOT STATUS')
        print('=' * 80)
        c.execute('''SELECT strategy, exchange, active, total_pnl, winning_trades, losing_trades,
                     win_rate, last_trade_time FROM bot_status ORDER BY total_pnl DESC''')
        bots = c.fetchall()
        for bot in bots:
            strategy, exchange, active, pnl, wins, losses, win_rate, last_trade = bot
            status_icon = 'ACTIVE' if active else 'INACTIVE'
            print(f'\n{strategy} ({exchange}):')
            print(f'  Status: {status_icon}')
            print(f'  PnL: ${pnl if pnl else 0:.2f}')
            print(f'  Trades: {(wins or 0) + (losses or 0)} (W:{wins or 0} L:{losses or 0})')
            print(f'  Win Rate: {win_rate if win_rate else 0:.1f}%')
            print(f'  Last Trade: {last_trade or "Never"}')

    # Trade statistics
    if 'trades' in tables:
        print('\n' + '=' * 80)
        print('TRADE STATISTICS')
        print('=' * 80)

        # Total trades
        c.execute('SELECT COUNT(*) FROM trades')
        total_trades = c.fetchone()[0]
        print(f'\nTotal Trades: {total_trades}')

        if total_trades > 0:
            # Date range
            c.execute('SELECT MIN(timestamp), MAX(timestamp) FROM trades')
            first, last = c.fetchone()
            print(f'Period: {first} to {last}')

            # By side
            c.execute("SELECT side, COUNT(*), SUM(cost) FROM trades GROUP BY side")
            for side, count, total in c.fetchall():
                print(f'  {side}: {count} trades, ${total if total else 0:.2f} volume')

            # PnL analysis
            c.execute("SELECT COUNT(*), SUM(pnl), AVG(pnl) FROM trades WHERE side='SELL' AND pnl IS NOT NULL")
            sell_count, total_pnl, avg_pnl = c.fetchone()
            if sell_count and sell_count > 0:
                print(f'\nRealized PnL:')
                print(f'  Closed trades: {sell_count}')
                print(f'  Total PnL: ${total_pnl if total_pnl else 0:.2f}')
                print(f'  Avg PnL: ${avg_pnl if avg_pnl else 0:.2f}')

            # By strategy
            print(f'\nBy Strategy:')
            c.execute("""SELECT strategy, COUNT(*) as trade_count,
                       SUM(CASE WHEN side='SELL' AND pnl > 0 THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN side='SELL' AND pnl < 0 THEN 1 ELSE 0 END) as losses,
                       SUM(CASE WHEN side='SELL' THEN pnl ELSE 0 END) as total_pnl
                       FROM trades GROUP BY strategy ORDER BY total_pnl DESC""")
            for strategy, count, wins, losses, pnl in c.fetchall():
                win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                print(f'  {strategy}: {count} trades, PnL:${pnl if pnl else 0:.2f}, WR:{win_rate:.1f}%')

            # Top symbols
            print(f'\nTop Performing Symbols:')
            c.execute("""SELECT symbol, SUM(pnl) as total_pnl, COUNT(*) as trades
                       FROM trades WHERE side='SELL' AND pnl IS NOT NULL
                       GROUP BY symbol ORDER BY total_pnl DESC LIMIT 10""")
            for symbol, pnl, count in c.fetchall():
                print(f'  {symbol}: ${pnl if pnl else 0:.2f} ({count} trades)')

    # Open positions
    if 'positions' in tables:
        print('\n' + '=' * 80)
        print('OPEN POSITIONS')
        print('=' * 80)

        c.execute("SELECT COUNT(*), SUM(position_size_usd) FROM positions WHERE status='OPEN'")
        open_count, open_value = c.fetchone()
        print(f'\nOpen Positions: {open_count or 0}')
        print(f'Total Value: ${open_value if open_value else 0:.2f}')

        if open_count and open_count > 0:
            c.execute("""SELECT strategy, symbol, entry_price, position_size_usd, entry_date,
                       unrealized_pnl_usd FROM positions WHERE status='OPEN' ORDER BY entry_date DESC LIMIT 10""")
            print(f'\nMost Recent Open Positions:')
            for strategy, symbol, entry, size, date, pnl in c.fetchall():
                print(f'  {symbol} ({strategy}): ${size if size else 0:.2f} @ ${entry if entry else 0:.2f} - {date} - PnL:${pnl if pnl else 0:.2f}')

    # Circuit breaker status
    if 'circuit_breaker' in tables:
        print('\n' + '=' * 80)
        print('CIRCUIT BREAKER STATUS')
        print('=' * 80)

        c.execute('SELECT strategy, active, trigger_reason, triggered_at FROM circuit_breaker WHERE active=1')
        active_breakers = c.fetchall()
        if active_breakers:
            for strategy, active, reason, triggered in active_breakers:
                print(f'  WARNING: {strategy}: {reason} (since {triggered})')
        else:
            print('  OK: No active circuit breakers')

    conn.close()
    print('\n' + '=' * 80)

except Exception as e:
    print(f'\nError: {e}')
    import traceback
    traceback.print_exc()
