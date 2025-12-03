#!/usr/bin/env python3
import sqlite3
import pandas as pd

db_path = 'data/trades.db'
conn = sqlite3.connect(db_path)

print("=" * 60)
print("CIRCUIT BREAKER STATUS")
print("=" * 60)
try:
    df = pd.read_sql_query("SELECT * FROM circuit_breaker", conn)
    if df.empty:
        print("No circuit breaker records found")
    else:
        print(df.to_string(index=False))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("OPEN POSITIONS")
print("=" * 60)
try:
    df = pd.read_sql_query("SELECT * FROM positions WHERE status='OPEN' ORDER BY buy_timestamp DESC", conn)
    if df.empty:
        print("No open positions found")
    else:
        print(df.to_string(index=False))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("RECENT TRADES (Last 48 Hours)")
print("=" * 60)
try:
    query = """
    SELECT strategy, symbol, side, COUNT(*) as count 
    FROM trades 
    WHERE timestamp > datetime('now', '-48 hours') 
    GROUP BY strategy, symbol, side
    ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print("No trades in last 48 hours")
    else:
        print(df.to_string(index=False))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("BOT STATUS")
print("=" * 60)
try:
    df = pd.read_sql_query("SELECT strategy, status, total_trades, wallet_balance, last_heartbeat FROM bot_status", conn)
    if df.empty:
        print("No bot status found")
    else:
        print(df.to_string(index=False))
except Exception as e:
    print(f"Error: {e}")

conn.close()
