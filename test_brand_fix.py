#!/usr/bin/env python3
"""
Test the fixed brand extractor with semantic parsing
"""
from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

def test_luxury_scent():
    """Test the Luxury Scent case from the Snoonu ad"""
    print("="*70)
    print("TESTING BRAND EXTRACTOR FIX")
    print("="*70)

    # Initialize extractor
    extractor = BrandExtractor()

    # Test case 1: Luxury Scent (from ChatGPT's analysis)
    test_text_1 = "Shop Online from Luxury Scent - Fast Delivery in Qatar | Snoonu"
    print(f"\nTest 1: {test_text_1}")
    print("-"*70)

    context_1 = AdContext(unique_id="test_1", advertiser_id="test", raw_text=test_text_1)
    matches_1 = extractor.extract(context_1)

    print(f"Extracted {len(matches_1)} brand(s):")
    for match in matches_1:
        print(f"  - {match.name} (confidence: {match.confidence:.3f}, source: {match.source}, type: {match.entity_type})")

    # Test case 2: Generic terms that should be filtered
    test_text_2 = "Restaurants Qatar Pizza Menu Coffee Machine"
    print(f"\nTest 2: {test_text_2}")
    print("-"*70)

    context_2 = AdContext(unique_id="test_2", advertiser_id="test", raw_text=test_text_2)
    matches_2 = extractor.extract(context_2)

    print(f"Extracted {len(matches_2)} brand(s):")
    if matches_2:
        for match in matches_2:
            print(f"  - {match.name} (confidence: {match.confidence:.3f}, source: {match.source})")
    else:
        print("  ✅ Correctly filtered out all generic terms!")

    # Test case 3: Known brand (McDonald's)
    test_text_3 = "Order from McDonald's on Talabat"
    print(f"\nTest 3: {test_text_3}")
    print("-"*70)

    context_3 = AdContext(unique_id="test_3", advertiser_id="test", raw_text=test_text_3)
    matches_3 = extractor.extract(context_3)

    print(f"Extracted {len(matches_3)} brand(s):")
    for match in matches_3:
        print(f"  - {match.name} (confidence: {match.confidence:.3f}, source: {match.source}, type: {match.entity_type})")

    # Test case 4: Platform should be filtered
    test_text_4 = "Shop from Snoonu"
    print(f"\nTest 4: {test_text_4}")
    print("-"*70)

    context_4 = AdContext(unique_id="test_4", advertiser_id="test", raw_text=test_text_4)
    matches_4 = extractor.extract(context_4)

    print(f"Extracted {len(matches_4)} brand(s):")
    if matches_4:
        for match in matches_4:
            print(f"  - {match.name} (confidence: {match.confidence:.3f}, source: {match.source})")
    else:
        print("  ✅ Correctly filtered out platform brand!")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_luxury_scent()
