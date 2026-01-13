#!/bin/bash
# Quick Start Test Launcher
# Ensures all directories exist and starts test cleanly

echo "=========================================="
echo "🚀 QUICK START TEST LAUNCHER"
echo "=========================================="
echo ""

cd /root/cryptobot_v3

# Step 1: Create necessary directories
echo "1️⃣  Creating directories..."
mkdir -p logs
mkdir -p data
echo "✅ Directories created"
echo ""

# Step 2: Clean up old test artifacts
echo "2️⃣  Cleaning up old test files..."
rm -f data/quick_start_test.db
rm -f STOP_SIGNAL
echo "✅ Cleanup complete"
echo ""

# Step 3: Check test script exists
echo "3️⃣  Checking test script..."
if [ -f "test_quick_start.py" ]; then
    echo "✅ test_quick_start.py found"
else
    echo "❌ test_quick_start.py NOT found!"
    echo "   Run: git pull origin claude/priority1-enhancements-lXrIG"
    exit 1
fi
echo ""

# Step 4: Test Python imports (quick validation)
echo "4️⃣  Testing Python imports..."
python3 -c "import sys; sys.path.insert(0, '.'); from core.engine import TradingEngine; from strategies.grid_strategy_v2 import DynamicGridStrategy; from strategies.take_profit_strategy import TakeProfitStrategy; print('✅ All imports successful')" 2>&1

if [ $? -ne 0 ]; then
    echo "⚠️  Import test failed - checking details..."
    echo ""
fi

# Step 5: Start the test
echo ""
echo "5️⃣  Starting Quick Start test..."
nohup python3 -u test_quick_start.py > logs/quick_start_test.log 2>&1 &
TEST_PID=$!

echo "✅ Test started!"
echo "   PID: $TEST_PID"
echo ""

# Step 6: Wait a moment and verify it's running
sleep 3

if ps -p $TEST_PID > /dev/null; then
    echo "✅ Test process is running (PID: $TEST_PID)"
else
    echo "❌ Test process died! Checking logs..."
    if [ -f "logs/quick_start_test.log" ]; then
        echo ""
        echo "📋 Error log:"
        cat logs/quick_start_test.log
    fi
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ TEST RUNNING SUCCESSFULLY"
echo "=========================================="
echo ""
echo "📊 Monitor with:"
echo "   tail -f logs/quick_start_test.log"
echo ""
echo "🛑 Stop with:"
echo "   kill $TEST_PID"
echo ""
echo "📈 Check positions:"
echo "   sqlite3 data/quick_start_test.db 'SELECT * FROM positions;'"
echo ""
echo "=========================================="
echo ""

# Show first 30 lines of log
echo "📋 Initial startup log:"
echo ""
sleep 2
head -30 logs/quick_start_test.log

echo ""
echo "✅ Test is running! Use 'tail -f logs/quick_start_test.log' to watch"
