import sqlite3
import os

def migrate_v1_comparison():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(root_dir, 'data', 'trades.db')
    
    print(f"Migrating {db_path} for V1/V2 comparison...")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Add v1_score column
        try:
            c.execute("ALTER TABLE confluence_scores ADD COLUMN v1_score INTEGER")
            print("✅ Added v1_score column")
        except sqlite3.OperationalError:
            print("ℹ️ v1_score column already exists")
            
        conn.commit()
        conn.close()
        print("🚀 Comparison migration complete")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_v1_comparison()
