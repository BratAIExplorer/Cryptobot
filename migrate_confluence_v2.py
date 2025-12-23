import sqlite3
import os

def migrate_database():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    # V3 Databases to migrate
    db_files = ['trades_v3.db', 'trades_v3_live.db', 'trades_v3_paper.db']
    
    for db_name in db_files:
        db_path = os.path.join(root_dir, 'data', db_name)
        if not os.path.exists(db_path):
            continue
            
        print(f"\nMigrating database: {db_name}")
        
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # 1. Ensure Confluence Scores Table Exists
            c.execute('''
                CREATE TABLE IF NOT EXISTS confluence_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    technical_score REAL,
                    onchain_score REAL,
                    macro_score REAL,
                    fundamental_score REAL,
                    total_score REAL,
                    recommendation TEXT,
                    position_size TEXT,
                    stop_loss_pct REAL,
                    details TEXT
                )
            ''')
            
            # 2. Check existing columns in confluence_scores
            c.execute("PRAGMA table_info(confluence_scores)")
            columns = [column[1] for column in c.fetchall()]
            
            # 3. Add missing columns
            new_columns = [
                ('raw_score', 'REAL'), # Changed to REAL for accuracy
                ('regime_state', 'TEXT'),
                ('regime_multiplier', 'REAL'),
                ('v1_score', 'REAL')
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    print(f"   -> Adding column {col_name}...")
                    c.execute(f"ALTER TABLE confluence_scores ADD COLUMN {col_name} {col_type}")
            
            # 4. Create market_regimes table if it doesn't exist
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
            print(f"✅ Migration successful for {db_name}")
            
        except Exception as e:
            print(f"❌ Migration failed for {db_name}: {e}")

if __name__ == "__main__":
    migrate_database()
