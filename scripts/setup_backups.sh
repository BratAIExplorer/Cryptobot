#!/bin/bash
# Setup script for automated backups

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_SCRIPT="$PROJECT_ROOT/scripts/backup_db.py"

echo "🛠️  Setting up automated backups..."
echo "📍 Project Root: $PROJECT_ROOT"
echo "📜 Backup Script: $BACKUP_SCRIPT"

# Make script executable
chmod +x "$BACKUP_SCRIPT"

# Prepare cron job entry (Runs daily at 2:00 AM)
CRON_JOB="0 2 * * * /usr/bin/python3 $BACKUP_SCRIPT >> $PROJECT_ROOT/backup.log 2>&1"

# Check if job already exists
(crontab -l 2>/dev/null | grep -F "$BACKUP_SCRIPT") && echo "✅ Cron job already exists!" && exit 0

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo "⏰ Backups will run daily at 2:00 AM"
echo "📂 Backups location: $PROJECT_ROOT/backups/"
