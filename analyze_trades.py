"""
Quick analysis script to check bot performance
"""
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/trades.db')

# 1. Strategy Summary
print("=" * 100)
print("STRATEGY PERFORMANCE SUMMARY")
print("=" * 100)

query = """
SELECT 
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    SUM(CASE WHEN side='BUY' THEN -cost WHEN side='SELL' THEN cost ELSE 0 END) as net_pnl
FROM trades
GROUP BY strategy
"""
df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))
print()

# 2. Open Positions
print("=" * 100)
print("OPEN POSITIONS (Unrealized)")
print("=" * 100)

query = """
SELECT 
    strategy,
    symbol,
    price as buy_price,
    amount,
    cost,
    timestamp as buy_time
FROM trades
WHERE side='BUY' 
    AND position_id NOT IN (SELECT position_id FROM trades WHERE side='SELL')
ORDER BY timestamp DESC
"""
df_open = pd.read_sql_query(query, conn)
if not df_open.empty:
    print(df_open.to_string(index=False))
    print(f"\nTotal Open Positions: {len(df_open)}")
    print(f"Total Capital Locked: ${df_open['cost'].sum():.2f}")
else:
    print("No open positions")
print()

# 3. Closed Positions (Realized P&L)
print("=" * 100)
print("CLOSED POSITIONS (Realized P&L)")
print("=" * 100)

query = """
SELECT 
    b.strategy,
    b.symbol,
    b.price as buy_price,
    s.price as sell_price,
    b.amount,
    b.cost as buy_cost,
    s.cost as sell_cost,
    (s.cost - b.cost) as realized_pnl,
    ((s.cost - b.cost) / b.cost * 100) as pnl_pct,
    b.timestamp as buy_time,
    s.timestamp as sell_time
FROM trades b
INNER JOIN trades s ON b.position_id = s.position_id
WHERE b.side='BUY' AND s.side='SELL'
ORDER BY s.timestamp DESC
"""
df_closed = pd.read_sql_query(query, conn)
if not df_closed.empty:
    print(df_closed.to_string(index=False))
    print(f"\nTotal Closed Trades: {len(df_closed)}")
    print(f"Total Realized P&L: ${df_closed['realized_pnl'].sum():.2f}")
    print(f"Win Rate: {(df_closed['realized_pnl'] > 0).sum() / len(df_closed) * 100:.1f}%")
else:
    print("No closed positions yet")
print()

# 4. Recent Activity
print("=" * 100)
print("LAST 10 TRADES")
print("=" * 100)

query = """
SELECT 
    timestamp,
    strategy,
    symbol,
    side,
    price,
    amount,
    cost
FROM trades
ORDER BY timestamp DESC
LIMIT 10
"""
df_recent = pd.read_sql_query(query, conn)
print(df_recent.to_string(index=False))
print()

conn.close()
