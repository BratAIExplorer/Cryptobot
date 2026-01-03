import sqlite3

conn = sqlite3.connect('./data/trades_v3.db')
cursor = conn.cursor()

print("=" * 80)
print("📊 DATABASE STRUCTURE")
print("=" * 80)

# Get all tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

print("\n📋 Tables found:")
for table in tables:
    print(f"   - {table[0]}")

print("\n" + "=" * 80)
print("📊 TRADES TABLE STRUCTURE")
print("=" * 80)

# Get trades table structure
try:
    cursor.execute("PRAGMA table_info(trades)")
    columns = cursor.fetchall()
    
    print("\nColumns in 'trades' table:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # Show sample data
    print("\n" + "=" * 80)
    print("📊 SAMPLE DATA (First 3 rows)")
    print("=" * 80)
    
    cursor.execute("SELECT * FROM trades LIMIT 3")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"\n{row}")
        
except Exception as e:
    print(f"Error: {e}")

conn.close()
