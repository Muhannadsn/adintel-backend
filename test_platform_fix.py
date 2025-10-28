#!/usr/bin/env python3
"""
Test script to verify platform brand fix.

Tests that ads from platform advertisers (Talabat, Snoonu, etc.) now correctly
extract the MERCHANT brand (Papa John's, DeLonghi, etc.) instead of the platform brand.
"""

import sqlite3
from pathlib import Path
from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

def test_platform_brand_extraction():
    """Test that we now extract merchant brands, not platform brands."""

    # Connect to database
    db_path = Path(__file__).parent / "data" / "adintel.db"
    conn = sqlite3.connect(db_path)

    # Get 5 sample ads from different platform advertisers
    # Note: ads table has 'id', not 'ad_id'. Also no 'advertiser_name' in ads table.
    cursor = conn.execute("""
        SELECT
            a.id,
            a.advertiser_id,
            a.image_url,
            ae.brand as old_brand,
            ae.product_name as old_product_name,
            ae.product_category as old_category
        FROM ads a
        LEFT JOIN ad_enrichment ae ON a.id = ae.ad_id
        WHERE a.advertiser_id IN (
            'AR14306592000630063105',  -- Talabat
            'AR12079153035289296897',  -- Snoonu
            'AR08778154730519003137'   -- Rafiq
        )
        AND a.image_url IS NOT NULL
        LIMIT 5
    """)

    test_ads = cursor.fetchall()
    conn.close()

    if not test_ads:
        print("❌ No test ads found in database!")
        return

    print("=" * 80)
    print("🧪 TESTING PLATFORM BRAND FIX")
    print("=" * 80)
    print(f"\nTesting {len(test_ads)} ads from platform advertisers")
    print(f"Expected: Merchant brands (Papa John's, etc.) NOT platform brands (Talabat, Snoonu)\n")

    # Initialize orchestrator
    orchestrator = AdIntelligenceOrchestrator(
        expected_region="QA",
        ollama_host="http://localhost:11434",
        model="llama3.1:8b"
    )

    results = []

    # Map advertiser IDs to names
    advertiser_names = {
        'AR14306592000630063105': 'Talabat',
        'AR12079153035289296897': 'Snoonu',
        'AR08778154730519003137': 'Rafiq'
    }

    for i, (ad_id, advertiser_id, image_url, old_brand, old_product, old_category) in enumerate(test_ads, 1):
        advertiser_name = advertiser_names.get(advertiser_id, advertiser_id)
        print(f"\n{'='*80}")
        print(f"TEST {i}/5: {advertiser_name} ad")
        print(f"Ad ID: {ad_id}")
        print(f"OLD EXTRACTION → Brand: {old_brand}, Product: {old_product}, Category: {old_category}")
        print(f"{'='*80}\n")

        # Create context
        context = AdContext(
            unique_id=ad_id,
            advertiser_id=advertiser_id,
            region_hint="QA",
            raw_text="",  # Will be populated by vision extraction
            raw_image_url=image_url
        )

        # Enrich (this will now use fixed config)
        try:
            enriched = orchestrator.enrich(context)

            result = {
                'ad_id': ad_id,
                'advertiser': advertiser_name,
                'old_brand': old_brand,
                'new_brand': enriched.brand,
                'old_product': old_product,
                'new_product': enriched.product_type,
                'old_category': old_category,
                'new_category': enriched.flags.get('food_category'),
                'brand_confidence': enriched.brand_confidence,
                'web_validated': enriched.flags.get('web_validated', False)
            }

            results.append(result)

            print(f"\n✅ NEW EXTRACTION:")
            brand_conf_str = f"{enriched.brand_confidence:.2f}" if enriched.brand_confidence is not None else "N/A"
            print(f"   Brand: {enriched.brand or 'None'} (confidence: {brand_conf_str})")
            print(f"   Product Type: {enriched.product_type or 'None'}")
            print(f"   Food Category: {enriched.flags.get('food_category', 'N/A')}")
            print(f"   Web Validated: {enriched.flags.get('web_validated', False)}")

            # Check if fixed
            platform_brands = ['Talabat', 'Snoonu', 'Rafeeq', 'Rafiq', 'Keeta', 'Deliveroo']
            if enriched.brand in platform_brands:
                print(f"\n⚠️  WARNING: Still extracting platform brand '{enriched.brand}'!")
            else:
                print(f"\n✅ SUCCESS: Extracted merchant brand '{enriched.brand}' instead of platform!")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print(f"\n\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['advertiser']}:")
        print(f"   OLD: {result['old_brand']} → NEW: {result['new_brand'] or 'None'}")
        print(f"   Category: {result['old_category']} → {result['new_category'] or 'None'}")
        conf_str = f"{result['brand_confidence']:.2f}" if result['brand_confidence'] is not None else "N/A"
        print(f"   Confidence: {conf_str}")
        print(f"   Web Validated: {result['web_validated']}")
        print()

    # Count fixes
    platform_brands = ['Talabat', 'Snoonu', 'Rafeeq', 'Rafiq', 'Keeta', 'Deliveroo']
    fixed = sum(1 for r in results if r['new_brand'] not in platform_brands)
    still_broken = sum(1 for r in results if r['new_brand'] in platform_brands)

    print(f"✅ Fixed: {fixed}/{len(results)}")
    print(f"❌ Still broken: {still_broken}/{len(results)}")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    test_platform_brand_extraction()
