# AdIntel Strategic Intelligence Platform - Full Specification

**Version:** 2.0
**Date:** October 17, 2025
**Status:** Planning Phase

---

## Executive Summary

Transform AdIntel from a basic ad scraping tool into a **strategic intelligence platform** that answers critical competitive questions through rich data visualizations and AI-powered insights.

**Core Philosophy:** Every visualization must answer a specific strategic question that drives actionable decisions.

---

## Current State Assessment

### What We Have ✅
- Working Google Ad Transparency Center scraper
- FastAPI backend (port 8001)
- Next.js frontend (port 3000)
- Basic competitor tracking (ad count, region, last scraped)
- Simple insights dashboard (market share, competitive intensity)
- CSV storage of scraped ads

### What's Missing ❌
- **No product/category level data** - Can't see what competitors are selling
- **No messaging analysis** - Can't understand positioning strategies
- **No temporal tracking** - Can't see campaign evolution over time
- **No platform/placement data** - Can't identify channel strategies
- **Limited AI analysis** - Only basic rule-based insights

---

## Strategic Modules to Build

### Module 1: Competitive Product Focus
**Strategic Question:** *"Which products are my competitors pushing hardest, and am I competing in the right categories?"*

**Visualization:** Interactive Bubble Chart

**What User Sees:**
- Each bubble = one product/category
- X-axis = ad volume for that product
- Y-axis = campaign duration (how many days advertised)
- Bubble size = number of unique creative variations
- Bubble color = competitor (Talabat orange, Rafiq purple, etc.)

**Key Interactions:**
- Click bubble → see all ads for that product
- Filter by: My products | Competitor products | All products
- Highlights gaps where competitors dominate but you have zero presence

**Data Required:**
- Product category per ad (AI-extracted)
- Product name/type
- Ad count per product per competitor
- First seen / last seen dates
- Unique creative count

---

### Module 2: Messaging & Positioning Battle
**Strategic Question:** *"What are competitors saying in their ads? Are they price-focused, quality-focused, or speed-focused?"*

**Visualization:** Horizontal Stacked Bar Chart

**What User Sees:**
- One bar per competitor
- Bar segments show messaging theme distribution:
  - 🟢 Price/Discount (45%)
  - 🔵 Speed (25%)
  - 🟡 Quality/Premium (15%)
  - 🟣 Convenience (15%)

**Key Interactions:**
- Click segment → filter ad gallery to show only those ads
- Time filter: This week | This month | This quarter
- Compare mode: Add "My Ads" as fifth bar to see positioning gaps

**Data Required:**
- AI classification of messaging themes per ad
- Confidence scores for each theme
- Temporal data to track theme shifts over time

---

### Module 3: Creative Velocity Tracker
**Strategic Question:** *"How fast are competitors iterating on creatives? Who's testing aggressively vs. running stale campaigns?"*

**Visualization:** Calendar Heatmap + Timeline

**What User Sees:**
- 30-day calendar grid
- Each day color-coded by total new ads launched:
  - 🟢 0-5 ads (low activity)
  - 🟡 6-15 ads (moderate)
  - 🔴 16+ ads (high activity)
- Swim lanes below showing each competitor's daily activity as sparklines

**Key Interactions:**
- Click high-activity day → see all ads launched that day
- Click competitor sparkline → zoom into detailed timeline
- Spot patterns: "Talabat launches Mondays, Rafiq counters Tuesdays"

**Data Required:**
- `first_seen_date` per ad (when it first appeared)
- `last_seen_date` (when it disappeared or was retired)
- `is_active` status
- Daily aggregation: new ads per competitor

---

### Module 4: Audience Targeting Insights
**Strategic Question:** *"Who are competitors targeting, and am I missing key audience segments?"*

**Visualization:** Sankey Diagram (Flow Chart)

**What User Sees:**
- Left: Competitors
- Middle: Audience segments (Young Professionals, Families, Students, etc.)
- Right: Product categories targeted at each segment
- Line thickness = ad volume/spend

**Example Flow:**
```
Talabat ──[thick]──> Young Professionals ──> Meal Deals
        └─[thin]───> Families ──────────────> Grocery
```

**Key Interactions:**
- Click flow path → see example ads for that targeting strategy
- Filter: All segments | Under-targeted segments only
- Highlights gaps: "No one targets Health-Conscious Eaters—opportunity"

**Data Required:**
- Audience segment tags per ad (AI-inferred from creative/copy)
- Age ranges, interests, behavior signals
- Cross-reference with product categories

---

### Module 5: Platform & Placement Battle
**Strategic Question:** *"Where are competitors advertising? Am I visible on the same platforms?"*

**Visualization:** Nested Donut Chart / Multi-Layer Bar

**What User Sees:**
- Outer ring: Platforms (Facebook 45%, Instagram 35%, Google 15%, TikTok 5%)
- Inner ring: Placements within each platform (Feed 60%, Stories 30%, Marketplace 10%)
- Competitor breakdown per platform/placement

**Key Interactions:**
- Click platform → drill down to placement details
- Click placement → see competitor dominance and sample ads
- Toggle view: Ad volume | Estimated spend | Engagement signals

**Data Required:**
- Platform per ad (Facebook, Instagram, Google, TikTok, etc.)
- Placement per ad (Feed, Stories, Reels, Search, Display, etc.)
- Competitor distribution across platforms

---

### Module 6: Promo & Offer Intensity Tracker
**Strategic Question:** *"How aggressive are competitors with discounts? Am I being out-promoted?"*

**Visualization:** Stacked Area Chart Over Time

**What User Sees:**
- X-axis: Past 30/90 days
- Y-axis: Number of promo ads
- Stacked areas: Each competitor gets a color
- Annotation markers for events (Black Friday, Ramadan, holidays)

**Key Interactions:**
- Hover over spike → see top offers from that period
- Click competitor area → filter to their promo ads
- Identify promo strategies tied to events/seasons

**Data Required:**
- Promo detection per ad (AI extract: "50% off", "Free delivery", etc.)
- Offer type categorization (percentage discount, free shipping, BOGO, etc.)
- Temporal data to track promo intensity over time

---

## Implementation Architecture

### Phase 1: Data Enrichment Layer (Backend) - Week 1-2

**Goal:** Transform basic ad data into strategic intelligence

**What to Build:**

1. **AI Analysis Service** (`/api/ai_analyzer.py`)
   - Connects to Claude API
   - Analyzes each ad to extract:
     - Product category (Meal Deal, Grocery, Restaurant, etc.)
     - Messaging themes (Price, Speed, Quality, Convenience) with confidence scores
     - Target audience signals (Young Professionals, Families, Students, etc.)
     - Offer type (Discount%, Free Delivery, Limited Time, etc.)
   - Batch processing mode for efficiency

2. **Enhanced Scraper** (Update `/scrapers/api_scraper.py`)
   - After fetching ads from Google, pass each through AI analyzer
   - Store enriched data in CSV with new columns:
     - `product_category`
     - `product_name`
     - `messaging_themes` (JSON: {"price": 0.8, "speed": 0.2})
     - `audience_segment`
     - `offer_type`
     - `platform` (if available from Google Ad Transparency)
     - `placement`
     - `first_seen_date`
     - `last_seen_date`
     - `is_active`

3. **Temporal Tracking System**
   - Each scrape run compares current ads vs. previous run
   - New ads → mark `first_seen_date`
   - Missing ads → mark `last_seen_date`, set `is_active = false`
   - Store in database (SQLite or PostgreSQL) instead of CSV-only

4. **Database Migration** (Optional but recommended)
   - Move from CSV to proper database (PostgreSQL or SQLite)
   - Tables:
     - `competitors` (id, name, advertiser_id, region)
     - `ads` (id, competitor_id, ad_text, image_url, first_seen, last_seen, is_active)
     - `ad_enrichment` (ad_id, product_category, messaging_themes, audience_segment, offer_type)
     - `scrape_runs` (id, timestamp, ads_found, ads_new, ads_retired)

**How to Build:**
- Use Claude API (already available) for AI analysis
- Create prompt templates for each analysis type
- Batch process ads in groups of 10-20 to optimize API calls
- Cache results to avoid re-analyzing unchanged ads
- Add retry logic for API failures

---

### Phase 2: Strategic Insights API - Week 2-3

**Goal:** Create backend endpoints that power each visualization

**What to Build:**

1. **Product Insights Endpoint** (`GET /api/insights/products`)
   - Aggregates ads by product category
   - Returns: ad count, unique creatives, days active, top messages
   - Grouped by competitor
   - Powers: Module 1 (Bubble Chart)

2. **Messaging Breakdown Endpoint** (`GET /api/insights/messaging`)
   - Calculates theme distribution per competitor
   - Returns: percentage breakdown of price/speed/quality/convenience
   - Time-filterable (week/month/quarter)
   - Powers: Module 2 (Stacked Bar)

3. **Creative Velocity Endpoint** (`GET /api/insights/velocity`)
   - Returns daily new ad count for past 30 days
   - Breakdown by competitor
   - Identifies high-activity days
   - Powers: Module 3 (Calendar Heatmap)

4. **Audience Targeting Endpoint** (`GET /api/insights/audiences`)
   - Returns audience segment → product category mappings
   - Flow data for Sankey diagram
   - Line thickness based on ad volume
   - Powers: Module 4 (Sankey)

5. **Platform Distribution Endpoint** (`GET /api/insights/platforms`)
   - Returns platform and placement breakdown
   - Competitor distribution per platform
   - Powers: Module 5 (Donut Chart)

6. **Promo Intensity Endpoint** (`GET /api/insights/promos`)
   - Returns daily promo ad count over time
   - Offer type distribution
   - Event annotations (holidays, special days)
   - Powers: Module 6 (Area Chart)

**How to Build:**
- Query database/CSV with proper aggregations
- Use pandas for data manipulation
- Return JSON optimized for frontend charting libraries
- Add caching (Redis or simple in-memory) for expensive queries
- Include metadata: last_updated, data_quality_score

---

### Phase 3: Frontend Visualization Components - Week 3-4

**Goal:** Build interactive React components for each strategic module

**What to Build:**

1. **Component Library** (`/components/insights/`)
   - `ProductBubbleChart.tsx` - Module 1
   - `MessagingStackedBar.tsx` - Module 2
   - `CreativeVelocityHeatmap.tsx` - Module 3
   - `AudienceFlow.tsx` - Module 4 (Sankey)
   - `PlatformDonut.tsx` - Module 5
   - `PromoIntensityArea.tsx` - Module 6

2. **Shared Interaction Patterns**
   - Click-to-drill: All charts link to filtered ad gallery
   - Hover tooltips with rich context
   - Time range filters (week/month/quarter/all)
   - Competitor filters (select/deselect competitors)
   - Export functionality (PNG, PDF, CSV)

3. **Dashboard Layout** (`/app/insights/page.tsx`)
   - Organize modules into collapsible sections:
     - **Product & Category Intelligence**
       - Product Focus (Bubble) + Category Trends
     - **Creative & Messaging Strategy**
       - Messaging Themes (Stacked Bar) + Creative Velocity (Heatmap)
     - **Audience & Channel Intelligence**
       - Audience Targeting (Sankey) + Platform Distribution (Donut)
     - **Promotional Strategy**
       - Promo Intensity (Area Chart)
   - Each section has horizontal scroll carousel for multiple charts
   - Sticky section headers
   - Mobile-responsive (stack vertically on small screens)

4. **Ad Gallery Enhancement** (`/components/AdGallery.tsx`)
   - Receives filter params from chart clicks
   - Shows filtered ads with metadata:
     - Product category badge
     - Messaging theme tags
     - Audience segment
     - Platform/placement
     - Active duration
   - Infinite scroll pagination
   - Grid/list view toggle

**How to Build:**
- Use Recharts library for charts (already in project)
- React Query for data fetching (already in project)
- Tailwind for styling (already in project)
- Framer Motion for smooth transitions
- Intersection Observer for lazy-loading charts
- Local state management with useState/useContext

---

### Phase 4: Polish & Optimization - Week 4-5

**Goal:** Performance, UX refinement, error handling

**What to Build:**

1. **Performance Optimizations**
   - Lazy load chart components (only render when scrolled into view)
   - Debounce filter interactions
   - Cache API responses client-side
   - Optimize database queries with indexes
   - Add loading skeletons for better perceived performance

2. **Error Handling**
   - Graceful degradation if AI analysis fails
   - Retry logic for failed API calls
   - User-friendly error messages
   - Fallback to rule-based insights if AI unavailable

3. **Data Quality Indicators**
   - Show "Last updated: 2 hours ago" on each chart
   - Data freshness badges
   - Confidence scores for AI-extracted insights
   - Warning if data is stale (>24 hours old)

4. **User Onboarding**
   - First-time user tour highlighting each module
   - Tooltips explaining what each chart shows
   - Sample data for empty states
   - "Why this matters" explainer for each module

5. **Export & Sharing**
   - Export individual charts as PNG
   - Generate PDF report with all insights
   - Copy shareable link with filter state
   - Email digest of weekly insights

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│ 1. DATA COLLECTION                                      │
├─────────────────────────────────────────────────────────┤
│ Google Ad Transparency ──> API Scraper                  │
│   - Fetches raw ad data (text, images, regions)         │
│   - Stores in staging area                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. AI ENRICHMENT                                        │
├─────────────────────────────────────────────────────────┤
│ Claude API Analyzer                                     │
│   - Product categorization                              │
│   - Messaging theme extraction                          │
│   - Audience signal detection                           │
│   - Offer type identification                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. DATA STORAGE                                         │
├─────────────────────────────────────────────────────────┤
│ Database (PostgreSQL/SQLite)                            │
│   - Raw ads + enriched metadata                         │
│   - Temporal tracking (first_seen, last_seen)           │
│   - Competitor profiles                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. INSIGHTS ENGINE                                      │
├─────────────────────────────────────────────────────────┤
│ FastAPI Endpoints                                       │
│   - Aggregate data by product/message/platform          │
│   - Calculate trends and velocities                     │
│   - Generate strategic comparisons                      │
│   - Cache expensive queries                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. VISUALIZATION LAYER                                  │
├─────────────────────────────────────────────────────────┤
│ Next.js Frontend                                        │
│   - Interactive charts (Recharts)                       │
│   - Filtering and drilling                              │
│   - Real-time updates                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Technical Stack (No Changes Needed)

**Backend:**
- Python 3.x
- FastAPI (existing)
- Claude API (existing)
- PostgreSQL or SQLite (new - for temporal tracking)
- Pandas (for data aggregation)

**Frontend:**
- Next.js 15 (existing)
- React Query (existing)
- Recharts (existing)
- Tailwind CSS (existing)
- Framer Motion (new - for animations)

**Infrastructure:**
- Same ports: Backend 8001, Frontend 3000
- Background scraping jobs (cron or scheduler)
- Optional: Redis for caching

---

## Development Timeline

### Week 1: Data Enrichment
- **Days 1-2:** Build AI analyzer service, test on sample ads
- **Days 3-4:** Integrate analyzer into scraper pipeline
- **Days 5-7:** Add temporal tracking, database migration (CSV → DB)

### Week 2: Insights API
- **Days 1-2:** Build endpoints for Modules 1-2 (products, messaging)
- **Days 3-4:** Build endpoints for Modules 3-4 (velocity, audiences)
- **Days 5-7:** Build endpoints for Modules 5-6 (platforms, promos)

### Week 3: Frontend Components
- **Days 1-2:** Build chart components for Modules 1-2
- **Days 3-4:** Build chart components for Modules 3-4
- **Days 5-7:** Build chart components for Modules 5-6

### Week 4: Integration & Polish
- **Days 1-3:** Wire all components to dashboard, interaction patterns
- **Days 4-5:** Performance optimization, error handling
- **Days 6-7:** User testing, bug fixes

### Week 5: Launch Prep
- **Days 1-2:** Documentation, onboarding flows
- **Days 3-4:** Export/sharing features
- **Days 5-7:** Final QA, deployment

---

## Success Metrics

**User Engagement:**
- Time spent on insights dashboard
- Click-through rate on chart interactions
- Number of filtered ad galleries viewed

**Data Quality:**
- AI categorization accuracy (spot-check 100 ads, aim for 90%+)
- Data freshness (scrape runs every 24 hours)
- Coverage (percentage of ads successfully analyzed)

**Business Impact:**
- User-reported actionable insights found
- Competitive gaps identified and acted upon
- Campaign decisions influenced by platform data

---

## Future Enhancements (Post-V2)

**Module 7: Sentiment & Engagement Prediction**
- Predict which ad styles/messages will perform best
- Sentiment analysis of ad copy
- Engagement score estimation

**Module 8: Automated Alerts**
- Notify when competitor launches major campaign
- Alert when new product category emerges
- Warn when competitor changes messaging strategy

**Module 9: Competitive Benchmarking**
- Compare your ads vs. competitors side-by-side
- "What if" simulator: predict impact of changes
- ROI estimation based on competitive spend

**Module 10: Multi-Region Intelligence**
- Cross-region comparison (Qatar vs. UAE vs. Saudi)
- Regional strategy differences
- Market-specific insights

---

## Risk Mitigation

**Risk 1: AI Analysis Cost**
- **Mitigation:** Batch processing, caching, use smaller model for simple tasks

**Risk 2: Google Blocks Scraper**
- **Mitigation:** Rate limiting, rotating IPs, fallback to manual uploads

**Risk 3: Data Quality Issues**
- **Mitigation:** Confidence scores, human review for low-confidence items, fallback rules

**Risk 4: Frontend Performance with Large Datasets**
- **Mitigation:** Pagination, lazy loading, data aggregation on backend, virtual scrolling

---

## Priority Recommendation

**Start with Modules 1, 2, and 3 first:**
1. **Product Focus** (Bubble) - Highest strategic value
2. **Messaging Themes** (Stacked Bar) - Easy to implement, big impact
3. **Creative Velocity** (Heatmap) - Unique insight, low complexity

**Reason:** These three answer the most critical questions and require minimal new data collection beyond AI analysis.

---

**Now go sleep! We'll build this beast when you wake up.** 💤🚀
