
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/trades.db')

print("="*80)
print("🛍️ BUY-THE-DIP PORTFOLIO DEEP DIVE")
print("="*80)

# 1. Configured Coins (Manually synced from run_bot.py for this check)
configured_coins = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT', 
    'ADA/USDT', 'TRX/USDT', 'AVAX/USDT', 'SHIB/USDT', 'DOT/USDT', 'LINK/USDT', 
    'BCH/USDT', 'NEAR/USDT', 'LTC/USDT', 'UNI/USDT', 'PEPE/USDT', 'APT/USDT', 
    'ICP/USDT', 'ETC/USDT'
]

# 2. Get Active Holdings
query_active = """
SELECT 
    symbol,
    count(*) as position_count,
    sum(cost) as total_invested,
    avg(price) as avg_entry_price,
    min(timestamp) as oldest_entry
FROM trades
WHERE strategy='Buy-the-Dip Strategy' 
    AND side='BUY' 
    AND position_id NOT IN (SELECT position_id FROM trades WHERE side='SELL')
GROUP BY symbol
"""
df_active = pd.read_sql_query(query_active, conn)

# 3. Analysis
active_symbols = df_active['symbol'].tolist() if not df_active.empty else []
missing_symbols = [coin for coin in configured_coins if coin not in active_symbols]

print(f"\n✅ ACTIVE HOLDINGS ({len(active_symbols)}/{len(configured_coins)} Configured Coins)")
print("-" * 80)
if not df_active.empty:
    print(df_active.to_string(index=False))
else:
    print("No active holdings.")

print(f"\n❌ NOT PURCHASED YET ({len(missing_symbols)} Coins)")
print("-" * 80)
print(", ".join(missing_symbols))

print("\n📊 STATS")
print(f"Total Invested: ${df_active['total_invested'].sum():.2f}")
print(f"Portfolio Coverage: {len(active_symbols)/len(configured_coins)*100:.1f}%")

conn.close()
