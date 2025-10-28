# Automated Competitor Ad Scraper

Automatically retrieve competitor ads from Google Ad Transparency Center (GATC).

## Quick Start

### 1. Scrape Using Chrome Extension (Recommended - 400+ ads)

**Best for: Large-scale scraping (400-1000 ads)**

```bash
# Close Chrome, then run:
./scrapers/scrape_with_extension.sh \
  "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  "Talabat" \
  400
```

This will:
- Use GATC Scraper Chrome extension to download CSV
- Extract 400 ads automatically
- Save to `data/input/Talabat_YYYYMMDD_HHMMSS.csv`

See [EXTENSION_SETUP.md](EXTENSION_SETUP.md) for setup instructions.

### 2. Scrape Using Selenium (Basic - up to 100 ads)

**Best for: Quick tests or small datasets**

```bash
python scrapers/gatc_scraper.py --advertiser "Careem" --region QA
```

This will:
- Search GATC for "Careem"
- Extract up to 100 ads
- Save to `data/input/Careem_YYYYMMDD_HHMMSS.csv`

### 2. Scrape All Configured Competitors

```bash
python scrapers/auto_scrape.py --run-now
```

Scrapes all competitors listed in `config/competitors.yaml`

### 3. Set Up Automated Daily Scraping

```bash
python scrapers/auto_scrape.py --schedule
```

Shows cron command to run scraping automatically every day.

## Configuration

Edit `config/competitors.yaml` to:
- Add/remove competitors
- Enable/disable specific competitors
- Change scraping settings
- Set schedule frequency

```yaml
competitors:
  - name: "Talabat"
    region: "QA"
    enabled: true

  - name: "Careem"
    region: "QA"
    enabled: true
```

## Options

### Single Competitor Scraper (`gatc_scraper.py`)

```bash
--advertiser  Advertiser name (required)
--region      Region code (default: QA)
--max-ads     Max ads to scrape (default: 100)
--output      Custom output file path
```

**Examples:**
```bash
# Scrape Deliveroo in UAE
python scrapers/gatc_scraper.py --advertiser "Deliveroo" --region AE

# Scrape max 50 ads
python scrapers/gatc_scraper.py --advertiser "Zomato" --max-ads 50

# Custom output file
python scrapers/gatc_scraper.py --advertiser "Uber Eats" --output my_data.csv
```

### Automated Scraper (`auto_scrape.py`)

```bash
--run-now     Run immediately
--schedule    Show scheduling instructions
```

## Automated Scheduling

### Mac/Linux (cron)

1. Run setup command:
```bash
python scrapers/auto_scrape.py --schedule
```

2. Copy the cron entry shown

3. Add to crontab:
```bash
crontab -e
```

4. Paste the entry and save

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (Daily, 2:00 AM)
4. Set action: Run Python script
   - Program: `python`
   - Arguments: `/path/to/scrapers/auto_scrape.py --run-now`
   - Start in: `/path/to/ad-intelligence`

## Output

Scraped data is saved to:
```
data/input/scraped/
├── Talabat_20251016.csv
├── Careem_20251016.csv
└── Deliveroo_20251016.csv
```

## Workflow

1. **Scrape competitors** → CSV files in `data/input/scraped/`
2. **Run analysis** → `python run_analysis.py --input data/input/scraped/Careem_20251016.csv`
3. **Get insights** → Campaign intelligence report

## Tips

- Run scraping during off-hours (2-4 AM) to avoid detection
- Scrape weekly for trend analysis
- Compare results over time to track competitor strategy changes
- Use `--max-ads 50` for quick tests

## Troubleshooting

**"Advertiser not found"**
- Check spelling
- Try different search terms
- Advertiser may not be in GATC

**Timeout errors**
- GATC may be slow
- Try running during off-peak hours
- Increase wait times in config

**Empty results**
- Advertiser may have no active ads in that region
- Check region code is correct
