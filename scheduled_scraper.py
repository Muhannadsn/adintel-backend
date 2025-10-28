#!/usr/bin/env python3
"""
Scheduled Incremental Scraper
Runs daily to update competitor data efficiently

Strategy:
- Initial run: Scrape 400-1000 ads per competitor
- Daily runs: Only scrape recent 100 ads, detect new/removed ads
- Only enrich NEW ads with AI (saves time)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.api_scraper import GATCAPIScraper
from api.database import AdDatabase
from api.ai_analyzer import AdIntelligence


# Competitor URLs to track
COMPETITORS = [
    {
        'name': 'Talabat',
        'url': 'https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA',
        'advertiser_id': 'AR14306592000630063105',
        'region': 'QA'
    },
    # {
    #     'name': 'Deliveroo',
    #     'url': 'https://adstransparency.google.com/advertiser/AR13676304484790173697?region=QA',
    #     'advertiser_id': 'AR13676304484790173697',
    #     'region': 'QA'
    # },
    {
        'name': 'Rafiq',
        'url': 'https://adstransparency.google.com/advertiser/AR08778154730519003137?region=QA',
        'advertiser_id': 'AR08778154730519003137',
        'region': 'QA'
    },
    # Add more competitors here
]


def is_initial_run(advertiser_id):
    """Check if this is the first time scraping this competitor"""
    db = AdDatabase()
    ads = db.get_ads_by_competitor(advertiser_id, active_only=False)
    return len(ads) == 0


def incremental_scrape(advertiser_id, region, is_initial=False):
    """
    Smart scraping: full scrape on first run, incremental updates after

    Args:
        advertiser_id: Competitor's advertiser ID
        region: Region code
        is_initial: If True, scrape 1000 ads. If False, scrape 100 recent ads

    Returns:
        dict: Stats about the scrape
    """
    scraper = GATCAPIScraper()
    db = AdDatabase()

    # Determine scrape size
    max_ads = 1000 if is_initial else 100

    print(f"\n{'='*80}")
    print(f"{'INITIAL SCRAPE' if is_initial else 'INCREMENTAL UPDATE'}")
    print(f"{'='*80}")
    print(f"Advertiser: {advertiser_id}")
    print(f"Region: {region}")
    print(f"Max ads: {max_ads}")

    # Step 1: Scrape ads (fast - no enrichment yet)
    scraped_ads = scraper.scrape_advertiser(
        advertiser_id=advertiser_id,
        region=region,
        max_ads=max_ads,
        enrich=False,  # Don't enrich yet - we'll do it selectively
        save_to_db=False  # Don't save yet - we need to check for duplicates
    )

    print(f"\n✅ Scraped {len(scraped_ads)} ads")

    # Step 2: Check which ads are NEW vs existing
    existing_ads = db.get_ads_by_competitor(advertiser_id, active_only=False)

    # Create set of existing ad signatures (ad_text + image_url)
    existing_signatures = set()
    for ad in existing_ads:
        signature = f"{ad.get('ad_text', '')}||{ad.get('image_url', '')}"
        existing_signatures.add(signature)

    # Identify new ads
    new_ads = []
    for ad in scraped_ads:
        signature = f"{ad.get('ad_text', '')}||{ad.get('image_url', '')}"
        if signature not in existing_signatures:
            new_ads.append(ad)

    print(f"🆕 Found {len(new_ads)} new ads (out of {len(scraped_ads)} scraped)")

    # Step 3: Enrich ONLY new ads with AI (saves time!)
    enriched_new_ads = []
    if new_ads:
        print(f"\n{'='*80}")
        print(f"AI ENRICHMENT (NEW ADS ONLY)")
        print(f"{'='*80}")
        print(f"⏱️  Estimated time: ~{len(new_ads) * 2.5 / 60:.1f} minutes")

        analyzer = AdIntelligence()
        enriched_new_ads = analyzer.batch_analyze(new_ads)

        print(f"\n✅ Enriched {len(enriched_new_ads)} new ads")

    # Step 4: Save new ads to database
    stats = {'ads_new': 0, 'ads_updated': 0}
    if enriched_new_ads:
        stats = db.save_ads(enriched_new_ads, advertiser_id)

    # Step 5: Mark ads as inactive if they disappeared
    # Get all ad signatures from current scrape
    current_signatures = []
    for ad in scraped_ads:
        signature = f"{ad.get('ad_text', '')}||{ad.get('image_url', '')}"
        current_signatures.append(signature)

    # Mark ads not in current scrape as inactive
    ads_retired = db.mark_ads_inactive(advertiser_id, current_signatures)

    print(f"\n📊 SUMMARY:")
    print(f"   New ads: {stats['ads_new']}")
    print(f"   Updated ads: {stats['ads_updated']}")
    print(f"   Retired ads: {ads_retired}")

    return {
        'advertiser_id': advertiser_id,
        'scraped_total': len(scraped_ads),
        'new_ads': stats['ads_new'],
        'updated_ads': stats['ads_updated'],
        'retired_ads': ads_retired,
        'timestamp': datetime.now().isoformat()
    }


def run_scheduled_scrape():
    """
    Run scraper for all competitors
    Called by cron/scheduler daily at 7pm
    """
    log_file = Path(__file__).parent / 'data' / 'scrape_log.json'
    log_file.parent.mkdir(exist_ok=True)

    results = []

    print(f"\n{'='*80}")
    print(f"SCHEDULED SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    for competitor in COMPETITORS:
        print(f"\n🎯 Processing: {competitor['name']}")

        try:
            # Check if initial run
            is_initial = is_initial_run(competitor['advertiser_id'])

            # Run scrape
            result = incremental_scrape(
                advertiser_id=competitor['advertiser_id'],
                region=competitor['region'],
                is_initial=is_initial
            )

            result['competitor_name'] = competitor['name']
            results.append(result)

        except Exception as e:
            print(f"❌ Error scraping {competitor['name']}: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                'competitor_name': competitor['name'],
                'advertiser_id': competitor['advertiser_id'],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    # Save log
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 Summary:")
    for result in results:
        if 'error' in result:
            print(f"   {result['competitor_name']}: ❌ ERROR - {result['error']}")
        else:
            print(f"   {result['competitor_name']}: +{result['new_ads']} new, ~{result['updated_ads']} updated")

    print(f"\n📝 Log saved: {log_file}")

    return results


if __name__ == '__main__':
    run_scheduled_scrape()
