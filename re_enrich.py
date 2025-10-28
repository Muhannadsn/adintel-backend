#!/usr/bin/env python3
"""
Re-enrich existing ads with the new 11-agent orchestrator
"""

from api.database import AdDatabase
from api.orchestrated_analyzer import AdIntelligence  # Using orchestrator now!

def main():
    print("=" * 70)
    print("RE-ENRICHING ALL ADS WITH UPDATED CATEGORIES")
    print("=" * 70)

    # Initialize
    db = AdDatabase()
    analyzer = AdIntelligence()

    # Get ALL ads that need enrichment (ads without enrichment data)
    ads = db.get_all_ads(active_only=True)

    # Filter to only ads that don't have enrichment yet
    unenriched_ads = [ad for ad in ads if not ad.get('product_category')]

    print(f"\nFound {len(unenriched_ads)} ads to enrich")
    print(f"Using updated categories: {len(analyzer.product_categories)} categories")
    print()

    if len(unenriched_ads) == 0:
        print("✅ All ads are already enriched!")
        return

    # Re-analyze with new categories
    enriched_ads = analyzer.batch_analyze(unenriched_ads, batch_size=10)

    # Save back to database
    stats = db.save_ads(enriched_ads)

    print(f"\n{'=' * 70}")
    print("✅ RE-ENRICHMENT COMPLETE!")
    print(f"{'=' * 70}")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    main()
