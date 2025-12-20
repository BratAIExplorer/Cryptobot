import shutil
import os
import datetime
import time

def backup_database():
    """
    Creates a timestamped backup of the live database.
    """
    # Configuration
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, 'data')
    BACKUP_DIR = os.path.join(ROOT_DIR, 'backups')
    
    DB_FILE = 'trades_v3_live.db'
    SOURCE_PATH = os.path.join(DATA_DIR, DB_FILE)
    
    # Ensure backup dir exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    if not os.path.exists(SOURCE_PATH):
        print(f"[Backup] Source file not found: {SOURCE_PATH}")
        return
        
    # Generate backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{DB_FILE}_{timestamp}.bak"
    DEST_PATH = os.path.join(BACKUP_DIR, backup_filename)
    
    # Copy
    try:
        shutil.copy2(SOURCE_PATH, DEST_PATH)
        print(f"[Backup] ✅ Successfully backed up to {backup_filename}")
        
        # Cleanup old backups (Keep last 7 days * 24h = 168 backups)
        # Simple logic: Keep last 100 files
        files = sorted(os.listdir(BACKUP_DIR))
        if len(files) > 100:
            for f in files[:-100]:
                os.remove(os.path.join(BACKUP_DIR, f))
                print(f"[Backup] Cleaned up old backup: {f}")
                
    except Exception as e:
        print(f"[Backup] ❌ Error: {e}")

if __name__ == "__main__":
    print("starting auto-backup service...")
    while True:
        backup_database()
        # Sleep 1 hour
        time.sleep(3600)
