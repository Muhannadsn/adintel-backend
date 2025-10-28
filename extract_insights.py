#!/usr/bin/env python3
"""
Strategic Insights Extractor for Pitch Deck
Generates pattern detection, threat identification, and quantified proof points
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Competitor name mapping
COMPETITORS = {
    "AR14306592000630063105": "Talabat",
    "AR08778154730519003137": "Rafiq",
    "AR12079153035289296897": "Snoonu",
    "AR13676304484790173697": "Keeta",
}

# YOUR COMPANY (Protagonist)
YOUR_COMPANY_ID = "AR12079153035289296897"  # Snoonu
YOUR_COMPANY_NAME = "Snoonu"

# Competitors (Antagonists)
COMPETITOR_IDS = [aid for aid in COMPETITORS.keys() if aid != YOUR_COMPANY_ID]

def get_db():
    return sqlite3.connect('data/adintel.db')

def format_date(date_str):
    """Format date for display"""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        return date_str

def get_competitor_name(advertiser_id):
    return COMPETITORS.get(advertiser_id, advertiser_id)

# ============================================================================
# A. PATTERN DETECTION
# ============================================================================

def detect_category_surge():
    """
    Find competitors with significant increases in category activity
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("A. PATTERN DETECTION - Category Activity Surges")
    print("="*80)

    # Get ads by competitor, category, and month
    query = """
    SELECT
        a.advertiser_id,
        e.product_category,
        DATE(a.first_seen_date) as ad_date,
        COUNT(*) as ad_count
    FROM ads a
    JOIN ad_enrichment e ON a.id = e.ad_id
    WHERE e.product_category IS NOT NULL
    GROUP BY a.advertiser_id, e.product_category, DATE(a.first_seen_date)
    ORDER BY a.advertiser_id, e.product_category, ad_date
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Aggregate by competitor, category, and month
    monthly_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for advertiser_id, category, ad_date, count in results:
        if not ad_date:
            continue
        try:
            date = datetime.strptime(ad_date, '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')  # e.g., "2025-10"
            monthly_data[advertiser_id][category][month_key] += count
        except:
            continue

    # Find surges (month-over-month increases > 200%)
    insights = []
    for advertiser_id, categories in monthly_data.items():
        for category, months in categories.items():
            sorted_months = sorted(months.items())
            if len(sorted_months) >= 2:
                for i in range(1, len(sorted_months)):
                    prev_month, prev_count = sorted_months[i-1]
                    curr_month, curr_count = sorted_months[i]

                    if prev_count > 0:
                        percent_change = ((curr_count - prev_count) / prev_count) * 100

                        if percent_change >= 200:  # 200% increase = 3x
                            insights.append({
                                'competitor': get_competitor_name(advertiser_id),
                                'category': category,
                                'prev_month': prev_month,
                                'prev_count': prev_count,
                                'curr_month': curr_month,
                                'curr_count': curr_count,
                                'percent_change': int(percent_change)
                            })

    if insights:
        for insight in insights[:5]:  # Top 5
            print(f"\n✅ {insight['competitor']} launched {insight['curr_count']} campaigns in {insight['category']}")
            print(f"   during {insight['curr_month']}, compared to {insight['prev_count']} in {insight['prev_month']}—a {insight['percent_change']}% increase.")
    else:
        print("\n⚠️  Not enough historical data yet. Continue scraping to detect patterns.")

    db.close()
    return insights

def detect_coordinated_promos():
    """
    Find dates when multiple competitors launched similar campaigns
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("PATTERN DETECTION - Coordinated Promo Activity")
    print("="*80)

    # Get promo launches by date
    query = """
    SELECT
        DATE(a.first_seen_date) as launch_date,
        a.advertiser_id,
        e.offer_type,
        e.offer_details
    FROM ads a
    JOIN ad_enrichment e ON a.id = e.ad_id
    WHERE e.offer_type IS NOT NULL
    ORDER BY launch_date DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Group by date
    daily_promos = defaultdict(lambda: defaultdict(list))

    for launch_date, advertiser_id, offer_type, offer_details in results:
        if launch_date:
            daily_promos[launch_date][advertiser_id].append({
                'offer_type': offer_type,
                'offer_details': offer_details
            })

    # Find days with 3+ competitors launching promos
    insights = []
    for date, competitors in daily_promos.items():
        if len(competitors) >= 3:
            competitor_names = [get_competitor_name(aid) for aid in competitors.keys()]
            total_promos = sum(len(offers) for offers in competitors.values())

            insights.append({
                'date': date,
                'num_competitors': len(competitors),
                'competitors': competitor_names,
                'total_promos': total_promos
            })

    insights.sort(key=lambda x: x['num_competitors'], reverse=True)

    if insights:
        for insight in insights[:3]:  # Top 3 dates
            comp_list = ', '.join(insight['competitors'])
            print(f"\n✅ {insight['num_competitors']} competitors ({comp_list})")
            print(f"   launched {insight['total_promos']} promo campaigns on {format_date(insight['date'])}—signaling coordinated seasonal push.")
    else:
        print("\n⚠️  No coordinated promo activity detected yet.")

    db.close()
    return insights

# ============================================================================
# B. THREAT IDENTIFICATION
# ============================================================================

def detect_category_entry():
    """
    Find competitors entering new categories
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("B. THREAT IDENTIFICATION - New Category Entry")
    print("="*80)

    # Get first ad in each category per competitor
    query = """
    SELECT
        a.advertiser_id,
        e.product_category,
        MIN(a.first_seen_date) as first_entry,
        COUNT(*) as total_ads,
        e.primary_theme
    FROM ads a
    JOIN ad_enrichment e ON a.id = e.ad_id
    WHERE e.product_category IS NOT NULL
    GROUP BY a.advertiser_id, e.product_category
    ORDER BY first_entry DESC
    LIMIT 10
    """

    cursor.execute(query)
    results = cursor.fetchall()

    insights = []
    for advertiser_id, category, first_entry, total_ads, theme in results:
        insights.append({
            'competitor': get_competitor_name(advertiser_id),
            'category': category,
            'first_entry': first_entry,
            'total_ads': total_ads,
            'theme': theme
        })

    if insights:
        for insight in insights[:5]:
            print(f"\n⚠️  {insight['competitor']} entered '{insight['category']}' on {format_date(insight['first_entry'])}")
            print(f"   They've now launched {insight['total_ads']} campaigns with '{insight['theme']}' messaging.")
    else:
        print("\n⚠️  Not enough data to detect category entries.")

    db.close()
    return insights

def detect_launch_velocity():
    """
    Calculate campaign launch frequency trends
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("THREAT IDENTIFICATION - Launch Velocity Trends")
    print("="*80)

    # Get monthly launch counts
    query = """
    SELECT
        a.advertiser_id,
        strftime('%Y-%m', a.first_seen_date) as month,
        COUNT(*) as launches
    FROM ads a
    WHERE a.first_seen_date IS NOT NULL
    GROUP BY a.advertiser_id, month
    ORDER BY a.advertiser_id, month
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Calculate month-over-month changes
    competitor_data = defaultdict(list)
    for advertiser_id, month, launches in results:
        competitor_data[advertiser_id].append((month, launches))

    insights = []
    for advertiser_id, monthly_launches in competitor_data.items():
        if len(monthly_launches) >= 2:
            sorted_data = sorted(monthly_launches, key=lambda x: x[0])

            # Calculate average velocity change
            velocity_changes = []
            for i in range(1, len(sorted_data)):
                prev_month, prev_count = sorted_data[i-1]
                curr_month, curr_count = sorted_data[i]

                if prev_count > 0:
                    percent_change = ((curr_count - prev_count) / prev_count) * 100
                    velocity_changes.append(percent_change)

            if velocity_changes:
                avg_change = sum(velocity_changes) / len(velocity_changes)

                insights.append({
                    'competitor': get_competitor_name(advertiser_id),
                    'avg_velocity_change': avg_change,
                    'latest_month': sorted_data[-1][0],
                    'latest_count': sorted_data[-1][1],
                    'prev_count': sorted_data[-2][1] if len(sorted_data) >= 2 else 0
                })

    insights.sort(key=lambda x: x['avg_velocity_change'], reverse=True)

    if insights:
        for insight in insights[:3]:
            if insight['avg_velocity_change'] > 30:
                print(f"\n⚠️  {insight['competitor']}: Campaign launch frequency increased {int(insight['avg_velocity_change'])}% month-over-month")
                print(f"   Latest: {insight['latest_count']} campaigns in {insight['latest_month']}")
    else:
        print("\n⚠️  Not enough historical data to calculate velocity trends.")

    db.close()
    return insights

# ============================================================================
# C. QUANTIFIED PROOF POINTS
# ============================================================================

def get_category_gaps():
    """
    For Slide 3: Cost of Inaction - category coverage gaps
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("C. QUANTIFIED PROOF POINTS - Category Coverage Gaps")
    print("="*80)

    # Get all categories each competitor is active in
    query = """
    SELECT
        a.advertiser_id,
        e.product_category,
        COUNT(*) as ad_count
    FROM ads a
    JOIN ad_enrichment e ON a.id = e.ad_id
    WHERE e.product_category IS NOT NULL
    GROUP BY a.advertiser_id, e.product_category
    ORDER BY ad_count DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Build category coverage per competitor
    competitor_categories = defaultdict(list)
    all_categories = set()

    for advertiser_id, category, ad_count in results:
        competitor_categories[advertiser_id].append({
            'category': category,
            'ad_count': ad_count
        })
        all_categories.add(category)

    # Find gaps (categories others are in but you're not)
    print(f"\n📊 Total categories in market: {len(all_categories)}")

    for advertiser_id, categories in competitor_categories.items():
        competitor_name = get_competitor_name(advertiser_id)
        category_names = {c['category'] for c in categories}
        missing = all_categories - category_names

        if missing:
            print(f"\n{competitor_name}:")
            print(f"  - Active in {len(category_names)} categories")
            print(f"  - Missing from {len(missing)} categories: {', '.join(list(missing)[:3])}")

    db.close()
    return competitor_categories

def get_detection_lag():
    """
    For Slide 5: How It Works - detection lag example
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("QUANTIFIED PROOF POINTS - Detection Lag Analysis")
    print("="*80)

    # Get sample of recent competitor campaigns
    query = """
    SELECT
        a.advertiser_id,
        a.first_seen_date,
        e.product_category,
        e.offer_details,
        a.ad_text
    FROM ads a
    JOIN ad_enrichment e ON a.id = e.ad_id
    WHERE e.offer_details IS NOT NULL
    ORDER BY a.first_seen_date DESC
    LIMIT 5
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print("\n📊 Recent competitor campaigns you should have detected:")

    for advertiser_id, first_seen, category, offer, ad_text in results:
        competitor = get_competitor_name(advertiser_id)

        # Calculate lag (assume you're checking manually weekly = 7 days lag)
        try:
            launch_date = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
            manual_detect_date = launch_date + timedelta(days=7)

            print(f"\n✅ {competitor} - {category}")
            print(f"   Offer: {offer}")
            print(f"   Launched: {format_date(first_seen)}")
            print(f"   Manual detection (7d lag): {manual_detect_date.strftime('%b %d, %Y')}")
            print(f"   With AdIntel: Would detect within 24 hours ⚡")
        except:
            pass

    db.close()

def get_market_share():
    """
    For Slide 7: ROI Scenarios - market share and competitive pressure
    """
    db = get_db()
    cursor = db.cursor()

    print("\n" + "="*80)
    print("QUANTIFIED PROOF POINTS - Market Share & Competitive Pressure")
    print("="*80)

    # Get total ads per competitor
    query = """
    SELECT
        a.advertiser_id,
        COUNT(*) as total_ads,
        COUNT(CASE WHEN a.is_active = 1 THEN 1 END) as active_ads
    FROM ads a
    GROUP BY a.advertiser_id
    ORDER BY total_ads DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    total_market_ads = sum(r[1] for r in results)

    print(f"\n📊 Total ads tracked in market: {total_market_ads}")
    print(f"\n Market Share by Campaign Volume:")

    for advertiser_id, total_ads, active_ads in results:
        competitor = get_competitor_name(advertiser_id)
        market_share = (total_ads / total_market_ads * 100) if total_market_ads > 0 else 0

        print(f"\n  {competitor}:")
        print(f"    - Total campaigns: {total_ads}")
        print(f"    - Active campaigns: {active_ads}")
        print(f"    - Market share: {market_share:.1f}%")

    db.close()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("STRATEGIC INSIGHTS EXTRACTION FOR PITCH DECK")
    print("="*80)
    print("\nGenerating insights from ad intelligence database...")
    print(f"Database: data/adintel.db")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # A. Pattern Detection
    detect_category_surge()
    detect_coordinated_promos()

    # B. Threat Identification
    detect_category_entry()
    detect_launch_velocity()

    # C. Quantified Proof Points
    get_category_gaps()
    get_detection_lag()
    get_market_share()

    print("\n" + "="*80)
    print("INSIGHTS EXTRACTION COMPLETE")
    print("="*80)
    print("\nUse these insights in your pitch deck to demonstrate:")
    print("  ✅ Real competitive intelligence from your data")
    print("  ✅ Quantified market dynamics and gaps")
    print("  ✅ Proof of concept for detection and analysis")
    print("\n")
