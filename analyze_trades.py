"""
Quick analysis script to check bot performance with REALIZED vs UNREALIZED PnL
"""
import sqlite3
import pandas as pd
import requests
import time
import os

# Connect to database
possible_paths = [
    'data/multi/trades_paper.db',  # V3 multi-exchange (CURRENT)
    'data/trades_paper.db',         # V2 paper mode
    'data/trades.db',               # V1 live mode
    'trades_paper.db',              # Legacy location
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if db_path is None:
    print("❌ ERROR: No database file found!")
    exit(1)

print(f"📊 Reading Database: {db_path}")
conn = sqlite3.connect(db_path)

def get_current_prices(symbols):
    """Fetch current prices from Binance for accurate Unrealized PnL"""
    if not symbols:
        return {}
    
    # Clean symbols (remove /USDT for API if needed, but Binance takes symbol=BTCUSDT)
    # Our DB uses 'BTC/USDT', Binance uses 'BTCUSDT'
    clean_symbols = [s.replace('/', '') for s in symbols]
    prices = {}
    
    print(f"🌍 Fetching live prices for {len(clean_symbols)} assets...")
    try:
        # Batch fetch via ticker/price (efficient)
        resp = requests.get("https://api.binance.com/api/v3/ticker/price")
        data = resp.json()
        
        # Create map
        market_map = {item['symbol']: float(item['price']) for item in data}
        
        # Match back to our format
        for s in symbols:
            clean = s.replace('/', '')
            if clean in market_map:
                prices[s] = market_map[clean]
    except Exception as e:
        print(f"⚠️ Error fetching prices: {e}")
    
    return prices

# 1. Open Positions & Unrealized PnL
print("=" * 100)
print("OPEN POSITIONS (Unrealized PnL)")
print("=" * 100)

query_open = """
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
df_open = pd.read_sql_query(query_open, conn)

unrealized_pnl_total = 0.0
equity_value_total = 0.0

if not df_open.empty:
    unique_symbols = df_open['symbol'].unique().tolist()
    current_prices = get_current_prices(unique_symbols)
    
    # Calculate Unrealized PnL
    df_open['current_price'] = df_open['symbol'].map(current_prices)
    df_open['current_value'] = df_open['amount'] * df_open['current_price']
    df_open['unrealized_pnl'] = df_open['current_value'] - df_open['cost']
    df_open['pnl_pct'] = (df_open['unrealized_pnl'] / df_open['cost']) * 100
    
    # Metrics
    unrealized_pnl_total = df_open['unrealized_pnl'].sum()
    equity_value_total = df_open['current_value'].sum()
    total_invested = df_open['cost'].sum()
    
    # Display top 20 oldest or largest? Let's show aggregated by Coin first
    print(f"Total Invested:   ${total_invested:,.2f}")
    print(f"Current Value:    ${equity_value_total:,.2f}")
    print(f"Unrealized PnL:   ${unrealized_pnl_total:,.2f} ({(unrealized_pnl_total/total_invested)*100:.2f}%)")
    print("-" * 100)
    
    # Group by Strategy + Symbol for cleaner view
    summary = df_open.groupby(['strategy', 'symbol']).agg({
        'amount': 'sum',
        'cost': 'sum',
        'current_value': 'sum',
        'unrealized_pnl': 'sum'
    }).reset_index()
    summary['pnl_pct'] = (summary['unrealized_pnl'] / summary['cost']) * 100
    print(summary.sort_values('unrealized_pnl').to_string(index=False))

else:
    print("No open positions")

print()

# 2. Strategy Performance (Cash Flow vs Realized)
print("=" * 100)
print("STRATEGY PERFORMANCE (Cash Flow vs Realized)")
print("=" * 100)

# Calculate Realized PnL per strategy
query_closed = """
SELECT 
    b.strategy,
    (s.cost - b.cost) as profit
FROM trades b
INNER JOIN trades s ON b.position_id = s.position_id
WHERE b.side='BUY' AND s.side='SELL'
"""
df_closed = pd.read_sql_query(query_closed, conn)
realized_map = df_closed.groupby('strategy')['profit'].sum().to_dict()

# Calculate Cash Flow (Trades table raw)
query_cashflow = """
SELECT 
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side='BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN side='SELL' THEN 1 ELSE 0 END) as sells,
    SUM(CASE WHEN side='BUY' THEN -cost WHEN side='SELL' THEN cost ELSE 0 END) as net_cash_flow
FROM trades
GROUP BY strategy
"""
df_cf = pd.read_sql_query(query_cashflow, conn)

# Merge Realized PnL
df_cf['realized_pnl'] = df_cf['strategy'].map(realized_map).fillna(0)

# Merge Unrealized PnL (from open positions)
if not df_open.empty:
    unrealized_map = df_open.groupby('strategy')['unrealized_pnl'].sum().to_dict()
    df_cf['unrealized_pnl'] = df_cf['strategy'].map(unrealized_map).fillna(0)
    
    # Count open positions
    open_counts = df_open.groupby('strategy').size().to_dict()
    df_cf['open_positions'] = df_cf['strategy'].map(open_counts).fillna(0).astype(int)
else:
    df_cf['unrealized_pnl'] = 0.0
    df_cf['open_positions'] = 0

# Calculate Total PnL (Realized + Unrealized)
df_cf['TOTAL_PNL'] = df_cf['realized_pnl'] + df_cf['unrealized_pnl']

# Reorder columns
cols = ['strategy', 'buys', 'sells', 'open_positions', 'net_cash_flow', 'realized_pnl', 'unrealized_pnl', 'TOTAL_PNL']
print(df_cf[cols].to_string(index=False))
print("-" * 100)
print(f"TOTAL REALIZED PnL:   ${df_cf['realized_pnl'].sum():,.2f}")
print(f"TOTAL UNREALIZED PnL: ${df_cf['unrealized_pnl'].sum():,.2f}")
print(f"OVERALL NET PROFIT:   ${(df_cf['realized_pnl'].sum() + df_cf['unrealized_pnl'].sum()):,.2f}")

conn.close()

