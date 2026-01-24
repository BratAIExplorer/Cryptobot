#!/bin/bash
# Extract confluence scores from bot logs for analysis
# Run this on VPS after 48 hours of trading with min_confluence=0

LOG_PATH="$HOME/cryptobot_v3/logs/bot_engine.log"
OUTPUT_FILE="confluence_analysis_$(date +%Y%m%d_%H%M%S).csv"

echo "Extracting confluence data from logs..."
echo "timestamp,symbol,dip_pct,confluence_score,action" > $OUTPUT_FILE

# Extract lines with "Dip Detected" and confluence scores
# Format: "INFO - Dip Detected: SOL/USDT (-3.2%), Confluence: 4/50"
grep -E "Dip Detected.*Confluence" $LOG_PATH | while read line; do
    # Extract timestamp (assuming standard log format)
    timestamp=$(echo "$line" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}')

    # Extract symbol (e.g., SOL/USDT)
    symbol=$(echo "$line" | grep -oE '[A-Z]+/USDT')

    # Extract dip percentage (e.g., -3.2)
    dip_pct=$(echo "$line" | grep -oE '\(-?[0-9]+\.[0-9]+%\)' | tr -d '()%')

    # Extract confluence score (e.g., 4 from "Confluence: 4/50")
    confluence=$(echo "$line" | grep -oE 'Confluence: [0-9]+' | grep -oE '[0-9]+$')

    # Determine if trade was executed (look for "QUALIFIED" or "Skipped")
    if echo "$line" | grep -q "QUALIFIED"; then
        action="TRADE"
    elif echo "$line" | grep -q "Skipped"; then
        action="SKIP"
    else
        action="UNKNOWN"
    fi

    if [ -n "$timestamp" ] && [ -n "$symbol" ] && [ -n "$confluence" ]; then
        echo "$timestamp,$symbol,$dip_pct,$confluence,$action" >> $OUTPUT_FILE
    fi
done

# Count trades
total_lines=$(wc -l < $OUTPUT_FILE)
total_dips=$((total_lines - 1))  # Subtract header
trade_count=$(grep -c "TRADE" $OUTPUT_FILE)
skip_count=$(grep -c "SKIP" $OUTPUT_FILE)

echo ""
echo "========================================"
echo "📊 Confluence Data Extraction Complete"
echo "========================================"
echo "Output file: $OUTPUT_FILE"
echo "Total dips detected: $total_dips"
echo "Trades executed: $trade_count"
echo "Trades skipped: $skip_count"
echo ""
echo "Confluence score distribution:"
awk -F',' 'NR>1 {scores[int($4/10)*10]++} END {for (score in scores) printf "%3d-%3d: %3d dips\n", score, score+9, scores[score]}' $OUTPUT_FILE | sort -n
echo ""
echo "Next step: Download this file and analyze with Python/Excel"
echo "  scp root@72.60.40.29:~/cryptobot_v3/$OUTPUT_FILE ."
