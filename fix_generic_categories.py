#!/usr/bin/env python3
"""
Fix ads with generic "Other" and "General" categories
Re-analyze them with the improved prompts
"""

from api.database import AdDatabase
from api.ai_analyzer import AdIntelligence

def main():
    print("=" * 70)
    print("FIXING GENERIC CATEGORIES (Other, General)")
    print("=" * 70)

    db = AdDatabase()
    analyzer = AdIntelligence()

    # Get all ads with generic categories
    all_ads = db.get_all_ads(active_only=True)

    # Filter ads with "Other" or "General" categories
    generic_ads = [
        ad for ad in all_ads
        if ad.get('product_category') in ['Other', 'General', 'Unknown', None]
    ]

    print(f"\nFound {len(generic_ads)} ads with generic categories")
    print(f"Total ads in database: {len(all_ads)}")
    print()

    if not generic_ads:
        print("✅ No generic ads found! Database is clean.")
        return

    # Re-analyze with new prompts
    print("🔄 Re-analyzing with improved AI prompts...")
    enriched_ads = analyzer.batch_analyze(generic_ads, batch_size=5)

    # Save back to database
    stats = {'ads_new': 0, 'ads_updated': 0, 'ads_total': 0}
    for ad in enriched_ads:
        advertiser_id = ad.get('advertiser_id')
        if advertiser_id:
            result = db.save_ads([ad], advertiser_id)
            stats['ads_updated'] += result.get('ads_updated', 0)
            stats['ads_new'] += result.get('ads_new', 0)
            stats['ads_total'] += 1

    print(f"\n{'=' * 70}")
    print("✅ GENERIC CATEGORY FIX COMPLETE!")
    print(f"{'=' * 70}")
    print(f"Stats: {stats}")
    print()

    # Show updated category distribution
    print("📊 Updated Category Distribution:")
    from collections import Counter
    all_ads_updated = db.get_all_ads(active_only=True)
    categories = [ad.get('product_category', 'Unknown') for ad in all_ads_updated]
    category_counts = Counter(categories)

    for category, count in category_counts.most_common():
        print(f"  {category}: {count} ads")

if __name__ == "__main__":
    main()
