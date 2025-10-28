#!/usr/bin/env python3
"""
Test vision model text extraction on a sample ad image
"""

from api.ai_analyzer import AdIntelligence

def main():
    print("=" * 70)
    print("TESTING VISION MODEL TEXT EXTRACTION")
    print("=" * 70)

    # Initialize analyzer
    analyzer = AdIntelligence()

    # Sample image URL from database
    test_image_url = "https://tpc.googlesyndication.com/archive/simgad/10179032648912247055"

    print(f"\n📸 Testing image: {test_image_url}")
    print("\n🔍 Extracting text with Llava vision model...\n")

    try:
        # Extract text from image
        extracted_text = analyzer._extract_text_from_image(test_image_url)

        print("=" * 70)
        print("✅ EXTRACTED TEXT:")
        print("=" * 70)
        print(extracted_text)
        print("=" * 70)

        # Now test full enrichment with the extracted text
        print("\n🤖 Running full AI analysis with extracted text...\n")

        test_ad = {
            'ad_text': 'Unknown',  # Simulate missing text
            'image_url': test_image_url,
            'advertiser_id': 'AR14306592000630063105',
            'regions': 'QA'
        }

        enriched = analyzer.categorize_ad(test_ad)

        print("=" * 70)
        print("✅ ENRICHMENT RESULTS:")
        print("=" * 70)
        print(f"Product Category: {enriched.get('product_category')}")
        print(f"Product Name: {enriched.get('product_name')}")
        print(f"Primary Theme: {enriched.get('primary_theme')}")
        print(f"Messaging Themes: {enriched.get('messaging_themes')}")
        print(f"Audience: {enriched.get('audience_segment')}")
        print(f"Offer Type: {enriched.get('offer_type')}")
        print(f"Offer Details: {enriched.get('offer_details')}")
        print(f"Confidence: {enriched.get('confidence_score'):.2f}")
        if 'extracted_text' in enriched:
            print(f"\nExtracted Text: {enriched.get('extracted_text')}")
        print("=" * 70)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
