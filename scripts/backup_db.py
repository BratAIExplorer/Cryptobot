#!/usr/bin/env python3
"""
Robust Database Backup Script
- Creates timestamped backups in 'backups/' directory
- Rotates backups (keeps last 7 days)
- Handles errors and logging
"""
import shutil
import os
import sys
import glob
import logging
from datetime import datetime, timedelta

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'backups')
DB_FILE = os.path.join(DATA_DIR, 'trades.db')
RETENTION_DAYS = 7
LOG_FILE = os.path.join(PROJECT_ROOT, 'backup.log')

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_backup():
    """Create a new backup of the database"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logging.info(f"Created backup directory: {BACKUP_DIR}")

    if not os.path.exists(DB_FILE):
        error_msg = f"Database file not found: {DB_FILE}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"trades_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copy2(DB_FILE, backup_path)
        success_msg = f"Backup created successfully: {backup_path}"
        logging.info(success_msg)
        print(f"✅ {success_msg}")
        return True
    except Exception as e:
        error_msg = f"Failed to create backup: {str(e)}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def rotate_backups():
    """Delete backups older than RETENTION_DAYS"""
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    
    # Find all backup files
    backup_files = glob.glob(os.path.join(BACKUP_DIR, "trades_backup_*.db"))
    
    deleted_count = 0
    for file_path in backup_files:
        try:
            # Get file creation time
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            
            if file_time < cutoff_date:
                os.remove(file_path)
                logging.info(f"Deleted old backup: {file_path}")
                deleted_count += 1
        except Exception as e:
            logging.error(f"Error deleting {file_path}: {str(e)}")
            
    if deleted_count > 0:
        print(f"🧹 Cleaned up {deleted_count} old backups (> {RETENTION_DAYS} days)")

def main():
    print("📦 Starting Database Backup...")
    if create_backup():
        rotate_backups()
        print("✨ Backup process completed!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
