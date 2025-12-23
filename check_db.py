import sqlite3
import os

data_dir = r'c:\CryptoBot_Project\data'
db_files = [f for f in os.listdir(data_dir) if f.endswith('.db')]

for db_file in db_files:
    db_path = os.path.join(data_dir, db_file)
    print(f"\n==========================================")
    print(f"DATABASE: {db_file}")
    print(f"==========================================")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {', '.join(tables)}")
        
        for table in tables:
            try:
                cursor.execute(f"SELECT count(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f" - {table}: {count} rows")
                
                if count > 0 and table in ['trades', 'bot_status']:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                    print(f"   Sample data: {cursor.fetchall()}")
            except Exception as e_table:
                print(f" - {table}: Error {e_table}")
        
        conn.close()
    except Exception as e_db:
        print(f"Error opening {db_file}: {e_db}")
