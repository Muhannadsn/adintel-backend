#!/usr/bin/env python3
"""
Process manually scraped and converted CSV files through enrichment pipeline
"""

import csv
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.database import AdDatabase
from api.orchestrated_analyzer import AdIntelligence
from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

def download_screenshots(ads, advertiser_id):
    """Download screenshots for ads with image URLs"""
    screenshots_dir = Path("screenshots") / advertiser_id
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for ad in ads:
        creative_id = ad.get('creative_id')
        image_url = ad.get('image_url')

        if not image_url or not creative_id:
            continue

        try:
            screenshot_path = screenshots_dir / f"{creative_id}.jpg"

            # Skip if already exists
            if screenshot_path.exists():
                print(f"   ⏭️  Screenshot exists: {creative_id}")
                continue

            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            screenshot_path.write_bytes(response.content)
            downloaded += 1
            if downloaded <= 5:  # Only log first 5
                print(f"   📸 Downloaded: {creative_id}")
        except Exception as e:
            print(f"   ⚠️  Failed to download {creative_id}: {e}")

    return downloaded

def main():
    print("=" * 70)
    print("PROCESSING MANUALLY SCRAPED CSV FILES")
    print("=" * 70)

    # Initialize
    db = AdDatabase()

    # Find converted CSV files
    input_dir = Path('/Users/muhannadsaad/Desktop/ad-intelligence/data/input')
    converted_files = list(input_dir.glob('*_converted_*.csv'))

    if not converted_files:
        print("\n❌ No converted CSV files found!")
        print(f"   Looking in: {input_dir}")
        print(f"   Pattern: *_converted_*.csv")
        return

    print(f"\nFound {len(converted_files)} converted CSV files:\n")
    for f in converted_files:
        print(f"   📄 {f.name}")

    print()

    # Process each file
    total_processed = 0
    total_with_images = 0

    for csv_file in converted_files:
        print(f"\n{'=' * 70}")
        print(f"Processing: {csv_file.name}")
        print(f"{'=' * 70}\n")

        ads = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                ads.append(row)

        print(f"Loaded {len(ads)} ads from CSV")

        # Download screenshots for ads with image URLs
        ads_with_images = [ad for ad in ads if ad.get('image_url')]
        print(f"   {len(ads_with_images)} ads have image URLs")

        advertiser_id = ads[0].get('advertiser_id') if ads else 'unknown'

        if ads_with_images:
            print(f"\n📸 Downloading screenshots...")
            downloaded = download_screenshots(ads_with_images, advertiser_id)
            print(f"   Downloaded {downloaded} new screenshots")
            total_with_images += len(ads_with_images)

        # Run enrichment using orchestrator (same as api_scraper.py)
        print(f"\n🤖 Running vision + text enrichment...")

        region = 'QA'  # Default region
        orchestrator = AdIntelligenceOrchestrator(
            expected_region=region,
            ollama_host="http://localhost:11434",
            model="llama3.1:8b"
        )

        enriched_ads = []
        screenshots_dir = Path("screenshots") / advertiser_id

        for idx, ad in enumerate(ads):
            print(f"\n[{idx+1}/{len(ads)}] Processing {ad.get('creative_id', 'unknown')}...")

            # Check for screenshot
            screenshot_path = None
            creative_id = ad.get('creative_id')

            if creative_id:
                test_path = screenshots_dir / f"{creative_id}.jpg"
                if test_path.exists():
                    screenshot_path = test_path

            # Create context with text from CSV
            # Use ad_text field for text-only ads, or empty string if not available
            ad_text = ad.get('ad_text', '') or ''
            html_content = ad.get('html_content', '') or ''

            # Combine both text sources
            raw_text = f"{ad_text}\n{html_content}".strip()

            context = AdContext(
                unique_id=ad.get('creative_id', f'ad_{idx}'),
                advertiser_id=ad.get('advertiser_id'),
                region_hint=region,
                raw_text=raw_text
            )

            # Log text content for debugging
            if raw_text and not screenshot_path:
                print(f"   📝 Using text content ({len(raw_text)} chars)")

            # Set screenshot path for vision layer
            if screenshot_path:
                context.set_flag('screenshot_path', str(screenshot_path))
                print(f"   📸 Using screenshot: {screenshot_path.name}")

            # Run full orchestrator pipeline (with vision!)
            enriched_context = orchestrator.enrich(context)

            # Log extraction results
            print(f"   ✅ Brand: {enriched_context.brand or 'None'}")
            print(f"   ✅ Product Type: {enriched_context.product_type or 'None'}")
            if enriched_context.brand_confidence:
                print(f"   📊 Brand Confidence: {enriched_context.brand_confidence:.2f}")
            if enriched_context.product_type_confidence:
                print(f"   📊 Product Type Confidence: {enriched_context.product_type_confidence:.2f}")

            # Convert context back to dict for storage (DATABASE COMPATIBLE)
            enriched_ad = ad.copy()
            enriched_ad.update({
                # Vision-extracted fields
                'brand': enriched_context.brand,
                'brand_confidence': enriched_context.brand_confidence,
                'food_category': enriched_context.flags.get('food_category'),
                'detected_region': enriched_context.region_validation.detected_region if enriched_context.region_validation else None,
                'rejected_wrong_region': enriched_context.flags.get('rejected_wrong_region', False),

                # Core classification
                'product_type': enriched_context.product_type,
                'product_category': enriched_context.product_type,
                'product_name': enriched_context.brand,
                'product_type_confidence': enriched_context.product_type_confidence,

                # Enrichment fields
                'offer_type': enriched_context.offer.offer_type if enriched_context.offer else 'none',
                'offer_details': enriched_context.offer.offer_details if enriched_context.offer else None,
                'audience_segment': enriched_context.audience.target_audience if enriched_context.audience else None,
                'target_audience': enriched_context.audience.target_audience if enriched_context.audience else None,
                'primary_theme': enriched_context.themes.primary_theme if enriched_context.themes else None,
                'messaging_themes': enriched_context.themes.messaging_themes if enriched_context.themes else {},

                # Metadata
                'confidence_score': enriched_context.product_type_confidence,
                'analysis_model': 'orchestrator',
                'vision_confidence': enriched_context.vision_extraction.confidence if enriched_context.vision_extraction else None,
                'extracted_text': enriched_context.raw_text[:500] if enriched_context.raw_text else None,
            })

            enriched_ads.append(enriched_ad)

        # Save to database
        print(f"\n💾 Saving to database...")
        stats = db.save_ads(enriched_ads)
        print(f"   Stats: {stats}")

        total_processed += len(ads)

        print(f"\n✅ Completed {csv_file.name}")

    print(f"\n{'=' * 70}")
    print("✅ ALL CSV FILES PROCESSED!")
    print(f"{'=' * 70}")
    print(f"Total ads processed: {total_processed}")
    print(f"Total ads with images: {total_with_images}")

if __name__ == "__main__":
    main()
