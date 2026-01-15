#!/bin/bash
# Cleanup Old Bot Installations - Run on VPS
# Permanently removes old/duplicate bot directories
# Date: 2026-01-15

set -e

echo "================================"
echo "🗑️  OLD BOT CLEANUP"
echo "================================"
echo ""
echo "⚠️  WARNING: This will DELETE old bot directories!"
echo "   Current ACTIVE bot: /root/cryptobot_v3"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "1️⃣  Killing all bot processes..."
pkill -f "run_bot.py" || echo "   No bot processes running"
sleep 2

echo ""
echo "2️⃣  Finding old bot directories..."
echo ""

# List of old bot paths to delete
OLD_PATHS=(
    "/Antigravity/antigravity/scratch/crypto_trading_bot"
    "/root/cryptobot_v2"
    "/root/cryptobot_old"
    "/root/crypto_trading_bot"
    "/home/antigravity/crypto_trading_bot"
)

FOUND_COUNT=0

for path in "${OLD_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "   ✅ Found: $path"
        SIZE=$(du -sh "$path" 2>/dev/null | cut -f1 || echo "unknown")
        echo "      Size: $SIZE"
        FOUND_COUNT=$((FOUND_COUNT + 1))
    fi
done

# Search for any other directories named "crypto*bot" or "cryptobot"
echo ""
echo "3️⃣  Searching entire filesystem for other bot directories..."
echo "   (This may take 30-60 seconds...)"
echo ""

find / -type d \( -name "*crypto*bot*" -o -name "*trading*bot*" \) 2>/dev/null | while read dir; do
    # Skip the active directory
    if [ "$dir" != "/root/cryptobot_v3" ] && [ "$dir" != "/home/user/Cryptobot" ]; then
        echo "   ⚠️  Found: $dir"
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
        echo "      Size: $SIZE"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  DELETION CONFIRMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  ABOUT TO DELETE ALL DIRECTORIES LISTED ABOVE"
echo "   ACTIVE bot will NOT be touched: /root/cryptobot_v3"
echo ""
read -p "Proceed with DELETION? (type 'DELETE' to confirm): " final_confirm

if [ "$final_confirm" != "DELETE" ]; then
    echo "Aborted. No files deleted."
    exit 0
fi

echo ""
echo "5️⃣  Deleting old bot directories..."
echo ""

for path in "${OLD_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "   🗑️  Deleting: $path"
        rm -rf "$path"
        echo "      ✅ Deleted"
    fi
done

# Delete other found directories (manual confirmation per directory)
find / -type d \( -name "*crypto*bot*" -o -name "*trading*bot*" \) 2>/dev/null | while read dir; do
    if [ "$dir" != "/root/cryptobot_v3" ] && [ "$dir" != "/home/user/Cryptobot" ]; then
        echo ""
        echo "   Found: $dir"
        read -p "   Delete this? (yes/no): " delete_confirm
        if [ "$delete_confirm" = "yes" ]; then
            rm -rf "$dir"
            echo "      ✅ Deleted"
        else
            echo "      ⏭️  Skipped"
        fi
    fi
done

echo ""
echo "================================"
echo "✅ CLEANUP COMPLETE"
echo "================================"
echo ""
echo "Remaining bot directory:"
echo "   /root/cryptobot_v3 (ACTIVE)"
echo ""
echo "To restart bot:"
echo "   cd /root/cryptobot_v3"
echo "   nohup python3 run_bot.py > bot.log 2>&1 &"
echo ""
