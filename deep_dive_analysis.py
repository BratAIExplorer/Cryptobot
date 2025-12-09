
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/trades.db')

print("="*80)
print("🧐 DEEP DIVE STRATEGY AUDIT")
print("="*80)

# 1. HYPER-SCALPER ANALYSIS
print("\n1. 🤖 HYPER-SCALPER HEALTH CHECK")
print("-" * 40)

query_scalper = """
SELECT 
    (s.cost - b.cost) as pnl,
    ((s.cost - b.cost) / b.cost * 100) as pnl_pct
FROM trades b
INNER JOIN trades s ON b.position_id = s.position_id
WHERE b.side='BUY' AND s.side='SELL' AND b.strategy='Hyper-Scalper Bot'
"""
df_scalper = pd.read_sql_query(query_scalper, conn)

if not df_scalper.empty:
    wins = df_scalper[df_scalper['pnl'] > 0]
    losses = df_scalper[df_scalper['pnl'] <= 0]
    
    avg_win = wins['pnl'].mean() if not wins.empty else 0
    avg_loss = losses['pnl'].mean() if not losses.empty else 0
    
    print(f"Total Closed Trades: {len(df_scalper)}")
    print(f"Win Rate: {(len(wins)/len(df_scalper)*100):.1f}%")
    print(f"Avg WIN:  ${avg_win:.2f}")
    print(f"Avg LOSS: ${avg_loss:.2f}")
    
    if avg_loss != 0:
        risk_reward = abs(avg_win / avg_loss)
        print(f"Risk/Reward Ratio: 1:{risk_reward:.2f}")
        if risk_reward < 1.0:
            print("⚠️  WARNING: You are losing more on bad trades than you make on good ones.")
            print("   (Risking $1.00 to make ${:.2f})".format(risk_reward))
    
else:
    print("No closed scalper trades found.")


# 2. BUY-THE-DIP "BAG" ANALYSIS
print("\n2. 🛍️ BUY-THE-DIP CURRENT BAGS")
print("-" * 40)

# We need current prices to calculate unrealized P&L. 
# Since we can't fetch live prices easily in this script without an API, 
# we will compare Entry Price to the "Last Traded Price" in the DB if available, 
# or just list the entry prices to see how "expensive" they were.

query_dip = """
SELECT 
    symbol,
    price as entry_price,
    timestamp as entry_time,
    amount,
    cost
FROM trades
WHERE strategy='Buy-the-Dip Strategy' 
AND side='BUY'
AND position_id NOT IN (SELECT position_id FROM trades WHERE side='SELL')
ORDER BY timestamp DESC
"""
df_dip = pd.read_sql_query(query_dip, conn)

if not df_dip.empty:
    print(f"Currently holding {len(df_dip)} positions.")
    print("\nRecent Entries:")
    print(df_dip[['symbol', 'entry_price', 'entry_time']].head(5).to_string(index=False))
    print("\nOldest Entries (Stuck Bags?):")
    print(df_dip[['symbol', 'entry_price', 'entry_time']].tail(5).to_string(index=False))
else:
    print("No open Buy-the-Dip positions.")

conn.close()
