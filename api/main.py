#!/usr/bin/env python3
"""
AdIntel API - FastAPI backend for ad intelligence platform
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid
import json
import sys
import os
import httpx

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from scrapers.api_scraper import GATCAPIScraper, parse_advertiser_url

# Import database for strategic insights
try:
    from api.database import AdDatabase
    DB_AVAILABLE = True
    db = AdDatabase()
except ImportError:
    print("⚠️  Database module not available. Install dependencies.")
    DB_AVAILABLE = False
    db = None

# Initialize FastAPI app
app = FastAPI(
    title="AdIntel API",
    description="API for competitive ad intelligence analysis",
    version="1.0.0"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (will move to database later)
jobs_db = {}

# ============================================================================
# Request/Response Models
# ============================================================================

class ScrapeRequest(BaseModel):
    url: str
    max_ads: int = 400
    name: Optional[str] = None  # Competitor name (optional, will auto-detect)

class ScrapeResponse(BaseModel):
    job_id: str
    status: str
    message: str
    advertiser_id: Optional[str] = None
    region: Optional[str] = None
    estimated_time: str = "2-5 seconds"

class AnalyzeRequest(BaseModel):
    csv_file: str  # Path to CSV file from scraping
    analyzer: str = "hybrid"  # hybrid, ollama, or claude
    sample_size: int = 50  # Number of ads to analyze

class AnalyzeResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[int] = None  # 0-100
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class CompetitorSummary(BaseModel):
    name: str
    advertiser_id: str
    region: str
    total_ads: int
    last_scraped: Optional[datetime] = None
    csv_file: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

# Known advertiser ID to name mapping
KNOWN_ADVERTISERS = {
    "AR14306592000630063105": "Talabat",
    "AR08778154730519003137": "Rafiq",
    "AR12079153035289296897": "Snoonu",
    "AR13676304484790173697": "Keeta",
}

def get_advertiser_name(advertiser_id: str) -> str:
    """Get friendly name for advertiser, fallback to ID if unknown"""
    return KNOWN_ADVERTISERS.get(advertiser_id, advertiser_id)

def create_job(job_type: str, params: dict) -> str:
    """Create a new job and return job ID"""
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {
        "job_id": job_id,
        "type": job_type,
        "status": "pending",
        "progress": 0,
        "params": params,
        "result": None,
        "error": None,
        "created_at": datetime.now(),
        "completed_at": None
    }
    return job_id

def update_job(job_id: str, updates: dict):
    """Update job status"""
    if job_id in jobs_db:
        jobs_db[job_id].update(updates)

def run_scraper_task(job_id: str, url: str, max_ads: int):
    """Background task to run scraper"""
    try:
        update_job(job_id, {"status": "running", "progress": 10})

        # Parse URL
        advertiser_id, region = parse_advertiser_url(url)
        if not advertiser_id:
            raise Exception("Could not parse advertiser ID from URL")

        update_job(job_id, {"progress": 20})

        # Run scraper
        scraper = GATCAPIScraper()
        ads = scraper.scrape_advertiser(
            advertiser_id=advertiser_id,
            region=region,
            max_ads=max_ads
        )

        update_job(job_id, {"progress": 70})

        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/input/{advertiser_id}_{timestamp}.csv"
        scraper.save_to_csv(ads, output_file)

        update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "result": {
                "advertiser_id": advertiser_id,
                "region": region,
                "total_ads": len(ads),
                "csv_file": output_file,
                "ads": ads[:10]  # Return first 10 ads as preview
            },
            "completed_at": datetime.now()
        })

    except Exception as e:
        update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })

def run_analyzer_task(job_id: str, csv_file: str, analyzer: str, sample_size: int):
    """Background task to run analyzer"""
    try:
        update_job(job_id, {"status": "running", "progress": 5})

        # Import here to avoid circular imports
        from run_analysis import run_pipeline

        # Run analysis
        output_dir = f"data/output/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = run_pipeline(
            input_file=csv_file,
            analyzer_type=analyzer,
            output_dir=output_dir,
            limit=sample_size,
            progress_callback=lambda p: update_job(job_id, {"progress": int(5 + (p * 0.9))})
        )

        update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "result": {
                "output_dir": output_dir,
                "total_analyzed": len(results),
                "insights": results  # Full insights
            },
            "completed_at": datetime.now()
        })

    except Exception as e:
        update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """Health check"""
    return {
        "message": "AdIntel API is running",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/scrape",
            "analyze": "/api/analyze",
            "jobs": "/api/jobs/{job_id}",
            "competitors": "/api/competitors"
        }
    }

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_ads(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape ads from Google Ad Transparency Center

    - **url**: Full GATC URL (e.g., https://adstransparency.google.com/advertiser/AR.../region=QA)
    - **max_ads**: Maximum number of ads to scrape (default: 400)
    - **name**: Optional competitor name
    """
    try:
        # Parse URL to validate it
        advertiser_id, region = parse_advertiser_url(request.url)
        if not advertiser_id:
            raise HTTPException(status_code=400, detail="Invalid GATC URL")

        # Create job
        job_id = create_job("scrape", {
            "url": request.url,
            "advertiser_id": advertiser_id,
            "region": region,
            "max_ads": request.max_ads
        })

        # Start background task
        background_tasks.add_task(run_scraper_task, job_id, request.url, request.max_ads)

        return ScrapeResponse(
            job_id=job_id,
            status="pending",
            message=f"Scraping started for advertiser {advertiser_id}",
            advertiser_id=advertiser_id,
            region=region,
            estimated_time="2-5 seconds"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_ads(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze scraped ads with AI

    - **csv_file**: Path to CSV file from scraping
    - **analyzer**: Analyzer type (hybrid, ollama, or claude)
    - **sample_size**: Number of ads to analyze (default: 50)
    """
    try:
        # Validate CSV file exists
        if not Path(request.csv_file).exists():
            raise HTTPException(status_code=404, detail="CSV file not found")

        # Create job
        job_id = create_job("analyze", {
            "csv_file": request.csv_file,
            "analyzer": request.analyzer,
            "sample_size": request.sample_size
        })

        # Estimate time
        estimated_minutes = (request.sample_size * 45) / 60  # 45 sec per ad
        estimated_time = f"~{int(estimated_minutes)} minutes"

        # Start background task
        background_tasks.add_task(
            run_analyzer_task,
            job_id,
            request.csv_file,
            request.analyzer,
            request.sample_size
        )

        return AnalyzeResponse(
            job_id=job_id,
            status="pending",
            message=f"Analysis started with {request.analyzer} analyzer",
            estimated_time=estimated_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a scraping or analysis job
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[job_id]
    return JobStatus(**job)

@app.get("/api/competitors", response_model=List[CompetitorSummary])
async def list_competitors():
    """
    List all scraped competitors (from database + CSV files for backward compatibility)
    """
    competitors_dict = {}

    # FIRST: Try to load from database (preferred source)
    if DB_AVAILABLE and db:
        try:
            # Query database for all advertisers (excluding rejected ads)
            import sqlite3
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        a.advertiser_id,
                        COUNT(*) as total_ads,
                        MAX(a.created_at) as last_scraped
                    FROM ads a
                    LEFT JOIN ad_enrichment e ON a.id = e.ad_id
                    WHERE a.advertiser_id IS NOT NULL
                      AND (e.rejected_wrong_region = 0 OR e.rejected_wrong_region IS NULL)
                    GROUP BY a.advertiser_id
                """)

                for row in cursor.fetchall():
                    advertiser_id, total_ads, last_scraped_str = row

                    # Skip unknown advertisers (where name == ID)
                    advertiser_name = get_advertiser_name(advertiser_id)
                    if advertiser_name == advertiser_id:
                        continue

                    # Parse datetime string to datetime object
                    last_scraped_dt = None
                    if last_scraped_str:
                        try:
                            last_scraped_dt = datetime.strptime(last_scraped_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            pass

                    # Use timestamp for mtime comparison
                    mtime = last_scraped_dt.timestamp() if last_scraped_dt else 0

                    competitors_dict[advertiser_id] = {
                        'mtime': mtime,
                        'data': CompetitorSummary(
                            name=advertiser_name,
                            advertiser_id=advertiser_id,
                            region="QA",  # Default region
                            total_ads=total_ads,
                            last_scraped=last_scraped_dt,
                            csv_file=None  # Database source
                        )
                    }
        except Exception as e:
            print(f"⚠️  Database query failed, falling back to CSV: {e}")

    # SECOND: Also scan CSV files (for backward compatibility)
    data_dir = Path(__file__).parent.parent / "data" / "input"
    if data_dir.exists():
        for csv_file in data_dir.glob("*.csv"):
            # Extract advertiser ID from filename
            advertiser_id = csv_file.stem.split('_')[0]

            # Skip invalid advertiser IDs and unknown advertisers (where name == ID)
            advertiser_name = get_advertiser_name(advertiser_id)
            if advertiser_id in ['None'] or 'gatc-scraped-data' in advertiser_id or not advertiser_id.startswith('AR') or advertiser_name == advertiser_id:
                continue

            # Get file modification time
            mtime = csv_file.stat().st_mtime

            # If we haven't seen this advertiser from DB, or CSV is newer, process it
            if advertiser_id not in competitors_dict or mtime > competitors_dict[advertiser_id]['mtime']:
                # Read CSV to get ad count (quick peek)
                import csv
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        ads = list(reader)
                        total_ads = len(ads)

                        # Get region from first ad
                        region = ads[0].get('regions', 'Unknown') if ads else 'Unknown'

                    competitors_dict[advertiser_id] = {
                        'mtime': mtime,
                        'data': CompetitorSummary(
                            name=get_advertiser_name(advertiser_id),
                            advertiser_id=advertiser_id,
                            region=region,
                            total_ads=total_ads,
                            last_scraped=datetime.fromtimestamp(mtime),
                            csv_file=str(csv_file)
                        )
                    }
                except Exception as e:
                    print(f"⚠️  Error reading CSV {csv_file}: {e}")

    # Return just the competitor data (not the mtime tracking)
    return [item['data'] for item in competitors_dict.values()]

@app.get("/api/insights/products")
async def get_product_insights(advertiser_id: Optional[str] = None):
    """
    Get product/category breakdown by competitor
    Powers: Module 1 (Product Focus Bubble Chart)

    Returns product intelligence with:
    - ad_count: Number of ads per product category
    - unique_creatives: Number of unique ad variations
    - days_active: How long this product has been advertised
    - product_name: Restaurant/brand name (when category is "Specific Restaurant/Brand Promo")

    Args:
        advertiser_id: Optional - filter to specific competitor

    Returns:
        {
            "products": [
                {
                    "competitor": "Talabat",
                    "advertiser_id": "AR123...",
                    "category": "Meal Deals",
                    "ad_count": 180,
                    "unique_creatives": 45,
                    "days_active": 14
                },
                {
                    "competitor": "Talabat",
                    "advertiser_id": "AR123...",
                    "category": "Specific Restaurant/Brand Promo",
                    "product_name": "Haldiram's - Indian Food",
                    "ad_count": 12,
                    "unique_creatives": 8,
                    "days_active": 5
                },
                ...
            ],
            "last_updated": "2025-10-17T06:30:00",
            "total_products": 15,
            "total_ads": 400
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get category-level breakdown from database
        products = db.get_products_by_competitor(advertiser_id)

        # EXCLUDE "Specific Restaurant/Brand Promo" aggregated entries
        # (we'll add detailed restaurant data with product_name instead)
        products = [p for p in products if p['category'] != 'Specific Restaurant/Brand Promo']

        # Enrich with competitor names
        for product in products:
            product['competitor'] = get_advertiser_name(product['advertiser_id'])

        # Get restaurant-specific data with product_name
        restaurants = db.get_restaurants_breakdown()

        # Add restaurant products to the products list with product_name
        for restaurant in restaurants:
            # restaurant['competitors'] contains advertiser_id (e.g., ['AR12079153035289296897'])
            advertiser_id_found = restaurant['competitors'][0] if restaurant['competitors'] else None

            if not advertiser_id_found:
                continue

            # Get advertiser name from ID
            advertiser_name = get_advertiser_name(advertiser_id_found)

            products.append({
                'advertiser_id': advertiser_id_found,
                'competitor': advertiser_name,
                'category': 'Specific Restaurant/Brand Promo',
                'product_name': f"{restaurant['restaurant']} - {restaurant['food_category']}",
                'ad_count': restaurant['ad_count'],
                'unique_creatives': restaurant['ad_count'],  # Estimate
                'days_active': 7  # Estimate
            })

        # Calculate totals
        total_products = len(products)
        total_ads = sum(p['ad_count'] for p in products)

        return {
            "products": products,
            "last_updated": datetime.now().isoformat(),
            "total_products": total_products,
            "total_ads": total_ads,
            "database_stats": db.get_stats() if db else {}
        }

    except Exception as e:
        print(f"Error getting product insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/messaging")
async def get_messaging_insights(time_range: str = "all", advertiser_id: Optional[str] = None):
    """
    Get messaging themes breakdown across competitors
    Powers: Module 2 (Messaging & Positioning Battle)

    Returns messaging intelligence with:
    - theme: Messaging theme (e.g., "Speed & Convenience", "Discounts & Offers")
    - ad_count: Number of ads using this theme
    - competitors: List of competitors using this theme
    - percentage: % of total ads using this theme

    Args:
        time_range: Filter by time period ("7d", "30d", "all")
        advertiser_id: Optional - filter to specific competitor

    Returns:
        {
            "themes": [
                {
                    "theme": "Speed & Convenience",
                    "ad_count": 120,
                    "percentage": 35.2,
                    "competitors": ["Talabat"],
                    "sample_messages": ["Delivered in 30 minutes", "Fast delivery guaranteed"]
                },
                ...
            ],
            "time_range": "all",
            "total_ads": 342,
            "total_themes": 8
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get messaging breakdown from database
        # Returns: {"AR123": {"price": 45, "speed": 25, ...}, "AR456": {...}, ...}
        messaging_data = db.get_messaging_breakdown(time_range)

        # Transform to theme-centric view
        # Aggregate across all competitors
        theme_aggregates = {}
        theme_competitors = {}  # Track which competitors use each theme

        for adv_id, themes in messaging_data.items():
            for theme, percentage in themes.items():
                if theme not in theme_aggregates:
                    theme_aggregates[theme] = 0
                    theme_competitors[theme] = []

                # Weight by percentage (percentage is already 0-100)
                theme_aggregates[theme] += percentage
                if percentage > 0:  # Only include competitor if they use this theme
                    theme_competitors[theme].append(adv_id)

        # Convert to list format
        themes_list = []
        total_weight = sum(theme_aggregates.values())

        for theme, weight in theme_aggregates.items():
            # Skip None/empty themes (ads without enrichment)
            if theme is None or theme == '' or not theme:
                continue

            # Calculate ad_count proportionally (estimate based on weight)
            # This is a proxy since we don't have actual ad counts per theme
            percentage = round((weight / total_weight * 100), 1) if total_weight > 0 else 0
            ad_count = int(weight)  # Use weight as proxy for ad count

            themes_list.append({
                'theme': theme.replace('_', ' ').title(),
                'ad_count': ad_count,
                'percentage': percentage,
                'competitors': [get_advertiser_name(aid) for aid in theme_competitors[theme]]
            })

        # Sort by ad_count descending
        themes_list.sort(key=lambda x: x['ad_count'], reverse=True)

        return {
            "themes": themes_list,
            "time_range": time_range,
            "total_ads": sum(t['ad_count'] for t in themes_list),
            "total_themes": len(themes_list),
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting messaging insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/velocity")
async def get_velocity_insights(days: int = 30):
    """
    Get creative velocity - daily new ad launch frequency
    Powers: Module 3 (Creative Velocity Heatmap)

    Returns daily ad launch data for heatmap visualization
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(status_code=503, detail="Database not available")

        velocity_data = db.get_daily_velocity(days)

        # Enrich with competitor names
        for day in velocity_data:
            enriched_competitors = {}
            for adv_id, count in day['by_competitor'].items():
                enriched_competitors[get_advertiser_name(adv_id)] = count
            day['by_competitor'] = enriched_competitors

        return {
            "timeline": velocity_data,
            "days": days,
            "total_days_with_activity": len([d for d in velocity_data if d['total_new_ads'] > 0]),
            "avg_daily_ads": sum(d['total_new_ads'] for d in velocity_data) / days if days > 0 else 0
        }
    except Exception as e:
        print(f"Error getting velocity insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/audiences")
async def get_audience_insights():
    """
    Get audience segment targeting breakdown
    Powers: Module 4 (Audience Targeting Flow)

    Returns audience intelligence with:
    - segment: Audience segment name (e.g., "New Customers", "Families")
    - competitors: List of competitors targeting this segment
    - total_ads: Number of ads targeting this segment
    - percentage: % of total ads targeting this segment
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(status_code=503, detail="Database not available")

        audience_data = db.get_audience_breakdown()

        # Enrich with competitor names
        for segment in audience_data:
            segment['competitors'] = [get_advertiser_name(aid) for aid in segment['competitors']]

        return {
            "segments": audience_data,
            "total_segments": len(audience_data),
            "total_ads": sum(s['total_ads'] for s in audience_data),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting audience insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/promos")
async def get_promo_insights(days: int = 30):
    """
    Get promo/offer intensity timeline
    Powers: Module 6 (Promo Intensity)

    Returns promo activity data showing:
    - Daily promo ad counts
    - Breakdown by offer type (percentage_discount, bogo, free_delivery, etc.)
    - Intensity trends over time
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(status_code=503, detail="Database not available")

        promo_data = db.get_promo_timeline(days)

        # Calculate totals
        total_promos = sum(d['total_promos'] for d in promo_data)
        avg_daily_promos = total_promos / days if days > 0 else 0

        # Get offer type breakdown
        offer_types = {}
        for day in promo_data:
            for offer_type, count in day['by_offer_type'].items():
                offer_types[offer_type] = offer_types.get(offer_type, 0) + count

        return {
            "timeline": promo_data,
            "days": days,
            "total_promos": total_promos,
            "avg_daily_promos": round(avg_daily_promos, 1),
            "offer_type_breakdown": offer_types,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting promo insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competitors/{advertiser_id}/insights")
async def get_competitor_insights(advertiser_id: str):
    """
    Get real strategic insights for a specific competitor
    Powers: CompetitorCard intelligence

    Returns:
    - top_product_category: Most advertised product
    - velocity: Ads per day
    - trend: up/down/stable compared to last week
    - share_of_voice: % of ads in last 30 days (more accurate than market share)
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(status_code=503, detail="Database not available")

        # Get competitor's ads
        ads = db.get_ads_by_competitor(advertiser_id, active_only=True)

        if not ads:
            return {
                "advertiser_id": advertiser_id,
                "total_ads": 0,
                "velocity": 0,
                "trend": "stable",
                "trend_percent": 0,
                "top_category": "Unknown",
                "category_percent": 0,
                "share_of_voice": 0
            }

        total_ads = len(ads)

        # Calculate velocity (ads per day)
        # Assume ads span the last 30 days for now
        velocity = round(total_ads / 30, 1)

        # Get top product category
        product_counts = {}
        for ad in ads:
            category = ad.get('product_category')
            if category:
                product_counts[category] = product_counts.get(category, 0) + 1

        top_category = "Unknown"
        category_percent = 0
        if product_counts:
            top_category = max(product_counts.items(), key=lambda x: x[1])[0]
            category_percent = round((product_counts[top_category] / total_ads) * 100, 1)

        # Calculate REAL trend (compare last 7 days vs previous 7 days)
        from datetime import datetime, timedelta
        now = datetime.now()
        seven_days_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        fourteen_days_ago = (now - timedelta(days=14)).strftime('%Y-%m-%d')

        # Count ads in last 7 days
        last_week_ads = [ad for ad in ads if ad.get('first_seen_date', '') >= seven_days_ago]

        # Count ads in previous 7 days (8-14 days ago)
        previous_week_ads = [
            ad for ad in ads
            if fourteen_days_ago <= ad.get('first_seen_date', '') < seven_days_ago
        ]

        last_week_count = len(last_week_ads)
        previous_week_count = len(previous_week_ads)

        # Calculate trend
        if previous_week_count == 0:
            # Not enough data to compare
            trend = 'stable'
            trend_percent = 0
        else:
            change = last_week_count - previous_week_count
            trend_percent = abs(round((change / previous_week_count) * 100))

            if change > 0:
                trend = 'up'
            elif change < 0:
                trend = 'down'
            else:
                trend = 'stable'
                trend_percent = 0

        # Calculate Share of Voice (% of ads in last 30 days only)
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Get all ads from last 30 days
        all_recent_ads = []
        for ad in db.get_all_ads(active_only=True):
            first_seen = ad.get('first_seen_date', '')
            if first_seen >= thirty_days_ago:
                all_recent_ads.append(ad)

        # Get this competitor's ads from last 30 days
        competitor_recent_ads = [ad for ad in ads if ad.get('first_seen_date', '') >= thirty_days_ago]

        # Calculate share of voice (more accurate than "market share")
        share_of_voice = round((len(competitor_recent_ads) / len(all_recent_ads)) * 100, 1) if all_recent_ads else 0

        return {
            "advertiser_id": advertiser_id,
            "total_ads": total_ads,
            "velocity": velocity,
            "trend": trend,
            "trend_percent": trend_percent,
            "top_category": top_category,
            "category_percent": category_percent,
            "share_of_voice": share_of_voice  # Renamed from market_share
        }

    except Exception as e:
        print(f"Error getting competitor insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competitors/{advertiser_id}/ads")
async def get_competitor_ads(
    request: Request,
    advertiser_id: str,
    limit: int = 50,
    active_only: bool = True,
    category: Optional[str] = None
):
    """
    Get all ads for a specific competitor with images for carousel
    Powers: Competitor deep-dive page ad gallery

    Args:
        advertiser_id: Competitor's advertiser ID
        limit: Max number of ads to return (default: 50)
        active_only: Only return active ads (default: True)
        category: Optional product category filter (e.g., "Burgers & Fast Food")

    Returns:
        {
            "ads": [
                {
                    "id": 123,
                    "image_url": "https://...",
                    "ad_text": "50% off first order",
                    "product_category": "Meal Deals",
                    "offer_type": "percentage_discount",
                    "offer_details": "50% off",
                    "primary_theme": "price",
                    "target_audience": "new_customers",
                    "first_seen_date": "2025-10-15",
                    "is_active": true
                },
                ...
            ],
            "total_ads": 100,
            "advertiser_name": "Talabat"
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get ads from database
        ads = db.get_ads_by_competitor(advertiser_id, active_only=active_only)

        # Filter by category if specified (BEFORE limiting!)
        if category:
            ads = [ad for ad in ads if ad.get('product_category') == category]

        # Limit results AFTER filtering
        limited_ads = ads[:limit] if limit else ads

        # Format for frontend (include all fields needed for display)
        # IMPORTANT: Proxy image URLs to bypass ad blockers
        from urllib.parse import quote

        # Get the host from the incoming request (works across network!)
        # This ensures images load on any device accessing the API
        base_url = str(request.base_url).rstrip('/')

        formatted_ads = []
        for ad in limited_ads:
            image_url = ad.get('image_url')
            # Proxy the image URL through our backend to bypass ad blockers
            if image_url:
                proxied_url = f"{base_url}/api/proxy/image?url={quote(image_url)}"
            else:
                proxied_url = None

            formatted_ads.append({
                'id': ad.get('id'),
                'image_url': proxied_url,
                'ad_text': ad.get('ad_text', 'Unknown'),
                'product_category': ad.get('product_category'),
                'product_name': ad.get('product_name'),
                'offer_type': ad.get('offer_type'),
                'offer_details': ad.get('offer_details'),
                'primary_theme': ad.get('primary_theme'),
                'target_audience': ad.get('target_audience'),
                'first_seen_date': ad.get('first_seen_date'),
                'last_seen_date': ad.get('last_seen_date'),
                'is_active': ad.get('is_active', True),
                # Vision-enriched fields
                'brand': ad.get('brand'),
                'food_category': ad.get('food_category'),
                'detected_region': ad.get('detected_region'),
                'rejected_wrong_region': ad.get('rejected_wrong_region')
            })

        return {
            "ads": formatted_ads,
            "total_ads": len(ads),
            "returned_ads": len(formatted_ads),
            "advertiser_name": get_advertiser_name(advertiser_id),
            "advertiser_id": advertiser_id
        }

    except Exception as e:
        print(f"Error getting competitor ads: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/offers")
async def get_offers_breakdown():
    """
    Get active offers breakdown with % distribution
    Powers: Active Offers widget (simple % table for marketing teams)

    Returns:
    - offer_type: Type of offer (percentage_discount, bogo, free_delivery, etc.)
    - label: Friendly name ("% Off Discounts", "Buy One Get One")
    - ad_count: Number of ads using this offer
    - percentage: % of total active offers
    - competitors: List of competitors using this offer
    - sample_offers: 3 example offers for context

    Example:
        {
            "offers": [
                {
                    "offer_type": "percentage_discount",
                    "label": "% Off Discounts",
                    "ad_count": 45,
                    "percentage": 52.3,
                    "competitors": ["Talabat"],
                    "sample_offers": ["50% off first order", "40% off 12-3pm", "25% off weekend"]
                },
                ...
            ],
            "total_offers": 86,
            "total_offer_types": 5
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get offers breakdown from database
        offers = db.get_offers_breakdown()

        # Enrich with competitor names
        for offer in offers:
            offer['competitors'] = [get_advertiser_name(aid) for aid in offer['competitors']]

        # Calculate totals
        total_offers = sum(o['ad_count'] for o in offers)
        total_offer_types = len(offers)

        return {
            "offers": offers,
            "total_offers": total_offers,
            "total_offer_types": total_offer_types,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting offers breakdown: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/restaurants")
async def get_restaurants_breakdown():
    """
    Get top restaurants being promoted with % distribution
    Powers: Top Restaurants widget (extracted from vision AI)

    Returns:
    - restaurant: Restaurant name (e.g., "Haldiram's", "Burger King")
    - ad_count: Number of ads promoting this restaurant
    - percentage: % of total restaurant promo ads
    - food_category: Category (e.g., "Pizza & Italian")
    - competitors: List of platforms promoting this restaurant

    Example:
        {
            "restaurants": [
                {
                    "restaurant": "Haldiram's",
                    "ad_count": 12,
                    "percentage": 15.3,
                    "food_category": "Asian Food (Chinese/Thai/Japanese)",
                    "competitors": ["Talabat"]
                },
                ...
            ],
            "total_restaurants": 18,
            "total_ads": 78
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get restaurants breakdown from database
        restaurants = db.get_restaurants_breakdown()

        # Enrich with competitor names
        for restaurant in restaurants:
            restaurant['competitors'] = [get_advertiser_name(aid) for aid in restaurant['competitors']]

        # Calculate totals
        total_ads = sum(r['ad_count'] for r in restaurants)
        total_restaurants = len(restaurants)

        return {
            "restaurants": restaurants,
            "total_restaurants": total_restaurants,
            "total_ads": total_ads,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting restaurants breakdown: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/brands")
async def get_brands_breakdown():
    """
    Get brand mentions breakdown with % distribution
    Vision-extracted brand data from LLaVA

    Returns:
    - brand: Brand name (e.g., "Snoonu", "Talabat")
    - ad_count: Number of ads mentioning this brand
    - percentage: % of total brand-mention ads
    - competitors: List of platforms promoting this brand
    - food_categories: List of food categories this brand is associated with

    Example:
        {
            "brands": [
                {
                    "brand": "Snoonu",
                    "ad_count": 25,
                    "percentage": 45.5,
                    "competitors": ["AR12079153035289296897"],
                    "food_categories": ["Pizza & Italian", "Burgers & Fast Food"]
                },
                ...
            ],
            "total_brands": 5,
            "total_ads": 55
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get brands breakdown from database
        brands = db.get_brands_breakdown()

        # Enrich with competitor names
        for brand in brands:
            brand['competitors'] = [get_advertiser_name(aid) for aid in brand['competitors']]

        # Calculate totals
        total_ads = sum(b['ad_count'] for b in brands)
        total_brands = len(brands)

        return {
            "brands": brands,
            "total_brands": total_brands,
            "total_ads": total_ads,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting brands breakdown: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/categories")
async def get_product_categories_breakdown():
    """
    Get product categories breakdown with % distribution
    General product category data (retail, restaurant, electronics, beauty, etc.)

    Returns:
    - product_category: Category name (e.g., "retail", "restaurant", "electronics")
    - category_label: Friendly name (e.g., "Retail", "Restaurant", "Electronics")
    - ad_count: Number of ads in this category
    - percentage: % of total ads
    - competitors: List of platforms advertising this category
    - brands: List of brands in this category

    Example:
        {
            "categories": [
                {
                    "product_category": "retail",
                    "category_label": "Retail",
                    "ad_count": 49,
                    "percentage": 43.4,
                    "competitors": ["Snoonu", "Keeta"],
                    "brands": ["Snoonu", "Keeta", "Talabat"]
                },
                ...
            ],
            "total_categories": 13,
            "total_ads": 113
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get product categories breakdown from database
        categories = db.get_product_categories_breakdown()

        # Enrich with competitor names
        for category in categories:
            category['competitors'] = [get_advertiser_name(aid) for aid in category['competitors']]

        # Calculate totals
        total_ads = sum(c['ad_count'] for c in categories)
        total_categories = len(categories)

        return {
            "categories": categories,
            "total_categories": total_categories,
            "total_ads": total_ads,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting product categories breakdown: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/food-categories")
async def get_food_categories_breakdown():
    """
    Get food categories breakdown with % distribution
    Vision-extracted food category data from LLaVA
    (Legacy endpoint - for restaurant-specific food categories)

    Returns:
    - food_category: Food category name (e.g., "Pizza & Italian", "Burgers & Fast Food")
    - ad_count: Number of ads in this category
    - percentage: % of total food category ads
    - competitors: List of platforms advertising this category
    - brands: List of brands in this category

    Example:
        {
            "food_categories": [
                {
                    "food_category": "Pizza & Italian",
                    "ad_count": 15,
                    "percentage": 35.2,
                    "competitors": ["Snoonu", "Talabat"],
                    "brands": ["Domino's", "Pizza Hut", "Snoonu"]
                },
                ...
            ],
            "total_categories": 8,
            "total_ads": 42
        }
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please scrape ads with --save-db flag first."
            )

        # Get food categories breakdown from database
        categories = db.get_food_categories_breakdown()

        # Enrich with competitor names
        for category in categories:
            category['competitors'] = [get_advertiser_name(aid) for aid in category['competitors']]

        # Calculate totals
        total_ads = sum(c['ad_count'] for c in categories)
        total_categories = len(categories)

        return {
            "food_categories": categories,
            "total_categories": total_categories,
            "total_ads": total_ads,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error getting food categories breakdown: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights/weekly")
async def get_weekly_insights(use_ai: bool = False, sample_size: int = 3):
    """
    Generate AI-powered weekly insights comparing all competitors with Vision AI
    Returns strategic summary + top 3 actionable insights for the dashboard

    - **use_ai**: Enable Vision AI analysis (default: False, set to True for deep analysis)
    - **sample_size**: Number of ads to analyze per competitor (default: 3, max: 20)
    """
    try:
        # Get all competitors
        competitors_data = await list_competitors()

        if not competitors_data:
            return {"insights": []}

        # Convert Pydantic models to dicts for insights engine
        competitors_list = [c.dict() for c in competitors_data]
        data_dir = Path(__file__).parent.parent / "data" / "input"

        if use_ai:
            # Use AI-powered vision analysis
            from insights_engine import get_insights_engine

            print("🤖 Generating AI-powered insights with Vision analysis...")
            engine = get_insights_engine()

            # Get full analysis data including visual insights
            analysis_data = engine._gather_analysis_data(
                competitors_list,
                data_dir,
                sample_size=min(sample_size, 20)
            )

            # Generate insights
            insights = engine._generate_ai_insights(analysis_data)

            # Aggregate visual data for charts
            all_categories = {}
            all_emotions = {}
            all_themes = {}

            for comp in analysis_data.get('competitors', []):
                visual = comp.get('visual_strategy', {})
                categories = visual.get('category_breakdown', {})

                # Aggregate categories
                for cat, count in categories.items():
                    all_categories[cat] = all_categories.get(cat, 0) + count

                # Track emotion and theme
                emotion = visual.get('top_emotion', 'neutral')
                all_emotions[emotion] = all_emotions.get(emotion, 0) + 1

                theme = visual.get('top_theme', 'generic')
                all_themes[theme] = all_themes.get(theme, 0) + 1

            return {
                "insights": insights,
                "visual_data": {
                    "categories": all_categories,
                    "emotions": all_emotions,
                    "themes": all_themes
                }
            }
        else:
            # Enhanced rule-based insights with actionable intelligence
            sorted_by_ads = sorted(competitors_data, key=lambda x: x.total_ads, reverse=True)
            total_ads = sum(c.total_ads for c in competitors_data)

            # Aggregate basic data from CSVs for charts (no AI analysis needed)
            all_formats = {}
            competitor_ad_counts = {}

            for comp in competitors_data:
                csv_file = Path(comp.csv_file) if comp.csv_file else None
                competitor_ad_counts[comp.name] = comp.total_ads

                if csv_file and csv_file.exists():
                    import csv as csv_module
                    import re
                    with open(csv_file, 'r') as f:
                        reader = csv_module.DictReader(f)
                        for ad in reader:
                            # Extract format from html_content dimensions
                            html = ad.get('html_content', '')
                            if html:
                                # Extract dimensions from HTML (e.g., height="250" width="300")
                                height_match = re.search(r'height="(\d+)"', html)
                                width_match = re.search(r'width="(\d+)"', html)

                                if height_match and width_match:
                                    h = int(height_match.group(1))
                                    w = int(width_match.group(1))

                                    # Categorize by common ad sizes
                                    if w == 300 and h == 250:
                                        ad_format = "Medium Rectangle (300x250)"
                                    elif w == 728 and h == 90:
                                        ad_format = "Leaderboard (728x90)"
                                    elif w == 320 and h == 50:
                                        ad_format = "Mobile Banner (320x50)"
                                    elif w == 160 and h == 600:
                                        ad_format = "Wide Skyscraper (160x600)"
                                    elif w == 300 and h == 600:
                                        ad_format = "Half Page (300x600)"
                                    elif w == 970 and h == 250:
                                        ad_format = "Billboard (970x250)"
                                    elif h > w:
                                        ad_format = "Vertical"
                                    elif w > h * 2:
                                        ad_format = "Banner"
                                    else:
                                        ad_format = "Square/Rectangle"

                                    all_formats[ad_format] = all_formats.get(ad_format, 0) + 1

            insights = []

            # Insight 1: Competitive threat - market leader dominance
            if len(sorted_by_ads) >= 2:
                leader = sorted_by_ads[0]
                second = sorted_by_ads[1]
                ratio = round(leader.total_ads / max(second.total_ads, 1), 1)

                # Calculate market share
                leader_share = int((leader.total_ads / total_ads) * 100)

                if ratio >= 2.0:
                    insights.append({
                        "title": f"{leader.name} owns {leader_share}% market share - aggressive threat",
                        "description": f"{leader.name} is running {ratio}x more ads than {second.name}. Their {leader.total_ads} active campaigns suggest heavy investment to dominate. You need to increase ad spend by {int((ratio - 1) * 100)}% to compete at their level.",
                        "metric": f"{leader_share}%",
                        "type": "warning",
                        "cta": f"Analyze {leader.name}'s Strategy",
                        "link": f"/competitor/{leader.advertiser_id}"
                    })
                else:
                    insights.append({
                        "title": f"Competitive market - {leader.name} leads by narrow margin",
                        "description": f"{leader.name} has {leader.total_ads} ads vs {second.name}'s {second.total_ads}. Market is fragmented ({leader_share}% vs {int((second.total_ads/total_ads)*100)}%). Opportunity to gain share with targeted campaigns.",
                        "metric": f"{ratio}x",
                        "type": "info",
                        "cta": "Find Gaps to Exploit",
                        "link": "/compare"
                    })

            # Insight 2: Campaign intensity benchmark
            avg_ads = total_ads // len(competitors_data) if competitors_data else 0

            if avg_ads > 90:
                insights.append({
                    "title": f"High-intensity market - {avg_ads} avg ads per competitor",
                    "description": f"Competitors are running {total_ads} total campaigns. This saturated market requires premium creative and targeting to break through. Budget recommendation: minimum {avg_ads} active ads to stay visible.",
                    "metric": f"{total_ads}",
                    "type": "warning",
                    "cta": "Benchmark Your Spend",
                    "link": "/compare"
                })
            elif avg_ads < 40:
                insights.append({
                    "title": f"Low competition window - only {avg_ads} avg ads",
                    "description": f"Market is underserved with just {total_ads} total campaigns. Perfect opportunity to dominate with aggressive spend. Launching {avg_ads * 2}+ campaigns could secure market leadership.",
                    "metric": f"{total_ads}",
                    "type": "success",
                    "cta": "Seize Opportunity",
                    "link": "/scrape"
                })
            else:
                insights.append({
                    "title": f"Moderate competition - {avg_ads} avg campaigns",
                    "description": f"{total_ads} total ads across market. Balanced competition. Focus on creative differentiation and precise targeting to outperform the {avg_ads}-ad benchmark.",
                    "metric": f"{avg_ads}",
                    "type": "info",
                    "cta": "Compare Strategies",
                    "link": "/compare"
                })

            # Insight 3: Strategic opportunity - weakest competitor or market gap
            if len(sorted_by_ads) >= 3:
                weakest = sorted_by_ads[-1]
                leader = sorted_by_ads[0]
                gap = leader.total_ads - weakest.total_ads

                insights.append({
                    "title": f"{weakest.name} is vulnerable - {gap} fewer ads than leader",
                    "description": f"{weakest.name} only running {weakest.total_ads} campaigns while {leader.name} runs {leader.total_ads}. This {gap}-campaign gap represents untapped market share. Target their customers with {weakest.total_ads * 2}+ ads to steal share.",
                    "metric": f"-{gap}",
                    "type": "success",
                    "cta": f"Attack {weakest.name}'s Market",
                    "link": f"/competitor/{weakest.advertiser_id}"
                })

            # Generate strategic summary (concise version)
            if len(sorted_by_ads) >= 3:
                leader = sorted_by_ads[0]
                second = sorted_by_ads[1]
                weakest = sorted_by_ads[-1]
                leader_share = int((leader.total_ads / total_ads) * 100)
                second_share = int((second.total_ads / total_ads) * 100)

                # Concise market characterization
                if avg_ads > 90:
                    intensity = "highly competitive"
                elif avg_ads < 40:
                    intensity = "low competition"
                else:
                    intensity = "moderately competitive"

                # Build concise summary (1-2 sentences max)
                summary = f"{leader.name} leads with {leader.total_ads} ads ({leader_share}%). "

                if leader.total_ads / max(second.total_ads, 1) >= 2.0:
                    summary += f"{intensity.capitalize()} market—focus on differentiation and spend."
                else:
                    summary += f"{intensity.capitalize()} and fragmented ({leader.name} {leader_share}%, {second.name} {second_share}%)—target {weakest.name}'s {weakest.total_ads} ad gap."
            else:
                summary = f"{total_ads} campaigns tracked. Add competitors for insights."

            return {
                "summary": summary,
                "insights": insights[:3],
                "visual_data": {
                    "formats": all_formats,
                    "competitors": competitor_ad_counts
                }
            }

    except Exception as e:
        print(f"Error generating insights: {e}")
        import traceback
        traceback.print_exc()
        return {"insights": []}

@app.get("/api/insights/{csv_file:path}")
async def get_insights(csv_file: str):
    """
    Get insights for a specific competitor (from analysis results)
    """
    # Find corresponding analysis output
    output_dir = Path("data/output")

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="No analysis results found")

    # Find latest analysis for this CSV
    # This is a placeholder - will improve with database

    return {
        "message": "Insights endpoint - will implement with database",
        "csv_file": csv_file
    }

@app.get("/api/insights/strategic/{module}")
async def get_strategic_insights(module: str):
    """
    🎯 PERSONALIZED AI Strategic Insights - Comparing YOUR COMPANY vs Competitors

    Uses DeepSeek/Llama to generate actionable quick actions based on real competitive data

    Args:
        module: products|messaging|velocity|audiences|platforms|promos

    Returns:
        [
            {
                "icon": "🎯",
                "text": "Talabat runs 3x more promo ads - increase discount campaigns",
                "color": "red"
            },
            ...
        ]
    """
    try:
        if not DB_AVAILABLE or not db:
            return {
                "actions": [
                    {"icon": "📊", "text": "Scrape competitor data to enable AI insights", "color": "blue"},
                    {"icon": "🎯", "text": "Add competitors to unlock strategic analysis", "color": "purple"},
                    {"icon": "⚡", "text": "Enable database to get personalized recommendations", "color": "green"}
                ]
            }

        # Import strategic analyst
        from api.strategic_analyst import get_strategic_analyst

        analyst = get_strategic_analyst()
        actions = analyst.generate_quick_actions(db, module=module)

        return {"actions": actions}

    except Exception as e:
        print(f"❌ Error generating strategic insights: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to generic actions
        return {
            "actions": [
                {"icon": "⚠️", "text": f"AI analyst error - check DeepSeek/Llama status", "color": "red"},
                {"icon": "📊", "text": "Increase ad volume to match top competitor", "color": "blue"},
                {"icon": "💡", "text": "Analyze competitor creative strategies", "color": "purple"}
            ]
        }

@app.delete("/api/ads/{ad_id}")
async def delete_ad(ad_id: int):
    """
    Delete an ad from the database (marks as rejected/deleted)

    Args:
        ad_id: The database ID of the ad to delete

    Returns:
        Success message with the deleted ad ID
    """
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )

        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            # First check if ad exists
            cursor = conn.execute("SELECT id FROM ads WHERE id = ?", (ad_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ad not found")

            # Mark the ad as rejected (soft delete)
            conn.execute(
                "UPDATE ad_enrichment SET rejected_wrong_region = 1 WHERE ad_id = ?",
                (ad_id,)
            )

            # If no enrichment record exists, create one
            cursor = conn.execute(
                "SELECT ad_id FROM ad_enrichment WHERE ad_id = ?",
                (ad_id,)
            )
            if not cursor.fetchone():
                conn.execute(
                    "INSERT INTO ad_enrichment (ad_id, rejected_wrong_region) VALUES (?, 1)",
                    (ad_id,)
                )

            conn.commit()

        return {
            "success": True,
            "message": f"Ad {ad_id} deleted successfully",
            "ad_id": ad_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting ad: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/ads/{ad_id}")
async def update_ad(ad_id: int, updates: dict):
    """Update ad fields (product_category, product_name, etc.)"""
    try:
        if not DB_AVAILABLE or not db:
            raise HTTPException(status_code=503, detail="Database not available")

        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            # Check if ad exists
            cursor = conn.execute("SELECT id FROM ads WHERE id = ?", (ad_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ad not found")

            # Build update query for ad_enrichment table
            allowed_fields = ['product_category', 'product_name']
            update_fields = {}

            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields[field] = value

            if not update_fields:
                raise HTTPException(status_code=400, detail="No valid fields to update")

            # Check if enrichment record exists
            cursor = conn.execute("SELECT ad_id FROM ad_enrichment WHERE ad_id = ?", (ad_id,))
            enrichment_exists = cursor.fetchone() is not None

            if enrichment_exists:
                # Update existing record
                set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
                values = list(update_fields.values()) + [ad_id]
                conn.execute(
                    f"UPDATE ad_enrichment SET {set_clause} WHERE ad_id = ?",
                    values
                )
            else:
                # Insert new record
                fields = ['ad_id'] + list(update_fields.keys())
                placeholders = ','.join(['?'] * len(fields))
                values = [ad_id] + list(update_fields.values())
                conn.execute(
                    f"INSERT INTO ad_enrichment ({','.join(fields)}) VALUES ({placeholders})",
                    values
                )

            conn.commit()

        return {
            "success": True,
            "message": f"Ad {ad_id} updated successfully",
            "ad_id": ad_id,
            "updated_fields": list(update_fields.keys())
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating ad: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxy/image")
async def proxy_image(url: str):
    """
    Proxy Google ad images to bypass ad blocker restrictions

    Args:
        url: The Google ad image URL to proxy

    Returns:
        The image with proper content-type headers

    Example:
        /api/proxy/image?url=https://tpc.googlesyndication.com/archive/simgad/123...
    """
    try:
        # Validate URL is from Google's ad servers
        allowed_domains = ['tpc.googlesyndication.com', 's0.2mdn.net']
        from urllib.parse import urlparse
        parsed = urlparse(url)

        if parsed.hostname not in allowed_domains:
            raise HTTPException(
                status_code=400,
                detail=f"Only images from {allowed_domains} are allowed"
            )

        # Fetch the image from Google
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Return the image with proper headers
            return Response(
                content=response.content,
                media_type=response.headers.get('content-type', 'image/png'),
                headers={
                    'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
                    'Access-Control-Allow-Origin': '*'
                }
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Run the app
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
