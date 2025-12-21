import sqlite3
import os

def migrate_database():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(root_dir, 'data', 'trades_v3.db')
    
    print(f"Migrating database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check existing columns in confluence_scores
        c.execute("PRAGMA table_info(confluence_scores)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add missing columns
        new_columns = [
            ('raw_score', 'INTEGER'),
            ('regime_state', 'TEXT'),
            ('regime_multiplier', 'REAL')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding column {col_name} to confluence_scores...")
                c.execute(f"ALTER TABLE confluence_scores ADD COLUMN {col_name} {col_type}")
        
        # Create market_regimes table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS market_regimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                regime_state TEXT,
                confidence REAL,
                btc_price REAL,
                btc_ma50 REAL,
                btc_ma200 REAL,
                volatility_percentile REAL,
                higher_highs BOOLEAN,
                lower_lows BOOLEAN,
                volume_trend TEXT,
                recent_drawdown_pct REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database migration successful")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_database()
