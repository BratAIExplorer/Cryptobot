#!/bin/bash
# 🔧 INFRASTRUCTURE SCRIPT 3/4: Daily Backup

echo "========================================================================"
echo "🔧 INFRASTRUCTURE SETUP #3: Daily Backup"
echo "========================================================================"
echo ""
echo "📖 WHAT THIS DOES:"
echo "   • Backs up database daily at 2 AM"
echo "   • Exports trades to CSV format"
echo "   • Keeps last 30 days of backups"
echo "   • Auto-deletes old backups"
echo ""
echo "⏱️  Time needed: 1 minute"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create backup script
BACKUP_SCRIPT="$BOT_DIR/scripts/daily_backup.sh"
mkdir -p "$BOT_DIR/scripts"
mkdir -p "$BOT_DIR/backups"

cat > "$BACKUP_SCRIPT" <<'EOF'
#!/bin/bash
# Daily backup script - runs at 2 AM

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$BOT_DIR/backups"
DB_FILE="$BOT_DIR/data/trades_v3_paper.db"
DATE=$(date +%Y%m%d)

echo "$(date): Starting daily backup..." >> "$BACKUP_DIR/backup.log"

# Create backup directory if doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database (if exists)
if [ -f "$DB_FILE" ]; then
    # SQLite database backup
    cp "$DB_FILE" "$BACKUP_DIR/trades_$DATE.db"
    echo "$(date): Database backed up to trades_$DATE.db" >> "$BACKUP_DIR/backup.log"

    # Export to CSV
    sqlite3 "$DB_FILE" <<SQL
.mode csv
.output $BACKUP_DIR/trades_$DATE.csv
SELECT * FROM trades;
SQL

    echo "$(date): CSV exported to trades_$DATE.csv" >> "$BACKUP_DIR/backup.log"

    # Compress to save space
    gzip -f "$BACKUP_DIR/trades_$DATE.csv"

    echo "$(date): CSV compressed to trades_$DATE.csv.gz" >> "$BACKUP_DIR/backup.log"
else
    echo "$(date): Database not found at $DB_FILE" >> "$BACKUP_DIR/backup.log"
fi

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "trades_*.db" -mtime +30 -delete
find "$BACKUP_DIR" -name "trades_*.csv.gz" -mtime +30 -delete

echo "$(date): Backup complete. Old backups cleaned up." >> "$BACKUP_DIR/backup.log"

# Get total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "$(date): Total backup size: $TOTAL_SIZE" >> "$BACKUP_DIR/backup.log"
EOF

chmod +x "$BACKUP_SCRIPT"

echo "Backup script created: $BACKUP_SCRIPT"
echo ""

# Add to crontab (2 AM daily)
echo "Adding to crontab (runs daily at 2 AM)..."

CRON_CMD="0 2 * * * $BACKUP_SCRIPT"
(crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_CMD") | crontab -

echo ""
echo "========================================================================"
echo "✅ Daily backup installed successfully!"
echo "========================================================================"
echo ""
echo "📊 BACKUP INFO:"
echo "   • Runs daily at 2:00 AM"
echo "   • Backups saved to: $BOT_DIR/backups/"
echo "   • Keeps last 30 days"
echo "   • Format: trades_YYYYMMDD.db + trades_YYYYMMDD.csv.gz"
echo ""
echo "📝 To test backup now:"
echo "   $BACKUP_SCRIPT"
echo ""
echo "📂 To view backups:"
echo "   ls -lh $BOT_DIR/backups/"
echo ""
