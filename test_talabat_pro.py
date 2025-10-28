#!/usr/bin/env python3
"""
Test Talabat Pro subscription service detection
"""

from api.ai_analyzer import AdIntelligence

def main():
    print("=" * 80)
    print("TESTING TALABAT PRO DETECTION")
    print("=" * 80)

    analyzer = AdIntelligence()

    # Test with a known Talabat Pro ad (sample 6 from earlier)
    talabat_pro_url = "https://tpc.googlesyndication.com/archive/simgad/4877814780854923256"

    print(f"\n📸 Testing image: {talabat_pro_url}")
    print("\n🔍 Extracting text with vision model...\n")

    try:
        # Extract text
        extracted_text = analyzer._extract_text_from_image(talabat_pro_url)

        print("=" * 80)
        print("VISION EXTRACTION:")
        print("=" * 80)
        print(extracted_text)
        print("=" * 80)

        # Run enrichment
        test_ad = {
            'ad_text': 'Unknown',
            'image_url': talabat_pro_url,
            'advertiser_id': 'AR14306592000630063105',
            'regions': 'QA'
        }

        enriched = analyzer.categorize_ad(test_ad)

        print("\n" + "=" * 80)
        print("AI CATEGORIZATION:")
        print("=" * 80)
        print(f"  📦 Product Category: {enriched.get('product_category')}")
        print(f"  🏷️  Product Name: {enriched.get('product_name')}")
        print(f"  💰 Offer Type: {enriched.get('offer_type')}")
        print(f"  🎁 Offer Details: {enriched.get('offer_details')}")
        print(f"  🎯 Primary Theme: {enriched.get('primary_theme')}")
        print(f"  👥 Audience: {enriched.get('audience_segment')}")
        print(f"  📊 Confidence: {enriched.get('confidence_score', 0):.2f}")
        print("=" * 80)

        if enriched.get('product_category') == 'Platform Subscription Service':
            print("\n✅ SUCCESS! Correctly detected as Platform Subscription Service")
        else:
            print(f"\n❌ FAILED! Expected 'Platform Subscription Service', got '{enriched.get('product_category')}'")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
