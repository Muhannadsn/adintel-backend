#!/usr/bin/env python3
"""
Test Scraper - Scrape 5 ads per merchant through orchestrator
Downloads screenshots to test_screenshots/ folder
"""
import sys
import os
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.api_scraper import GATCAPIScraper, parse_advertiser_url
from api.orchestrated_analyzer import AdIntelligence
from api.database import AdDatabase

# Test merchants (your main competitors)
TEST_MERCHANTS = [
    "https://adstransparency.google.com/advertiser/AR12079153035289296897?region=QA",  # Snoonu
    "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",  # Talabat
    "https://adstransparency.google.com/advertiser/AR02245493152427278337?region=QA",  # Deliveroo
]

SCREENSHOTS_DIR = Path(__file__).parent / "test_screenshots"


def download_screenshot(image_url: str, ad_id: str, advertiser_id: str) -> str:
    """
    Download ad screenshot to test_screenshots/

    Args:
        image_url: URL of the ad image
        ad_id: Unique ad identifier
        advertiser_id: Advertiser ID

    Returns:
        Local file path to saved screenshot
    """
    try:
        # Create advertiser subfolder
        advertiser_dir = SCREENSHOTS_DIR / advertiser_id
        advertiser_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{ad_id}.jpg"
        filepath = advertiser_dir / filename

        # Download image
        print(f"   📸 Downloading screenshot: {filename}")
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"   ✅ Saved to: {filepath}")
        return str(filepath)

    except Exception as e:
        print(f"   ⚠️  Failed to download screenshot: {e}")
        return ""


def test_scrape_and_orchestrate():
    """
    Main test function:
    1. Scrape 5 ads per merchant
    2. Download screenshots to test_screenshots/
    3. Run through orchestrator
    4. Save to database
    """
    print("=" * 80)
    print("TEST SCRAPER - ORCHESTRATOR INTEGRATION")
    print("=" * 80)
    print(f"\n📁 Screenshots will be saved to: {SCREENSHOTS_DIR}\n")

    # Initialize
    scraper = GATCAPIScraper()
    analyzer = AdIntelligence()
    db = AdDatabase()

    all_enriched_ads = []

    # Process each merchant
    for merchant_url in TEST_MERCHANTS:
        print("\n" + "=" * 80)
        print(f"🏪 Processing merchant: {merchant_url}")
        print("=" * 80)

        # Parse URL
        advertiser_id, region = parse_advertiser_url(merchant_url)

        if not advertiser_id:
            print("❌ Failed to parse URL, skipping...")
            continue

        print(f"   Advertiser ID: {advertiser_id}")
        print(f"   Region: {region}")
        print(f"   Max ads: 5")

        # Scrape 5 ads (no enrichment yet)
        print(f"\n📡 STEP 1: Scraping ads from API...")
        ads = scraper.scrape_advertiser(
            advertiser_id=advertiser_id,
            region=region,
            max_ads=5,
            enrich=False,
            save_to_db=False
        )

        if not ads:
            print("⚠️  No ads found, skipping merchant...")
            continue

        print(f"\n✅ Scraped {len(ads)} ads")

        # Download screenshots
        print(f"\n📸 STEP 2: Downloading screenshots...")
        for i, ad in enumerate(ads, 1):
            image_url = ad.get('image_url')
            creative_id = ad.get('creative_id', f'ad_{i}')

            if image_url:
                print(f"\n   Ad {i}/{len(ads)}:")
                print(f"   🖼️  URL: {image_url}")

                # Download screenshot
                local_path = download_screenshot(image_url, creative_id, advertiser_id)
                ad['screenshot_path'] = local_path
            else:
                print(f"   ⚠️  Ad {i} has no image URL")

        # Run through orchestrator
        print(f"\n🤖 STEP 3: Running through 11-agent orchestrator...")
        print(f"   (This will take ~{len(ads) * 3} seconds)")

        enriched_ads = []
        for i, ad in enumerate(ads, 1):
            print(f"\n   Processing ad {i}/{len(ads)}...")

            try:
                # Run orchestrator
                enriched = analyzer.categorize_ad(ad)
                enriched_ads.append(enriched)

                # Show quick summary
                print(f"   ✅ Brand: {enriched.get('brand', 'N/A')}")
                print(f"   ✅ Category: {enriched.get('product_category', 'N/A')}")
                print(f"   ✅ Offer: {enriched.get('offer_type', 'N/A')}")
                print(f"   ✅ Audience: {enriched.get('audience_segment', 'N/A')}")

                if enriched.get('rejected_wrong_region'):
                    print(f"   ❌ REJECTED: Wrong region detected!")

            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                enriched_ads.append(ad)  # Add unenriched version

        # Save to database
        print(f"\n💾 STEP 4: Saving to database...")
        stats = db.save_ads(enriched_ads, advertiser_id)
        print(f"   ✅ {stats}")

        all_enriched_ads.extend(enriched_ads)

    # Final summary
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)
    print(f"\n📊 SUMMARY:")
    print(f"   Total ads processed: {len(all_enriched_ads)}")
    print(f"   Screenshots saved to: {SCREENSHOTS_DIR}")

    # Count rejections
    rejected = sum(1 for ad in all_enriched_ads if ad.get('rejected_wrong_region'))
    print(f"   ✅ Valid ads: {len(all_enriched_ads) - rejected}")
    print(f"   ❌ Rejected (wrong region): {rejected}")

    # Show database stats
    db_stats = db.get_stats()
    print(f"\n📈 DATABASE STATS:")
    for key, value in db_stats.items():
        print(f"   {key}: {value}")

    print(f"\n🎯 Next steps:")
    print(f"   1. Check screenshots in: {SCREENSHOTS_DIR}")
    print(f"   2. View enriched data in database: data/adintel.db")
    print(f"   3. Start backend API: python3 api/main.py")
    print(f"   4. View in frontend: http://localhost:3000")

    return all_enriched_ads


if __name__ == "__main__":
    test_scrape_and_orchestrate()
