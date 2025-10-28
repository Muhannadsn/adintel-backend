#!/bin/bash
# Fresh scrape of all competitors (last 30 days)
# Database has been reset - starting clean!

echo "======================================================================"
echo "FRESH SCRAPE - ALL COMPETITORS"
echo "======================================================================"
echo ""
echo "Target: Last 30 days of ads"
echo "Enrichment: DISABLED (scrape first, decide later)"
echo "Save to DB: YES"
echo ""

# Competitor advertiser IDs
TALABAT="AR14306592000630063105"
KEETA="AR02245493152427278337"
DELIVEROO="AR13676304484790173697"
RAFIQ="AR08778154730519003137"
SNOONU="AR12079153035289296897"

# Scrape each competitor (WITHOUT enrichment for now - fast!)
echo "🍕 Scraping Talabat..."
python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/${TALABAT}?region=QA" --max-ads 200 --save-db

echo ""
echo "🚴 Scraping Keeta..."
python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/${KEETA}?region=QA" --max-ads 200 --save-db

echo ""
echo "🏍️ Scraping Deliveroo... DISABLED (no transparency center data)"
# python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/${DELIVEROO}?region=QA" --max-ads 200 --save-db

echo ""
echo "🚗 Scraping Rafiq..."
python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/${RAFIQ}?region=QA" --max-ads 200 --save-db

echo ""
echo "🛵 Scraping Snoonu..."
python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/${SNOONU}?region=QA" --max-ads 200 --save-db

echo ""
echo "======================================================================"
echo "✅ SCRAPING COMPLETE!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Review scraped data in dashboard"
echo "2. If data looks good, run enrichment:"
echo "   python3 re_enrich.py"
echo ""
