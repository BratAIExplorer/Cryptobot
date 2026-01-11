#!/bin/bash
# Quick diagnostic script for ETH Grid Bot issue
# Run this on VPS at /root/cryptobot_v3

echo "========================================="
echo "ETH GRID BOT DIAGNOSTIC"
echo "========================================="
echo ""

# Change to correct directory
cd /root/cryptobot_v3

echo "1. CHECK: Is ETH bot being evaluated?"
echo "-------------------------------------"
tail -1000 test_proven_config.log | grep "Test Grid Bot ETH" | tail -10
echo ""

echo "2. CHECK: ETH strategy initialization"
echo "-------------------------------------"
tail -1000 test_proven_config.log | grep -E "DynamicGrid.*ETH|Initialized.*ETH" | tail -5
echo ""

echo "3. CHECK: ETH-specific errors"
echo "-------------------------------------"
grep -i "eth" test_proven_config.log | grep -iE "error|exception|fail|traceback" | tail -10
echo ""

echo "4. CHECK: ETH signal generation"
echo "-------------------------------------"
tail -1000 test_proven_config.log | grep -E "ETH.*BUY|GRID.*ETH|Grid Entry.*ETH" | tail -10
echo ""

echo "5. CHECK: Database positions"
echo "-------------------------------------"
sqlite3 data/test_adapter_binance_paper.db "
SELECT
    symbol,
    COUNT(*) as positions,
    ROUND(SUM(CASE WHEN status='OPEN' THEN buy_price * amount ELSE 0 END), 2) as total_exposure
FROM positions
GROUP BY symbol;
"
echo ""

echo "6. CHECK: Active bots configured"
echo "-------------------------------------"
grep "Adding Grid Bot" test_proven_config.log | tail -5
echo ""

echo "7. CHECK: Recent cycle activity (last 100 lines)"
echo "-------------------------------------"
tail -100 test_proven_config.log
echo ""

echo "========================================="
echo "DIAGNOSTIC COMPLETE"
echo "========================================="
echo ""
echo "NEXT STEPS:"
echo "- Review output above"
echo "- Check if ETH bot is being evaluated (section 1)"
echo "- Check if ETH strategy was initialized (section 2)"
echo "- Check for errors (section 3)"
echo "- Share full output with developer"
