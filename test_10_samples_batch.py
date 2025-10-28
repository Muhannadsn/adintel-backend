#!/usr/bin/env python3
"""
Test vision extraction on 10 random ad images - batch mode
"""

import sqlite3
import random
from api.ai_analyzer import AdIntelligence

def main():
    print("=" * 80)
    print("TESTING VISION EXTRACTION ON 10 RANDOM AD IMAGES")
    print("=" * 80)

    # Get 10 random ads with images
    conn = sqlite3.connect('data/adintel.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, image_url, ad_text
        FROM ads
        WHERE advertiser_id = 'AR14306592000630063105'
        AND image_url IS NOT NULL
        AND image_url != ''
        ORDER BY RANDOM()
        LIMIT 10
    ''')

    ads = cursor.fetchall()
    conn.close()

    if not ads:
        print("No ads with images found!")
        return

    print(f"\nFound {len(ads)} random ads to test\n")

    # Initialize analyzer
    analyzer = AdIntelligence()

    results = []

    # Process each ad
    for i, (ad_id, image_url, ad_text) in enumerate(ads, 1):
        print(f"\n🔄 Processing sample {i}/10...")

        try:
            # Extract text from image
            extracted_text = analyzer._extract_text_from_image(image_url)

            # Run full enrichment
            test_ad = {
                'ad_text': ad_text,
                'image_url': image_url,
                'advertiser_id': 'AR14306592000630063105',
                'regions': 'QA'
            }

            enriched = analyzer.categorize_ad(test_ad)

            results.append({
                'id': ad_id,
                'image_url': image_url,
                'original_text': ad_text,
                'extracted_text': extracted_text,
                'enriched': enriched
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'id': ad_id,
                'image_url': image_url,
                'error': str(e)
            })

    # Print all results
    print("\n\n" + "=" * 80)
    print("RESULTS - REVIEW EACH IMAGE MANUALLY")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{'=' * 80}")
        print(f"SAMPLE {i}/10 - Ad ID: {result['id']}")
        print(f"{'=' * 80}")

        print(f"\n🔗 VIEW IMAGE: {result['image_url']}")

        if 'error' in result:
            print(f"\n❌ ERROR: {result['error']}")
            continue

        print(f"\nOriginal DB Text: {result['original_text']}")

        print(f"\n{'-' * 80}")
        print("VISION EXTRACTION:")
        print(f"{'-' * 80}")
        # Show first 400 chars of extracted text
        extracted = result['extracted_text']
        if len(extracted) > 400:
            print(extracted[:400] + "...")
        else:
            print(extracted)

        print(f"\n{'-' * 80}")
        print("AI CATEGORIZATION:")
        print(f"{'-' * 80}")
        enriched = result['enriched']
        print(f"  📦 Category: {enriched.get('product_category')}")
        print(f"  🏷️  Name: {enriched.get('product_name')}")
        print(f"  💰 Offer: {enriched.get('offer_type')} - {enriched.get('offer_details')}")
        print(f"  🎯 Theme: {enriched.get('primary_theme')}")
        print(f"  👥 Audience: {enriched.get('audience_segment')}")
        print(f"  📊 Confidence: {enriched.get('confidence_score', 0):.2f}")

    print(f"\n\n{'=' * 80}")
    print("✅ ALL SAMPLES PROCESSED!")
    print(f"{'=' * 80}")
    print("\nNow manually review each image URL above and verify:")
    print("  1. Does the extracted restaurant/brand match?")
    print("  2. Is the food category correct?")
    print("  3. Did it capture the promotional offer?")
    print("  4. Is the product categorization accurate?")

if __name__ == "__main__":
    main()
