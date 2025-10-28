# Ad Intelligence Platform - Quick Start Guide

Complete workflow from scraping competitor ads to generating insights.

---

## 🚀 Full Workflow

### Step 1: Scrape Competitor Ads (400 ads)

**Option A: Using Chrome Extension (Recommended)**

1. **Close Chrome completely**
2. Run the wrapper script:

```bash
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  "Talabat" \
  400
```

The script will:
- Prompt you to close Chrome (if not already closed)
- Open Chrome with your GATC Scraper extension
- Navigate to the advertiser page
- Automatically trigger extension to scrape 400 ads
- Download CSV to `data/input/Talabat_YYYYMMDD_HHMMSS.csv`
- Takes ~7-10 minutes for 400 ads

**Option B: Manual Extension Trigger**

If automatic triggering fails:
1. Script will prompt: "MANUAL INTERVENTION NEEDED"
2. Click the GATC Scraper extension icon in Chrome
3. Set number of ads to 400
4. Click "Scrape Current Page"
5. Script monitors and moves file automatically

---

### Step 2: Analyze Ads with AI

Once you have the CSV file, run analysis:

```bash
python run_analysis.py \
  --input data/input/Talabat_YYYYMMDD_HHMMSS.csv \
  --analyzer hybrid
```

**What happens:**
- Extracts screenshots from all ad URLs
- Stage 1: llava vision model extracts text (~30 sec per ad)
- Stage 2: deepseek-r1 analyzes text (~15 sec per ad)
- Total: ~45 sec per ad
- Generates insights report with offer distribution, keywords, products

**Output files:**
```
data/output/analysis_YYYYMMDD_HHMMSS/
├── screenshots/           # All extracted ad images
├── analyses.csv           # Individual ad analysis
├── campaign_insights.json # Aggregated statistics
└── campaign_report.txt    # Human-readable summary
```

---

### Step 3: View Insights

```bash
cat data/output/analysis_YYYYMMDD_HHMMSS/campaign_report.txt
```

**Example output:**
```
TALABAT CAMPAIGN INTELLIGENCE REPORT
================================================================================

Campaign Overview:
Talabat is pushing 400 ads with the following distribution:

Offer Distribution:
  • Free Delivery: 40.0% (160 ads)
  • Percentage Discount: 25.0% (100 ads)
  • Buy One Get One: 15.0% (60 ads)
  • Fixed Amount Discount: 12.5% (50 ads)
  • No Offer: 7.5% (30 ads)

Most Highlighted Category: Food Delivery

Top Keywords:
  1. free delivery (160 mentions)
  2. order now (120 mentions)
  3. save (95 mentions)
  4. restaurants (85 mentions)
  5. exclusive (70 mentions)

Top Products Mentioned:
  1. Groceries (85 ads)
  2. Restaurants (80 ads)
  3. Pharmacy (45 ads)
```

---

## 📊 Understanding the Analyzers

### Hybrid Analyzer (Recommended - Fastest)
- **Speed:** ~45 sec per ad
- **Cost:** Free (local models)
- **Models:** llava + deepseek-r1
- **Best for:** Production use

```bash
python run_analysis.py --input data.csv --analyzer hybrid
```

### Ollama Analyzer (Accurate but slower)
- **Speed:** ~90+ sec per ad
- **Cost:** Free (local model)
- **Model:** llava only
- **Best for:** Maximum accuracy

```bash
python run_analysis.py --input data.csv --analyzer ollama
```

### Claude Analyzer (Most accurate)
- **Speed:** ~2-3 sec per ad
- **Cost:** Paid API (Anthropic)
- **Model:** Claude 3.5 Sonnet
- **Best for:** Critical analysis

```bash
python run_analysis.py --input data.csv --analyzer claude
```

---

## 🔄 Automated Daily Scraping

### Setup automated scraping for all competitors:

1. Edit `config/competitors.yaml` to add competitors:

```yaml
competitors:
  - name: "Talabat"
    region: "QA"
    enabled: true
  - name: "Careem"
    region: "QA"
    enabled: true
```

2. Run all competitors:

```bash
python scrapers/auto_scrape.py --run-now
```

3. Schedule daily runs (2 AM):

```bash
python scrapers/auto_scrape.py --schedule
# Follow the cron instructions shown
```

---

## 🛠️ Troubleshooting

### Chrome Profile Errors
**Problem:** "user data directory is already in use"
**Solution:** Close Chrome completely before running scraper

### Extension Not Found
**Problem:** Script can't find GATC Scraper extension
**Solution:** Verify extension is installed in Profile 1:
```bash
cat ~/Library/Application\ Support/Google/Chrome/Profile\ 1/Preferences | grep -i gatc
```

### Analysis Timing Out
**Problem:** llava/deepseek timing out
**Solution:** Reduce batch size or increase timeout in code

### Empty Screenshots
**Problem:** Creative field shows "Check GATC link"
**Solution:** Script automatically falls back to iframe extraction for video ads

---

## 📁 Project Structure

```
ad-intelligence/
├── scrapers/
│   ├── extension_scraper.py      # Chrome extension automation
│   ├── scrape_with_extension.sh  # Wrapper script (use this!)
│   ├── gatc_scraper.py            # Basic Selenium scraper
│   └── auto_scrape.py             # Batch scraping
├── extractors/
│   └── gatc.py                    # Screenshot extraction
├── analyzers/
│   ├── hybrid.py                  # Fast two-stage analysis
│   ├── ollama.py                  # Single-model analysis
│   └── claude.py                  # Claude API analysis
├── config/
│   └── competitors.yaml           # Competitor tracking config
├── data/
│   ├── input/                     # Scraped CSVs
│   └── output/                    # Analysis results
└── run_analysis.py                # Main pipeline
```

---

## 💡 Tips & Best Practices

1. **Start small:** Test with 50 ads first to verify setup
2. **Off-hours:** Run scraping during 2-4 AM to avoid detection
3. **Batch processing:** Use `auto_scrape.py` for multiple competitors
4. **Track trends:** Scrape weekly and compare campaign_insights.json over time
5. **Local models:** Pull llava and deepseek-r1 once, reuse forever (no API costs!)

---

## 📞 Need Help?

- **Extension Setup:** See `scrapers/EXTENSION_SETUP.md`
- **Scraper Details:** See `scrapers/README.md`
- **Analysis Details:** See `analyzers/README.md` (if exists)

---

## 🎯 Complete Example

```bash
# 1. Scrape Talabat (400 ads)
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  "Talabat" \
  400

# 2. Analyze with hybrid analyzer
python run_analysis.py \
  --input data/input/Talabat_20251016.csv \
  --analyzer hybrid

# 3. View insights
cat data/output/analysis_20251016_143000/campaign_report.txt

# 4. Compare with competitor
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR01234567890123456789?region=QA" \
  "Careem" \
  400

python run_analysis.py \
  --input data/input/Careem_20251016.csv \
  --analyzer hybrid
```

Done! 🎉
