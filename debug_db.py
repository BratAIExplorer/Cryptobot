
import sqlite3
import pandas as pd

conn = sqlite3.connect('c:/CryptoBot_Project/data/trades_v3.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Check Bot Status
try:
    df = pd.read_sql_query("SELECT * FROM bot_status", conn)
    print("\nBot Status:")
    print(df)
except:
    print("\nNo bot_status table.")

# Check Trades
try:
    df = pd.read_sql_query("SELECT * FROM trades LIMIT 5", conn)
    print("\nRecent Trades:")
    print(df)
except:
    print("\nNo trades table.")

conn.close()
