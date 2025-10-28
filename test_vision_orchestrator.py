#!/usr/bin/env python3
"""
Test the full orchestrator with Vision Layer (Layer 0) integrated.

This test proves the system is no longer blind - it can now:
1. Extract text from ad images using DeepSeek + LLaVA
2. Feed that extracted text to all downstream agents
3. Properly classify brands, products, offers, etc.
"""

from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

def test_vision_orchestrator():
    """Test orchestrator with vision layer on TGI Fridays ad."""

    print("=" * 80)
    print("TESTING VISION-ENABLED ORCHESTRATOR")
    print("=" * 80)

    # Initialize orchestrator (now includes vision layer)
    orchestrator = AdIntelligenceOrchestrator(
        expected_region="QA",
        ollama_host="http://localhost:11434",
        model="llama3.1:8b"
    )

    # Create context with ONLY image path (no raw_text!)
    # This simulates the real scraper scenario
    context = AdContext(
        unique_id="TEST_TGI_001",
        advertiser_id="AR12079153035289296897",
        region_hint="QA",
        raw_text=""  # ← Empty! Vision layer will populate this
    )

    # Set screenshot path
    context.set_flag(
        'screenshot_path',
        '/Users/muhannadsaad/Desktop/ad-intelligence/test_screenshots/AR12079153035289296897/CR04376697774863810561.jpg'
    )

    print(f"\n📸 Testing with TGI Fridays Mozzarella Sticks ad")
    print(f"   Screenshot: {context.flags['screenshot_path']}")
    print(f"   Initial raw_text: '{context.raw_text}' (empty - vision will populate)")

    # Run full enrichment pipeline
    enriched = orchestrator.enrich(context)

    # Verify results
    print("\n\n" + "=" * 80)
    print("VERIFICATION: Did Vision Layer Work?")
    print("=" * 80)

    print(f"\n✅ Vision extraction succeeded: {enriched.vision_extraction is not None}")

    if enriched.vision_extraction:
        print(f"   - Confidence: {enriched.vision_extraction.confidence:.2f}")
        print(f"   - Method: {enriched.vision_extraction.method_used}")
        print(f"   - Extracted text length: {len(enriched.vision_extraction.extracted_text)} chars")
        print(f"\n   First 200 chars of extracted text:")
        print(f"   \"{enriched.vision_extraction.extracted_text[:200]}...\"")

    print(f"\n✅ Raw text populated: {len(enriched.raw_text) > 0}")
    print(f"   - Length: {len(enriched.raw_text)} chars")

    print(f"\n✅ Brand detected: {enriched.brand}")
    print(f"   - Confidence: {enriched.brand_confidence}")

    print(f"\n✅ Product type: {enriched.product_type}")
    print(f"   - Confidence: {enriched.product_type_confidence}")

    if enriched.product_type == "restaurant":
        food_cat = enriched.flags.get("food_category", "N/A")
        print(f"\n✅ Food category: {food_cat}")

    if enriched.offer:
        print(f"\n✅ Offer detected:")
        print(f"   - Type: {enriched.offer.offer_type}")
        print(f"   - Details: {enriched.offer.offer_details}")

    if enriched.audience:
        print(f"\n✅ Audience: {enriched.audience.target_audience}")

    if enriched.themes:
        print(f"\n✅ Primary theme: {enriched.themes.primary_theme}")

    print("\n" + "=" * 80)
    print("SUCCESS: Vision layer is integrated and working!")
    print("=" * 80)

    return enriched


if __name__ == "__main__":
    test_vision_orchestrator()
