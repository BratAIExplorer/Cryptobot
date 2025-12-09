import sqlite3
import pandas as pd
import os

# Use absolute path to match logger
root_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(root_dir, 'data', 'trades.db')

print(f"Checking DB: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM system_health", conn)
    conn.close()

    if not df.empty:
        print("\n✅ System Health Data Found:")
        print(df.to_string())
    else:
        print("\n❌ System Health table is empty!")
except Exception as e:
    print(f"\n❌ Error: {e}")
