#!/bin/bash
# Automated GATC Extension Scraper Wrapper
# Handles Chrome profile conflicts automatically

# Configuration
CHROME_PROFILE="/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1"
DOWNLOAD_DIR="/Users/muhannadsaad/Desktop/ad-intelligence/data/input"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================================="
echo "GATC Extension Scraper - Automated Workflow"
echo "=================================================================="
echo ""

# Check if URL provided
if [ -z "$1" ]; then
    echo "Usage: ./scrape_with_extension.sh <advertiser_url> [competitor_name] [max_ads]"
    echo ""
    echo "Example:"
    echo "  ./scrape_with_extension.sh https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA Talabat 400"
    exit 1
fi

ADVERTISER_URL="$1"
COMPETITOR_NAME="${2:-competitor}"
MAX_ADS="${3:-400}"

echo -e "${YELLOW}⚠️  Chrome Profile Conflict Detection${NC}"
echo ""
echo "This script needs to use your Chrome profile with the GATC Scraper extension."
echo "Chrome cannot be open at the same time."
echo ""
echo -e "${YELLOW}Please close ALL Chrome windows now and press Enter to continue...${NC}"
read -p "" dummy

# Double-check Chrome is closed
if pgrep -x "Google Chrome" > /dev/null; then
    echo ""
    echo -e "${YELLOW}⚠️  Chrome is still running. Attempting to close...${NC}"
    killall "Google Chrome" 2>/dev/null
    sleep 2

    # Check again
    if pgrep -x "Google Chrome" > /dev/null; then
        echo ""
        echo "❌ Could not close Chrome automatically."
        echo "Please close Chrome manually and run this script again."
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✓ Chrome closed successfully${NC}"
echo ""
echo "Starting scraper..."
echo ""

# Run the scraper
python scrapers/extension_scraper.py \
  --url "$ADVERTISER_URL" \
  --name "$COMPETITOR_NAME" \
  --max-ads "$MAX_ADS" \
  --chrome-profile "$CHROME_PROFILE" \
  --download-dir "$DOWNLOAD_DIR"

echo ""
echo "=================================================================="
echo "Done!"
echo "=================================================================="
