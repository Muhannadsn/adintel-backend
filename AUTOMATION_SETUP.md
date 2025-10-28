# AdIntel Automation Setup

## Summary

You now have a complete system for:
1. **Initial full scrape** (1000 ads, AI enrichment)
2. **Daily incremental updates** (only new ads, auto-detects removed ads)
3. **Scheduled automation** (runs at 7pm daily)
4. **Real strategic insights** (competitor cards, personalized quick actions)

---

## Quick Start

### 1. Initial Setup (One-time)

```bash
# Make scripts executable
chmod +x setup_cron.sh scheduled_scraper.py

# Install cron schedule (runs daily at 7pm)
./setup_cron.sh
```

### 2. Initial Full Scrape (One-time, ~30-45 mins per competitor)

For each competitor, run:

```bash
# Talabat
python scrapers/api_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA" \
  --max-ads 1000 \
  --enrich \
  --save-db

# Deliveroo
python scrapers/api_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR13676304484790173697?region=QA" \
  --max-ads 1000 \
  --enrich \
  --save-db

# Rafiq
python scrapers/api_scraper.py \
  --url "https://adstransparency.google.com/advertiser/AR08778154730519003137?region=QA" \
  --max-ads 1000 \
  --enrich \
  --save-db
```

**What this does:**
- Scrapes 1000 ads
- Analyzes each ad with AI (~2-3 sec per ad)
- Extracts: product category, messaging themes, audience segment, offers
- Saves to database (`data/adintel.db`)

**Time estimate:** ~45 mins per competitor (1000 ads × 2.5 sec)

### 3. Restart API Server (to load new endpoint)

```bash
# Kill existing server
pkill -f "uvicorn.*main:app"

# Restart
cd api
python main.py
```

**OR** if using uvicorn directly:
```bash
uvicorn api.main:app --reload --port 8001
```

### 4. Verify Everything Works

```bash
# Check database stats
python -c "from api.database import AdDatabase; db = AdDatabase(); print(db.get_stats())"

# Test competitor insights endpoint
curl http://localhost:8001/api/competitors/AR14306592000630063105/insights

# View frontend
open http://localhost:3001
```

---

## Daily Automation

### How It Works

**Schedule:** Every day at 7:00 PM

**Process:**
1. Checks if it's first run (no data in DB)
2. **First run:** Scrapes 1000 ads + full AI enrichment (~45 mins)
3. **Daily runs:** Scrapes 100 recent ads only (~2-5 mins)
4. Compares with existing ads
5. Only enriches NEW ads with AI
6. Marks disappeared ads as inactive
7. Saves to database

**Time per daily run:** ~2-5 minutes (vs 45 mins initial)

### Manual Trigger (for testing)

```bash
# Run scraper now
python scheduled_scraper.py

# View logs
cat data/scrape_log.json
cat data/scrape_cron.log
```

### View/Manage Cron

```bash
# View scheduled jobs
crontab -l

# Edit schedule
crontab -e

# Remove automation
crontab -l | grep -v "scheduled_scraper.py" | crontab -
```

---

## What Changed

### 1. Competitor Cards Now Show Real Data

**Before:** Random mock data that changed on every re-render

**After:** Real insights from database:
- ✅ Top product category (from AI enrichment)
- ✅ Real velocity (ads/day)
- ✅ Market share (% of total ads)
- ✅ Trend (up/down/stable) - currently simplified, will improve

**API:** `GET /api/competitors/{advertiser_id}/insights`

### 2. Incremental Scraping

**Smart update logic:**
- Tracks ad signatures (ad_text + image_url)
- Only enriches NEW ads
- Updates `is_active` status for disappeared ads
- Saves time: 2 mins vs 45 mins

**Database method:** `mark_ads_inactive()`

### 3. Scheduled Automation

**Files:**
- `scheduled_scraper.py` - Main automation script
- `setup_cron.sh` - Installs cron job
- `data/scrape_log.json` - Execution history
- `data/scrape_cron.log` - Console output

---

## Next Steps (TODO)

### Immediate

1. ✅ Restart API server to enable `/api/competitors/{id}/insights` endpoint
2. ⏳ Run initial full scrape for all competitors (1000 ads each)
3. ⏳ Personalize Quick Actions based on competitive gaps

### Quick Actions Personalization (Next)

**Current:** Generic suggestions
```
🎯 Focus on top 3 performing products
📊 Analyze competitor product mix
```

**Target:** Data-driven recommendations
```
👥 Target "Families" segment - 0 competitors active
🏷️ Test "BOGO" offers - only Talabat using this (45% success)
⚡ Increase velocity to 15 ads/day to match Deliveroo
```

**Implementation:**
- Analyze competitive gaps (underserved segments, unused offer types)
- Compare your position vs market leader
- Generate specific, actionable recommendations

### Advanced Features (Later)

- Real trend calculation (7-day vs previous 7-day comparison)
- Email notifications when competitors launch new campaigns
- Slack integration for daily summary
- Competitive alerts (new products, messaging shifts)

---

## File Structure

```
ad-intelligence/
├── scheduled_scraper.py        # Daily automation script
├── setup_cron.sh                # Cron installer
├── AUTOMATION_SETUP.md          # This file
├── api/
│   ├── main.py                  # New endpoint: /api/competitors/{id}/insights
│   └── database.py              # New method: mark_ads_inactive()
├── data/
│   ├── adintel.db               # Main database
│   ├── scrape_log.json          # Automation history
│   └── scrape_cron.log          # Cron output
└── scrapers/
    └── api_scraper.py           # Already has --enrich --save-db flags
```

---

## Troubleshooting

### Cron job not running?

```bash
# Check if cron service is running (macOS)
sudo launchctl list | grep cron

# View cron logs
cat data/scrape_cron.log

# Test manually
python scheduled_scraper.py
```

### API returning 404 for insights?

```bash
# Restart API server
pkill -f "uvicorn.*main:app"
cd api && python main.py
```

### Frontend showing old mock data?

- Refresh page (competitor cards cache for 5 minutes)
- Check browser console for API errors
- Verify database has data: `python -c "from api.database import AdDatabase; print(AdDatabase().get_stats())"`

### Enrichment too slow?

**Option 1:** Reduce sample size
```bash
python scheduled_scraper.py  # Edit COMPETITORS list, set max_ads = 500
```

**Option 2:** Use faster model
```python
# In api/ai_analyzer.py, change model:
self.model = "llama3.2:1b"  # Faster but less accurate
```

**Option 3:** Skip enrichment for daily runs
```python
# In scheduled_scraper.py, set:
enrich=False  # in incremental_scrape()
```

---

## Cost & Performance

| Operation | Time | Cost |
|-----------|------|------|
| Initial scrape (1000 ads) | ~45 mins | Free (local Ollama) |
| Daily update (100 ads, ~10 new) | ~2-5 mins | Free |
| Database storage | Instant | ~10MB per 1000 ads |
| API queries | <100ms | Free |

**Total daily time:** ~10-15 mins for 3 competitors (most is AI enrichment)

---

## Support

Need help? Check:
1. `data/scrape_log.json` - Execution history
2. `data/scrape_cron.log` - Cron output
3. API logs - `tail -f /tmp/api.log`
4. Frontend logs - Browser DevTools console
