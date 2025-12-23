import sqlite3
import os

def migrate_db(db_path):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} - does not exist.")
        return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of columns to add
    migrations = [
        ("positions", "entry_price_expected", "REAL"),
        ("positions", "exit_price_expected", "REAL"),
        ("trades", "expected_price", "REAL"),
        ("trades", "slippage_pct", "REAL"),
        ("confluence_scores", "raw_score", "INTEGER"),
        ("confluence_scores", "v1_score", "INTEGER"),
        ("confluence_scores", "exchange", "TEXT"),
        ("positions", "exchange", "TEXT"),
        ("trades", "exchange", "TEXT")
    ]

    for table, column, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"✅ Added {column} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"ℹ️ {column} already exists in {table}")
            else:
                print(f"❌ Error adding {column} to {table}: {e}")

    conn.commit()
    conn.close()
    print(f"Done migrating {db_path}.\n")

if __name__ == "__main__":
    # Migrate ALL potential DB files
    root_dir = os.path.dirname(os.path.abspath(__file__))
    dbs = [
        'trades.db',
        'trades_v3.db',
        'trades_v3_live.db',
        'trades_v3_paper.db'
    ]
    for db in dbs:
        migrate_db(os.path.join(root_dir, 'data', db))
