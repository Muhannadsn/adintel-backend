#!/bin/bash
# Live brand extraction monitor

echo "🔴 LIVE BRAND EXTRACTION MONITOR"
echo "=================================="
echo ""

tail -f /tmp/brand_fix_enrichment.log | grep --line-buffered -E "\[.*Processing CR|Brand:|Product Type:" | while read line; do
    if [[ $line == *"Processing CR"* ]]; then
        echo ""
        echo "📸 $line"
    elif [[ $line == *"Brand:"* ]]; then
        echo "   🏷️  $line"
    elif [[ $line == *"Product Type:"* ]]; then
        echo "   📦 $line"
    fi
done
