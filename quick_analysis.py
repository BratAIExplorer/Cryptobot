"""
Quick Bot Progress Analysis
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

conn = sqlite3.connect('data/trades.db')

print("\n" + "="*80)
print("🤖 CRYPTO BOT PROGRESS REPORT")
print("="*80)
print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Trading Period
cursor = conn.cursor()
cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM trades')
start, end = cursor.fetchone()
print(f"📅 Trading Period: {start} → {end}")
print()

# Overall Stats
cursor.execute('SELECT COUNT(*) FROM trades')
total_trades = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM trades WHERE side="BUY"')
total_buys = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM trades WHERE side="SELL"')
total_sells = cursor.fetchone()[0]

cursor.execute('SELECT SUM(CASE WHEN side="BUY" THEN -cost WHEN side="SELL" THEN cost ELSE 0 END) FROM trades')
total_pnl = cursor.fetchone()[0] or 0

print("📊 OVERALL STATISTICS:")
print(f"   Total Trades: {total_trades}")
print(f"   Buys: {total_buys} | Sells: {total_sells}")
print(f"   Net P&L: ${total_pnl:.2f}")
print()

# Strategy Breakdown
print("📈 STRATEGY BREAKDOWN:")
print("-" * 80)
query = """
SELECT 
    strategy,
    COUNT(*) as trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    SUM(CASE WHEN side='BUY' THEN -cost WHEN side='SELL' THEN cost ELSE 0 END) as pnl
FROM trades
GROUP BY strategy
ORDER BY trades DESC
"""
df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))
print()

# Open Positions
print("💼 CURRENT HOLDINGS:")
print("-" * 80)
query = """
SELECT 
    symbol,
    strategy,
    price as entry_price,
    amount,
    cost,
    timestamp as entry_time
FROM trades
WHERE side='BUY' 
    AND position_id NOT IN (SELECT position_id FROM trades WHERE side='SELL')
ORDER BY timestamp DESC
"""
df_open = pd.read_sql_query(query, conn)
if not df_open.empty:
    print(df_open.to_string(index=False))
    print(f"\n   Total Positions: {len(df_open)}")
    print(f"   Capital Locked: ${df_open['cost'].sum():.2f}")
else:
    print("   No open positions")
print()

# Recent Activity
print("⏰ LAST 5 TRADES:")
print("-" * 80)
query = """
SELECT 
    timestamp,
    strategy,
    symbol,
    side,
    price,
    cost
FROM trades
ORDER BY timestamp DESC
LIMIT 5
"""
df_recent = pd.read_sql_query(query, conn)
print(df_recent.to_string(index=False))
print()

# Closed Trades Summary
print("✅ CLOSED TRADES PERFORMANCE:")
print("-" * 80)
query = """
SELECT 
    COUNT(*) as closed_trades,
    SUM(s.cost - b.cost) as realized_pnl,
    AVG((s.cost - b.cost) / b.cost * 100) as avg_pnl_pct,
    SUM(CASE WHEN s.cost > b.cost THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN s.cost <= b.cost THEN 1 ELSE 0 END) as losses
FROM trades b
INNER JOIN trades s ON b.position_id = s.position_id
WHERE b.side='BUY' AND s.side='SELL'
"""
cursor.execute(query)
result = cursor.fetchone()
if result[0] > 0:
    closed, pnl, avg_pct, wins, losses = result
    win_rate = wins / closed * 100 if closed > 0 else 0
    print(f"   Closed Trades: {closed}")
    print(f"   Realized P&L: ${pnl:.2f}")
    print(f"   Avg P&L %: {avg_pct:.2f}%")
    print(f"   Win Rate: {win_rate:.1f}% ({wins}W / {losses}L)")
else:
    print("   No closed trades yet")

print()
print("="*80)

conn.close()
