# GATC Extension Scraper Setup Guide

Automate competitor ad scraping using the GATC Scraper Chrome extension.

## Setup Steps

### 1. Create Dedicated Chrome Profile

```bash
# Open Chrome and create a new profile
# Chrome Menu → Settings → "Add person" or "Add profile"
# Name it: "GATC Scraper"
```

### 2. Install GATC Scraper Extension

In the new profile:
1. Go to Chrome Web Store
2. Search for "GATC Scraper"
3. Click "Add to Chrome"
4. Verify extension icon appears in toolbar

### 3. Set Download Location

```bash
# In Chrome settings (chrome://settings/downloads):
# Set "Location" to a known folder, e.g.:
/Users/muhannadsaad/Downloads/gatc_scrapes
```

Create the directory:
```bash
mkdir -p ~/Downloads/gatc_scrapes
```

### 4. Find Chrome Profile Path

**Mac:**
```bash
# Your Chrome profiles are at:
~/Library/Application Support/Google/Chrome/
```

List profiles:
```bash
ls -la ~/Library/Application\ Support/Google/Chrome/ | grep Profile
```

You'll see folders like:
- `Profile 1`
- `Profile 2`
- etc.

**Find your "GATC Scraper" profile:**
```bash
# Open each profile's Preferences file
cat ~/Library/Application\ Support/Google/Chrome/Profile\ 1/Preferences | grep name
```

Look for the profile with name "GATC Scraper"

### 5. Test the Scraper

**IMPORTANT:** Close Chrome before running the scraper to avoid profile conflicts.

#### Easy Method (Recommended):
Use the wrapper script that handles Chrome closing automatically:

```bash
# Make script executable (one time)
chmod +x scrapers/scrape_with_extension.sh

# Run scraper
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  "Talabat" \
  400
```

The script will:
1. Prompt you to close Chrome
2. Verify Chrome is closed
3. Run the scraper automatically
4. Handle all the extension interaction

#### Manual Method:
Close Chrome manually, then run:

```bash
python scrapers/extension_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  --name "Talabat" \
  --max-ads 400 \
  --chrome-profile "/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1" \
  --download-dir "/Users/muhannadsaad/Desktop/ad-intelligence/data/input"
```

## How It Works

1. **Opens Chrome** with your extension-enabled profile
2. **Navigates** directly to advertiser page URL
3. **Finds** GATC Scraper extension automatically
4. **Opens** extension popup programmatically
5. **Auto-fills** number of ads (400)
6. **Clicks** "Scrape Current Page" button
7. **Monitors** download folder for CSV file
8. **Moves** file to `data/input/` with proper naming

The scraper has three fallback methods:
- **Method 1:** Open extension popup directly via URL
- **Method 2:** Inject JavaScript to trigger extension
- **Method 3:** Wait for manual triggering if automation fails

## Usage Examples

### Using the wrapper script (easiest):

```bash
# Scrape Talabat (400 ads)
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  "Talabat" \
  400

# Scrape Careem (400 ads)
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR01234567890123456789?region=QA" \
  "Careem" \
  400
```

### Using Python directly:

```bash
# Scrape Talabat
python scrapers/extension_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  --name "Talabat" \
  --max-ads 400 \
  --chrome-profile "/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1" \
  --download-dir "/Users/muhannadsaad/Desktop/ad-intelligence/data/input"

# Scrape 1000 ads
python scrapers/extension_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR01234567890123456789?region=QA" \
  --name "Deliveroo" \
  --max-ads 1000 \
  --chrome-profile "/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1" \
  --download-dir "/Users/muhannadsaad/Desktop/ad-intelligence/data/input"
```

## Create Shortcut Script

Save this as `scrape_competitor.sh`:

```bash
#!/bin/bash
# Quick scraper script

CHROME_PROFILE="/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1"
DOWNLOAD_DIR="/Users/muhannadsaad/Downloads/gatc_scrapes"

python scrapers/extension_scraper.py \
  --competitor "$1" \
  --region "${2:-JO}" \
  --max-ads "${3:-400}" \
  --chrome-profile "$CHROME_PROFILE" \
  --download-dir "$DOWNLOAD_DIR"
```

Make executable:
```bash
chmod +x scrape_competitor.sh
```

Use it:
```bash
./scrape_competitor.sh "Talabat" JO 400
./scrape_competitor.sh "Careem" QA 500
```

## Troubleshooting

### Extension icon not visible
- Pin the extension: Right-click toolbar → Pin GATC Scraper

### Browser closes immediately
- Remove `--headless` from script (it's already removed)

### Wrong profile loaded
- Double-check profile path
- Try `Profile 2`, `Profile 3`, etc.

### Download not detected
- Verify download directory is correct
- Check Chrome settings for download location
- Look in Chrome downloads (chrome://downloads/)

### "Could not find competitor"
- Check spelling
- Try alternate names
- Manually navigate to their GATC page first

## Next Steps

After scraping:
```bash
# Run analysis on scraped data
python run_analysis.py \
  --input data/input/scraped/Talabat_20251016.csv \
  --analyzer hybrid
```

## Automated Daily Scraping

Add to crontab (scrape at 2 AM daily):
```bash
0 2 * * * cd /path/to/ad-intelligence && ./scrape_competitor.sh "Talabat" JO 400
```
