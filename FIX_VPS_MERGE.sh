#!/bin/bash
# Fix VPS Merge Conflict and Restart Bot
# Run this on the VPS: bash FIX_VPS_MERGE.sh

echo "=================================================="
echo "🔧 FIXING VPS MERGE CONFLICT"
echo "=================================================="
echo ""

# Step 1: Abort current merge
echo "1️⃣  Aborting failed merge..."
git merge --abort

echo "   ✅ Merge aborted"
echo ""

# Step 2: Stash any local changes
echo "2️⃣  Stashing local changes..."
git stash

echo "   ✅ Changes stashed"
echo ""

# Step 3: Pull latest with force
echo "3️⃣  Pulling latest code (accepting remote changes)..."
git fetch origin claude/review-handover-bot-performance-Rwv92
git reset --hard origin/claude/review-handover-bot-performance-Rwv92

echo "   ✅ Code updated to latest"
echo ""

# Step 4: Verify files
echo "4️⃣  Verifying key files..."
if [ -f "check_position_sell_targets.py" ]; then
    echo "   ✅ check_position_sell_targets.py found"
else
    echo "   ❌ check_position_sell_targets.py missing!"
fi

if [ -f "force_close_positions.py" ]; then
    echo "   ✅ force_close_positions.py found"
else
    echo "   ❌ force_close_positions.py missing!"
fi

if [ -f "EXECUTE_NOW.md" ]; then
    echo "   ✅ EXECUTE_NOW.md found"
else
    echo "   ❌ EXECUTE_NOW.md missing!"
fi

echo ""
echo "=================================================="
echo "✅ FIX COMPLETE - Ready to Execute"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. python3 check_position_sell_targets.py"
echo "  2. python3 force_close_positions.py"
echo "  3. bash restart_bot.sh"
echo ""
