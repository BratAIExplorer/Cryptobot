import sqlite3
import pandas as pd

conn = sqlite3.connect('crypto_trading_bot/data/trades.db')

print("=" * 100)
print("CLOSED POSITIONS WITH P&L")
print("=" * 100)

query = """
SELECT 
    id, 
    symbol, 
    strategy, 
    buy_price, 
    sell_price, 
    profit,
    buy_timestamp, 
    sell_timestamp 
FROM positions 
WHERE status='CLOSED' 
ORDER BY sell_timestamp DESC
"""

df = pd.read_sql_query(query, conn)
if not df.empty:
    print(df.to_string(index=False))
    print(f"\nTotal Realized P&L: ${df['profit'].sum():.2f}")
    wins = (df['profit'] > 0).sum()
    print(f"Win Rate: {wins}/{len(df)} = {wins/len(df)*100:.1f}%")
else:
    print("No closed positions")

print("\n" + "=" * 100)
print("BOT STATUS TABLE (Dashboard Values)")
print("=" * 100)

query2 = "SELECT * FROM bot_status"
df_status = pd.read_sql_query(query2, conn)
print(df_status.to_string(index=False))

conn.close()
