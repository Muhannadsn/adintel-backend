#!/usr/bin/env python3
"""
Test the CRITICAL FIXES: 50-char limit and 2-word minimum
"""
from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

def test_critical_fixes():
    print("="*70)
    print("TESTING CRITICAL FIXES FOR GARBAGE BRANDS")
    print("="*70)

    extractor = BrandExtractor()

    # Test 1: Single word "The" should be filtered
    test_text_1 = "The Restaurant Menu"
    print(f"\nTest 1: '{test_text_1}'")
    print("-"*70)
    print("Expected: 'The' should be FILTERED (single-word unknown)")

    context_1 = AdContext(unique_id="test_1", advertiser_id="test", raw_text=test_text_1)
    matches_1 = extractor.extract(context_1)

    print(f"Result: Extracted {len(matches_1)} brand(s)")
    for match in matches_1:
        print(f"  - {match.name} (source: {match.source})")

    if len(matches_1) == 0 or not any(m.name == "The" for m in matches_1):
        print("  ✅ PASS: 'The' correctly filtered!")
    else:
        print("  ❌ FAIL: 'The' was extracted!")

    # Test 2: Long marketing text should be filtered
    test_text_2 = "Shop from DE'LONGHI ONLINE WITH ONE HOUR DELIVERY SKIP THE DOORSTEP AND HAVE IT DELIVERED TO YOUR DOORSTEP"
    print(f"\nTest 2: Long marketing text (100+ chars)")
    print("-"*70)
    print("Expected: Long brand names should be FILTERED (>50 chars)")

    context_2 = AdContext(unique_id="test_2", advertiser_id="test", raw_text=test_text_2)
    matches_2 = extractor.extract(context_2)

    print(f"Result: Extracted {len(matches_2)} brand(s)")
    for match in matches_2:
        print(f"  - {match.name} (length: {len(match.name)}, source: {match.source})")

    # Check if any brand is over 50 chars
    long_brands = [m for m in matches_2 if len(m.name) > 50]
    if len(long_brands) == 0:
        print("  ✅ PASS: No brands over 50 characters!")
    else:
        print(f"  ❌ FAIL: Found {len(long_brands)} brands over 50 chars!")

    # Test 3: OCR error "ShoNoU" should be filtered (single word unknown)
    test_text_3 = "Order from ShoNoU today"
    print(f"\nTest 3: '{test_text_3}'")
    print("-"*70)
    print("Expected: 'ShoNoU' should be FILTERED (single-word unknown, OCR error)")

    context_3 = AdContext(unique_id="test_3", advertiser_id="test", raw_text=test_text_3)
    matches_3 = extractor.extract(context_3)

    print(f"Result: Extracted {len(matches_3)} brand(s)")
    for match in matches_3:
        print(f"  - {match.name} (source: {match.source})")

    if len(matches_3) == 0 or not any(m.name == "ShoNoU" for m in matches_3):
        print("  ✅ PASS: 'ShoNoU' correctly filtered!")
    else:
        print("  ❌ FAIL: 'ShoNoU' was extracted!")

    # Test 4: Known single-word brand "Apple" should STILL WORK
    test_text_4 = "Apple iPhone 15 Pro"
    print(f"\nTest 4: '{test_text_4}'")
    print("-"*70)
    print("Expected: 'Apple' should be EXTRACTED (known catalog brand)")

    context_4 = AdContext(unique_id="test_4", advertiser_id="test", raw_text=test_text_4)
    matches_4 = extractor.extract(context_4)

    print(f"Result: Extracted {len(matches_4)} brand(s)")
    for match in matches_4:
        print(f"  - {match.name} (source: {match.source})")

    if any(m.name == "Apple" for m in matches_4):
        print("  ✅ PASS: 'Apple' correctly extracted (catalog brand)!")
    else:
        print("  ❌ FAIL: 'Apple' was not extracted!")

    # Test 5: Multi-word unknown "Luxury Scent" should STILL WORK
    test_text_5 = "Shop from Luxury Scent - Fast Delivery"
    print(f"\nTest 5: '{test_text_5}'")
    print("-"*70)
    print("Expected: 'Luxury Scent' should be EXTRACTED (2+ words, semantic pattern)")

    context_5 = AdContext(unique_id="test_5", advertiser_id="test", raw_text=test_text_5)
    matches_5 = extractor.extract(context_5)

    print(f"Result: Extracted {len(matches_5)} brand(s)")
    for match in matches_5:
        print(f"  - {match.name} (source: {match.source})")

    if any(m.name == "Luxury Scent" for m in matches_5):
        print("  ✅ PASS: 'Luxury Scent' correctly extracted!")
    else:
        print("  ❌ FAIL: 'Luxury Scent' was not extracted!")

    print("\n" + "="*70)
    print("CRITICAL FIXES TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_critical_fixes()
