#!/bin/bash
################################################################################
# FIX PORTFOLIO - Show All Bots (Not Just Those with Trades)
# Date: 2026-01-23
# Purpose: Fix get_portfolio_summary() to display all active bots
################################################################################

set -e

echo "========================================================================"
echo "🔧 FIXING PORTFOLIO - Show All Active Bots"
echo "========================================================================"
echo ""

cd ~/cryptobot_v3/enterprise/backend

# Backup current file
echo "📦 Creating backup..."
cp utils/bot_reader.py utils/bot_reader.py.backup_portfolio_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Create Python script to fix get_portfolio_summary
echo "🔧 Modifying get_portfolio_summary()..."

cat > /tmp/fix_portfolio.py << 'ENDPYTHON'
#!/usr/bin/env python3
"""
Fix bot_reader.py to show all active bots in portfolio,
not just those with positions
"""
import re

# Read the file
with open('utils/bot_reader.py', 'r') as f:
    content = f.read()

# Find and replace the strategy breakdown section
old_strategy_query = r'''        # Strategy breakdown from positions
        cursor\.execute\("""
            SELECT
                strategy,
                COUNT\(\) as position_count,
                SUM\(COALESCE\(unrealized_pnl_usd, 0\)\) as strategy_pnl
            FROM positions
            GROUP BY strategy
        """\)
        strategies = \[\]
        for row in cursor\.fetchall\(\):
            strategies\.append\(\{
                "name": row\[0\],
                "trades": row\[1\],
                "pnl": round\(row\[2\], 2\)
            \}\)'''

new_strategy_query = '''        # Strategy breakdown from bot_status (show ALL active bots)
        cursor.execute("""
            SELECT
                bs.strategy,
                bs.wallet_balance,
                COALESCE(COUNT(p.id), 0) as position_count,
                COALESCE(SUM(p.unrealized_pnl_usd), 0.0) as strategy_pnl
            FROM bot_status bs
            LEFT JOIN positions p ON bs.strategy = p.strategy
            WHERE bs.status = 'RUNNING'
            GROUP BY bs.strategy, bs.wallet_balance
            ORDER BY bs.strategy
        """)
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                "name": row[0],
                "balance": round(row[1], 2),
                "trades": row[2],
                "pnl": round(row[3], 2)
            })'''

# Try to replace
if re.search(old_strategy_query, content, re.MULTILINE):
    content = re.sub(old_strategy_query, new_strategy_query, content, flags=re.MULTILINE)
    print("✅ Successfully replaced strategy query")
else:
    print("⚠️  Could not find exact pattern, trying simpler approach...")

    # Try finding just the key parts
    if "# Strategy breakdown from positions" in content:
        # Find the section
        start = content.find("# Strategy breakdown from positions")
        if start != -1:
            # Find the end (where the conn.close() or return happens after this section)
            # Look for the end of the strategies loop
            temp = content[start:]
            end_marker = "conn.close()"
            end_pos = temp.find(end_marker)

            if end_pos != -1:
                # Replace just the query and loop
                before = content[:start]
                after = content[start + end_pos:]

                middle = '''# Strategy breakdown from bot_status (show ALL active bots)
        cursor.execute("""
            SELECT
                bs.strategy,
                bs.wallet_balance,
                COALESCE(COUNT(p.id), 0) as position_count,
                COALESCE(SUM(p.unrealized_pnl_usd), 0.0) as strategy_pnl
            FROM bot_status bs
            LEFT JOIN positions p ON bs.strategy = p.strategy
            WHERE bs.status = 'RUNNING'
            GROUP BY bs.strategy, bs.wallet_balance
            ORDER BY bs.strategy
        """)
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                "name": row[0],
                "balance": round(row[1], 2),
                "trades": row[2],
                "pnl": round(row[3], 2)
            })

        '''

                content = before + middle + after
                print("✅ Used alternate replacement method")
            else:
                print("❌ Could not find section end")
                exit(1)
    else:
        print("❌ Could not find strategy breakdown section")
        exit(1)

# Write the modified content
with open('utils/bot_reader.py', 'w') as f:
    f.write(content)

print("✅ Portfolio fix applied successfully")
ENDPYTHON

python3 /tmp/fix_portfolio.py

echo "✅ Portfolio fix completed"
echo ""

# Restart backend
echo "🔄 Restarting backend..."
pkill -f "uvicorn main:app" 2>/dev/null || echo "Backend not running"
sleep 2
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend restarted (PID: $BACKEND_PID)"
sleep 5
echo ""

# Test the fix
echo "========================================================================"
echo "🧪 TESTING FIXED PORTFOLIO"
echo "========================================================================"
echo ""

# Get auth token
echo "📝 Getting auth token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cryptobot.com","password":"change_me_immediately"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token obtained"
echo ""

# Test portfolio endpoint
echo "📊 Testing Portfolio Endpoint:"
curl -s http://localhost:8000/api/trades/portfolio \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "📊 Testing Bot Status:"
curl -s http://localhost:8000/api/bots/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "========================================================================"
echo "✅ FIX COMPLETE!"
echo "========================================================================"
echo ""
echo "Expected Portfolio Strategies (5 bots):"
echo "   - Grid Bot BTC (balance: \$250)"
echo "   - Grid Bot ETH (balance: \$200)"
echo "   - Buy-Dip-5.2% (balance: \$333)"
echo "   - Buy-Dip-5.5% (balance: \$333)"
echo "   - Buy-Dip-8.0% (balance: \$334)"
echo ""
echo "🔄 HARD REFRESH your browser (Ctrl+Shift+R)"
echo "========================================================================"
echo ""
