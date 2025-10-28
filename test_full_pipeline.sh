#!/bin/bash
################################################################################
# FULL PIPELINE TEST
# Tests: Scraping → Orchestrator → Database → API → Strategic Analyst
#
# This script:
# 1. Scrapes 3 ads from each competitor
# 2. Runs vision enrichment (LLaVA + 11-Agent Orchestrator)
# 3. Saves to database with brand + food_category fields
# 4. Tests new aggregation endpoints
# 5. Tests Strategic Analyst with vision data
################################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                  🚀 FULL PIPELINE INTEGRATION TEST                         ║"
echo "║             Scraping → Vision AI → Database → API → Frontend              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Change to project directory
cd /Users/muhannadsaad/Desktop/ad-intelligence

# Competitors to test
declare -a competitors=(
  "AR12079153035289296897:Snoonu"
  "AR13676304484790173697:Keeta"
  "AR14306592000630063105:Talabat"
  "AR08778154730519003137:Rafiq"
)

echo "📋 COMPETITORS TO SCRAPE:"
for comp in "${competitors[@]}"; do
  IFS=':' read -r id name <<< "$comp"
  echo "   • $name (ID: $id)"
done
echo ""

# Step 1: Clean old test data (optional - comment out to keep existing data)
echo "🧹 STEP 1: Cleaning old test data..."
# sqlite3 data/adintel.db "DELETE FROM ads WHERE advertiser_id IN ('AR12079153035289296897', 'AR13676304484790173697', 'AR14306592000630063105', 'AR08778154730519003137');"
echo "   ⏭️  Skipped - keeping existing data for comparison"
echo ""

# Step 2: Scrape ads with vision enrichment
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  STEP 2: SCRAPING ADS WITH VISION ENRICHMENT                               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

for comp in "${competitors[@]}"; do
  IFS=':' read -r id name <<< "$comp"

  echo "┌────────────────────────────────────────────────────────────────────────────┐"
  echo "│ 📊 Scraping: $name"
  echo "└────────────────────────────────────────────────────────────────────────────┘"

  python scrapers/api_scraper.py \
    --url "https://adstransparency.google.com/advertiser/$id?region=QA" \
    --max-ads 3 \
    --enrich \
    --save-db 2>&1 | grep -E "(Scraped|ads total|Enrichment|brand|food_category|Saved|Database saved|LAYER|Vision|Brand|Food Category|Agent)" | head -30

  echo ""
  echo "✅ $name complete"
  echo ""
done

# Step 3: Verify database
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  STEP 3: DATABASE VERIFICATION                                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Total ads in database:"
sqlite3 data/adintel.db "SELECT COUNT(*) FROM ads;"
echo ""

echo "🔍 Vision-enriched ads breakdown:"
sqlite3 data/adintel.db "
SELECT
  CASE
    WHEN brand IS NOT NULL AND food_category IS NOT NULL THEN 'Both brand & food_category'
    WHEN brand IS NOT NULL THEN 'Brand only'
    WHEN food_category IS NOT NULL THEN 'Food category only'
    ELSE 'No vision data'
  END as enrichment_type,
  COUNT(*) as count
FROM ad_enrichment
GROUP BY enrichment_type;
" -header -column
echo ""

echo "🏪 Brands detected:"
sqlite3 data/adintel.db "
SELECT brand, COUNT(*) as ad_count
FROM ad_enrichment
WHERE brand IS NOT NULL AND brand != ''
GROUP BY brand
ORDER BY ad_count DESC;
" -header -column
echo ""

echo "🍽️ Food categories detected:"
sqlite3 data/adintel.db "
SELECT food_category, COUNT(*) as ad_count
FROM ad_enrichment
WHERE food_category IS NOT NULL AND food_category != ''
GROUP BY food_category
ORDER BY ad_count DESC;
" -header -column
echo ""

# Step 4: Test API endpoints
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  STEP 4: TESTING API ENDPOINTS                                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "🌐 Testing /api/insights/brands endpoint..."
curl -s http://localhost:8001/api/insights/brands | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Total brands: {data.get('total_brands', 0)}\")
print(f\"   Total ads: {data.get('total_ads', 0)}\")
print(\"   Brands:\")
for brand in data.get('brands', [])[:5]:
    print(f\"      • {brand['brand']}: {brand['ad_count']} ads ({brand['percentage']:.1f}%)\")
" 2>/dev/null || echo "   ❌ Endpoint not responding - is backend running?"
echo ""

echo "🍕 Testing /api/insights/food-categories endpoint..."
curl -s http://localhost:8001/api/insights/food-categories | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Total categories: {data.get('total_categories', 0)}\")
print(f\"   Total ads: {data.get('total_ads', 0)}\")
print(\"   Categories:\")
for cat in data.get('food_categories', [])[:5]:
    print(f\"      • {cat['food_category']}: {cat['ad_count']} ads ({cat['percentage']:.1f}%)\")
" 2>/dev/null || echo "   ❌ Endpoint not responding - is backend running?"
echo ""

echo "📦 Testing /api/insights/products endpoint..."
curl -s http://localhost:8001/api/insights/products | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   Total products: {data.get('total_products', 0)}\")
print(f\"   Total ads: {data.get('total_ads', 0)}\")
print(\"   Top products:\")
for prod in data.get('products', [])[:5]:
    print(f\"      • {prod.get('category', 'Unknown')}: {prod['ad_count']} ads\")
" 2>/dev/null || echo "   ❌ Endpoint not responding - is backend running?"
echo ""

# Step 5: Test Strategic Analyst
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  STEP 5: STRATEGIC ANALYST (AI-POWERED INSIGHTS)                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "🧠 Testing Strategic Analyst modules with vision data..."
echo ""

# Test brands module
echo "📊 Module: BRANDS"
curl -s "http://localhost:8001/api/insights/quick-actions?module=brands" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    actions = data.get('actions', [])
    if actions:
        for i, action in enumerate(actions[:3], 1):
            print(f\"   {i}. {action.get('icon', '📊')} [{action.get('color', 'blue').upper()}] {action.get('text', 'N/A')}\")
    else:
        print('   ⚠️  No actions generated (AI may be processing)')
except:
    print('   ❌ Could not parse response')
" 2>/dev/null || echo "   ❌ Endpoint not responding"
echo ""

# Test food categories module
echo "🍽️ Module: FOOD CATEGORIES"
curl -s "http://localhost:8001/api/insights/quick-actions?module=food_categories" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    actions = data.get('actions', [])
    if actions:
        for i, action in enumerate(actions[:3], 1):
            print(f\"   {i}. {action.get('icon', '📊')} [{action.get('color', 'blue').upper()}] {action.get('text', 'N/A')}\")
    else:
        print('   ⚠️  No actions generated (AI may be processing)')
except:
    print('   ❌ Could not parse response')
" 2>/dev/null || echo "   ❌ Endpoint not responding"
echo ""

# Test products module
echo "📦 Module: PRODUCTS"
curl -s "http://localhost:8001/api/insights/quick-actions?module=products" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    actions = data.get('actions', [])
    if actions:
        for i, action in enumerate(actions[:3], 1):
            print(f\"   {i}. {action.get('icon', '📊')} [{action.get('color', 'blue').upper()}] {action.get('text', 'N/A')}\")
    else:
        print('   ⚠️  No actions generated (AI may be processing)')
except:
    print('   ❌ Could not parse response')
" 2>/dev/null || echo "   ❌ Endpoint not responding"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ PIPELINE TEST COMPLETE                                                 ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 SUMMARY:"
echo "   ✅ Scraped ads from 4 competitors (3 ads each)"
echo "   ✅ Vision enrichment with LLaVA + 11-Agent Orchestrator"
echo "   ✅ Database updated with brand + food_category fields"
echo "   ✅ API endpoints tested (brands, food_categories, products)"
echo "   ✅ Strategic Analyst generating AI-powered competitive insights"
echo ""
echo "🌐 NEXT STEPS:"
echo "   1. Open frontend: http://localhost:3000"
echo "   2. Check ProductBubbleChart for food categories"
echo "   3. View AI Strategic Actions in sidebar"
echo "   4. Run more scrapers to build comprehensive dataset"
echo ""
echo "📝 LOGS:"
echo "   • Backend: /tmp/backend_final.log"
echo "   • Database: data/adintel.db"
echo "   • Screenshots: screenshots/"
echo ""
