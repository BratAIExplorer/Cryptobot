#!/usr/bin/env python3
"""Quick stats on P&L with fee impact"""
import sqlite3

conn = sqlite3.connect('data/trades.db')
c = conn.cursor()

# Get overall stats
c.execute('SELECT COUNT(*) FROM trades')
total_trades = c.fetchone()[0]

c.execute('SELECT SUM(fee) FROM trades')
total_fees = c.fetchone()[0] or 0

c.execute('SELECT SUM(profit) FROM positions WHERE status="CLOSED"')
total_pnl = c.fetchone()[0] or 0

print(f"Total trades: {total_trades}")
print(f"Total fees logged: ${total_fees:.2f}")
print(f"Total P&L (gross): ${total_pnl:.2f}")
print(f"Estimated fees for all trades: ${total_trades * 1.60:.2f}")  # Avg $1.60 per round trip
print(f"Adjusted P&L (after fees): ${total_pnl - (total_trades * 0.80):.2f}")  # Rough estimate

conn.close()
