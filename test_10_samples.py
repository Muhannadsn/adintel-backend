#!/usr/bin/env python3
"""
Test vision extraction on 10 random ad images
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

    # Process each ad
    for i, (ad_id, image_url, ad_text) in enumerate(ads, 1):
        print("=" * 80)
        print(f"SAMPLE {i}/10 - Ad ID: {ad_id}")
        print("=" * 80)
        print(f"\n📸 IMAGE URL: {image_url}")
        print(f"\n🔗 VIEW IMAGE: {image_url}")
        print(f"\nOriginal ad_text in DB: {ad_text}")

        print("\n🔍 Extracting text with vision model...")

        try:
            # Extract text from image
            extracted_text = analyzer._extract_text_from_image(image_url)

            print("\n" + "-" * 80)
            print("VISION EXTRACTION RESULT:")
            print("-" * 80)
            print(extracted_text)
            print("-" * 80)

            # Now run full enrichment
            print("\n🤖 Running AI categorization...")

            test_ad = {
                'ad_text': ad_text,
                'image_url': image_url,
                'advertiser_id': 'AR14306592000630063105',
                'regions': 'QA'
            }

            enriched = analyzer.categorize_ad(test_ad)

            print("\n" + "-" * 80)
            print("AI CATEGORIZATION RESULT:")
            print("-" * 80)
            print(f"  📦 Product Category: {enriched.get('product_category')}")
            print(f"  🏷️  Product Name: {enriched.get('product_name')}")
            print(f"  🎯 Primary Theme: {enriched.get('primary_theme')}")
            print(f"  💰 Offer Type: {enriched.get('offer_type')}")
            print(f"  🎁 Offer Details: {enriched.get('offer_details')}")
            print(f"  👥 Audience: {enriched.get('audience_segment')}")
            print(f"  📊 Confidence: {enriched.get('confidence_score', 0):.2f}")
            print("-" * 80)

            print("\n⏸️  VERIFY THIS IMAGE MANUALLY:")
            print(f"   1. Open: {image_url}")
            print(f"   2. Check if the extracted info matches what you see")
            print(f"   3. Press Enter to continue to next sample...")
            input()

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("\nPress Enter to continue to next sample...")
            input()

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
