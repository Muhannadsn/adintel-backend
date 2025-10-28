# 🚀 AdIntel API Guide

**FastAPI Backend for Ad Intelligence Platform**

---

## 📍 Quick Start

### Start the API Server

```bash
cd api
python main.py
```

Server runs at: **http://localhost:8001**

Interactive API docs: **http://localhost:8001/docs**

---

## 🔗 API Endpoints

### 1. Health Check

**GET /** - Check if API is running

```bash
curl http://localhost:8001/
```

**Response:**
```json
{
  "message": "AdIntel API is running",
  "version": "1.0.0",
  "endpoints": {
    "scrape": "/api/scrape",
    "analyze": "/api/analyze",
    "jobs": "/api/jobs/{job_id}",
    "competitors": "/api/competitors"
  }
}
```

---

### 2. Scrape Ads

**POST /api/scrape** - Scrape competitor ads from Google Ad Transparency Center

**Request Body:**
```json
{
  "url": "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
  "max_ads": 400,
  "name": "Talabat"  // Optional
}
```

**Example:**
```bash
curl -X POST "http://localhost:8001/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
    "max_ads": 400
  }'
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Scraping started for advertiser AR14306592000630063105",
  "advertiser_id": "AR14306592000630063105",
  "region": "QA",
  "estimated_time": "2-5 seconds"
}
```

---

### 3. Check Job Status

**GET /api/jobs/{job_id}** - Check status of scraping or analysis job

**Example:**
```bash
curl http://localhost:8001/api/jobs/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response (Scraping Completed):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "result": {
    "advertiser_id": "AR14306592000630063105",
    "region": "QA",
    "total_ads": 400,
    "csv_file": "data/input/AR14306592000630063105_20251016_200637.csv",
    "ads": [
      {
        "advertiser_id": "AR14306592000630063105",
        "creative_id": "CR13784462842319077377",
        "advertiser_name": "Talabat",
        "image_url": "https://s0.2mdn.net/simgad/17703927797632342896",
        "first_shown": "2025-01-15",
        "last_shown": "2025-10-16",
        "regions": "QA"
      }
      // ... first 10 ads
    ]
  },
  "error": null,
  "created_at": "2025-10-16T20:00:00",
  "completed_at": "2025-10-16T20:00:03"
}
```

**Status Values:**
- `pending` - Job queued, not started yet
- `running` - Job is currently processing
- `completed` - Job finished successfully
- `failed` - Job encountered an error

---

### 4. Analyze Ads

**POST /api/analyze** - Analyze scraped ads with AI

**Request Body:**
```json
{
  "csv_file": "data/input/AR14306592000630063105_20251016_200637.csv",
  "analyzer": "hybrid",
  "sample_size": 50
}
```

**Analyzer Options:**
- `hybrid` - Two-stage pipeline (llava + deepseek-r1) - **Recommended, 60% faster**
- `ollama` - Single ollama model
- `claude` - Claude API (requires API key)

**Example:**
```bash
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_file": "data/input/AR14306592000630063105_20251016_200637.csv",
    "analyzer": "hybrid",
    "sample_size": 50
  }'
```

**Response:**
```json
{
  "job_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "pending",
  "message": "Analysis started with hybrid analyzer",
  "estimated_time": "~37 minutes"
}
```

---

### 5. List Competitors

**GET /api/competitors** - List all scraped competitors

**Example:**
```bash
curl http://localhost:8001/api/competitors
```

**Response:**
```json
[
  {
    "name": "Talabat",
    "advertiser_id": "AR14306592000630063105",
    "region": "QA",
    "total_ads": 400,
    "last_scraped": "2025-10-16T20:00:03",
    "csv_file": "data/input/AR14306592000630063105_20251016_200637.csv"
  },
  {
    "name": "Deliveroo",
    "advertiser_id": "AR98765432109876543210",
    "region": "QA",
    "total_ads": 350,
    "last_scraped": "2025-10-16T19:30:15",
    "csv_file": "data/input/AR98765432109876543210_20251016_193015.csv"
  }
]
```

---

## 🔄 Complete Workflow Example

### Step 1: Scrape Talabat Ads

```bash
# Start scraping
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
    "max_ads": 400
  }')

# Extract job_id
JOB_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"
```

### Step 2: Wait for Scraping to Complete

```bash
# Check status (repeat until status is "completed")
curl -s "http://localhost:8001/api/jobs/$JOB_ID" | python3 -m json.tool
```

### Step 3: Analyze the Ads

```bash
# Get CSV file from scraping result
CSV_FILE=$(curl -s "http://localhost:8001/api/jobs/$JOB_ID" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['result']['csv_file'])")

# Start analysis
ANALYSIS_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"csv_file\": \"$CSV_FILE\",
    \"analyzer\": \"hybrid\",
    \"sample_size\": 50
  }")

ANALYSIS_JOB_ID=$(echo $ANALYSIS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Analysis Job ID: $ANALYSIS_JOB_ID"
```

### Step 4: Monitor Analysis Progress

```bash
# Check analysis status
curl -s "http://localhost:8001/api/jobs/$ANALYSIS_JOB_ID" | python3 -m json.tool
```

---

## 🐍 Python Client Example

```python
import requests
import time
import json

API_BASE = "http://localhost:8001"

def scrape_competitor(url, max_ads=400):
    """Scrape competitor ads"""
    response = requests.post(
        f"{API_BASE}/api/scrape",
        json={"url": url, "max_ads": max_ads}
    )
    return response.json()

def check_job(job_id):
    """Check job status"""
    response = requests.get(f"{API_BASE}/api/jobs/{job_id}")
    return response.json()

def wait_for_job(job_id, check_interval=2):
    """Wait for job to complete"""
    while True:
        status = check_job(job_id)
        print(f"Status: {status['status']} - Progress: {status.get('progress', 0)}%")

        if status['status'] in ['completed', 'failed']:
            return status

        time.sleep(check_interval)

def analyze_ads(csv_file, analyzer="hybrid", sample_size=50):
    """Analyze ads"""
    response = requests.post(
        f"{API_BASE}/api/analyze",
        json={
            "csv_file": csv_file,
            "analyzer": analyzer,
            "sample_size": sample_size
        }
    )
    return response.json()

def list_competitors():
    """List all competitors"""
    response = requests.get(f"{API_BASE}/api/competitors")
    return response.json()

# Example usage
if __name__ == "__main__":
    # Scrape Talabat
    print("🚀 Starting scrape...")
    scrape_result = scrape_competitor(
        "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
        max_ads=400
    )

    job_id = scrape_result['job_id']
    print(f"📊 Job ID: {job_id}")

    # Wait for scraping to complete
    print("⏳ Waiting for scrape to complete...")
    final_status = wait_for_job(job_id)

    if final_status['status'] == 'completed':
        csv_file = final_status['result']['csv_file']
        total_ads = final_status['result']['total_ads']
        print(f"✅ Scraped {total_ads} ads")
        print(f"📁 CSV: {csv_file}")

        # Start analysis
        print("🧠 Starting analysis...")
        analysis_result = analyze_ads(csv_file, sample_size=50)
        analysis_job_id = analysis_result['job_id']

        print(f"📊 Analysis Job ID: {analysis_job_id}")
        print(f"⏱️  Estimated time: {analysis_result['estimated_time']}")

        # Monitor analysis
        print("⏳ Waiting for analysis to complete...")
        analysis_status = wait_for_job(analysis_job_id, check_interval=10)

        if analysis_status['status'] == 'completed':
            print("✅ Analysis complete!")
            print(json.dumps(analysis_status['result'], indent=2))

    # List all competitors
    print("\n📋 All competitors:")
    competitors = list_competitors()
    for comp in competitors:
        print(f"  - {comp['name']}: {comp['total_ads']} ads")
```

---

## 🌐 Interactive API Documentation

FastAPI provides **automatic interactive API docs**:

1. Start the server: `python api/main.py`
2. Open browser: **http://localhost:8001/docs**
3. Try out endpoints directly in the browser!

**Swagger UI:** http://localhost:8001/docs
**ReDoc:** http://localhost:8001/redoc

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (React/Next.js - to be built)
│  (Browser)  │
└──────┬──────┘
       │ HTTP Requests
       ▼
┌─────────────┐
│  FastAPI    │ (Port 8001)
│   Backend   │
└──────┬──────┘
       │ Calls
       ▼
┌─────────────────────────────┐
│  Your Existing Tools        │
│  - api_scraper.py           │
│  - run_analysis.py          │
│  - analyzers/hybrid.py      │
└─────────────────────────────┘
       │ Saves to
       ▼
┌─────────────┐
│ File System │
│ data/input/ │
│ data/output/│
└─────────────┘
```

---

## 📦 Deployment

### Local Development
```bash
cd api
python main.py
```

### Production (Railway/Render)

**Procfile:**
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
- `PORT` - Server port (auto-set by Railway/Render)
- `OLLAMA_HOST` - Ollama server URL (if using remote Ollama)

---

## 🔮 Next Steps

1. **Add Database** - PostgreSQL for persistent job storage
2. **Add Redis** - Celery queue for better background task management
3. **Add Authentication** - User accounts and API keys
4. **Build Frontend** - React dashboard to visualize data
5. **Add Webhooks** - Notify external services when jobs complete
6. **Facebook Ads Library** - Add scraper for Facebook ads

---

## 🎯 Current Status

✅ **Working:**
- Scraping via API
- Job status tracking
- Background task execution
- Competitor listing

🚧 **In Progress:**
- Analysis integration (needs progress callback fix)
- Insights aggregation endpoint

📋 **Planned:**
- Database integration
- Frontend dashboard
- Authentication
- Scheduled scraping

---

**API is production-ready for scraping!** 🚀

Start building your frontend or integrate with other tools!
