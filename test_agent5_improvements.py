#!/usr/bin/env python3
"""
Test Agent 5 Improvements: Fast Path, Conflict Resolution, Marketplace Handling
Based on Gemini's critique feedback
"""

from agents.context import AdContext, BrandMatch
from agents.product_type_classifier import ProductTypeClassifier


def test_fast_path_product():
    """Test fast path: Known product brand should skip LLM"""
    print("=" * 70)
    print("TEST 1: Fast Path - Known Product Brand (NutriBullet)")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_fp_product",
        advertiser_id="AR14306592000630063105",
        raw_text="Nutribullet 9-in-1 Smart Pot 2. Specifications: 6L capacity, 1000W power",
        brand_matches=[
            BrandMatch(
                name="NutriBullet",
                confidence=0.92,
                alias="nutribullet",
                source="catalog",
                entity_type="product"
            )
        ]
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")
    print(f"✅ Signals: {decision.signals}")

    assert decision.product_type == "physical_product", "Should classify as physical_product"
    assert decision.confidence >= 0.90, "Should have high confidence from fast path"
    assert "known_product_brand" in decision.signals, "Should indicate fast path was used"
    print("\n✅ PASSED: Fast path correctly classified product brand without LLM\n")


def test_fast_path_restaurant():
    """Test fast path: Known restaurant brand should skip LLM"""
    print("=" * 70)
    print("TEST 2: Fast Path - Known Restaurant Brand (McDonald's)")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_fp_restaurant",
        advertiser_id="AR14306592000630063105",
        raw_text="McDonald's Big Mac Meal 50% off! Get your favorite burger today.",
        brand_matches=[
            BrandMatch(
                name="McDonald's",
                confidence=0.95,
                alias="mcdonald's",
                source="catalog",
                entity_type="restaurant"
            )
        ]
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")
    print(f"✅ Signals: {decision.signals}")

    assert decision.product_type == "restaurant", "Should classify as restaurant"
    assert decision.confidence >= 0.90, "Should have high confidence from fast path"
    assert "known_restaurant_brand" in decision.signals, "Should indicate fast path was used"
    print("\n✅ PASSED: Fast path correctly classified restaurant brand without LLM\n")


def test_conflict_resolution():
    """Test conflict resolution: Platform advertising product"""
    print("=" * 70)
    print("TEST 3: Conflict Resolution - Talabat Advertising NutriBullet")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_conflict",
        advertiser_id="AR14306592000630063105",  # Talabat
        raw_text="Nutribullet 9-in-1 Smart Pot 2 now available on TalabatMart! 6L capacity, 1000W",
        brand_matches=[
            BrandMatch(
                name="NutriBullet",
                confidence=0.92,
                alias="nutribullet",
                source="catalog",
                entity_type="product"
            )
        ],
        platform_branding="Talabat"  # Set by subscription detector
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")
    print(f"✅ Signals: {decision.signals}")

    # Should still classify as physical_product via fast path
    assert decision.product_type == "physical_product", "Should classify as physical_product despite platform"
    assert decision.confidence >= 0.90, "Should have high confidence"
    print("\n✅ PASSED: Conflict resolution handled platform advertising product\n")


def test_marketplace_category_promotion():
    """Test marketplace with category language → category_promotion"""
    print("=" * 70)
    print("TEST 4: Marketplace - Category Promotion (Lulu Offers)")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_marketplace_cat",
        advertiser_id="AR14306592000630063105",
        raw_text="Lulu Hypermarket - Amazing deals on fresh groceries, electronics, and more! Shop now.",
        brand_matches=[
            BrandMatch(
                name="Lulu Hypermarket",
                confidence=0.88,
                alias="lulu",
                source="catalog",
                entity_type="grocery"
            )
        ]
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")
    print(f"✅ Signals: {decision.signals}")

    assert decision.product_type == "category_promotion", "Should classify as category_promotion"
    assert "marketplace_brand" in decision.signals, "Should indicate marketplace fast path"
    print("\n✅ PASSED: Marketplace with 'deals' classified as category_promotion\n")


def test_marketplace_specific_product():
    """Test marketplace with specific product → physical_product"""
    print("=" * 70)
    print("TEST 5: Marketplace - Specific Product (Al Meera Fresh Milk)")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_marketplace_prod",
        advertiser_id="AR14306592000630063105",
        raw_text="Al Meera - Fresh organic milk 2L now available. QAR 12 only.",
        brand_matches=[
            BrandMatch(
                name="Al Meera",
                confidence=0.85,
                alias="al meera",
                source="catalog",
                entity_type="grocery"
            )
        ]
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")
    print(f"✅ Signals: {decision.signals}")

    assert decision.product_type == "physical_product", "Should classify as physical_product"
    assert "marketplace_brand" in decision.signals, "Should indicate marketplace fast path"
    print("\n✅ PASSED: Marketplace with specific product classified as physical_product\n")


def test_low_confidence_fallback_to_llm():
    """Test that low confidence brands still use LLM"""
    print("=" * 70)
    print("TEST 6: Low Confidence - Should Use LLM (Unknown Brand)")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    context = AdContext(
        unique_id="test_low_conf",
        advertiser_id="AR14306592000630063105",
        raw_text="Get 50% off at our new burger restaurant! Best burgers in town.",
        brand_matches=[
            BrandMatch(
                name="Unknown Burger Place",
                confidence=0.65,  # Below 0.85 threshold
                alias="unknown",
                source="catalog_fuzzy",
                entity_type="restaurant"
            )
        ]
    )

    decision = classifier.classify(context)

    print(f"✅ Product Type: {decision.product_type}")
    print(f"✅ Confidence: {decision.confidence:.2f}")
    print(f"✅ Reasoning: {decision.reasoning}")

    # Should use LLM because confidence < 0.85
    assert decision.product_type == "restaurant", "Should classify as restaurant via LLM"
    assert "known_restaurant_brand" not in decision.signals, "Should NOT use fast path"
    print("\n✅ PASSED: Low confidence brand correctly fell back to LLM\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AGENT 5 IMPROVEMENTS TEST SUITE")
    print("Based on Gemini's Critique Feedback")
    print("=" * 70 + "\n")

    try:
        test_fast_path_product()
        test_fast_path_restaurant()
        test_conflict_resolution()
        test_marketplace_category_promotion()
        test_marketplace_specific_product()
        test_low_confidence_fallback_to_llm()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Fast Path: Working")
        print("✅ Conflict Resolution: Working")
        print("✅ Marketplace Handling: Working")
        print("\nAgent 5 is now production-ready with Gemini's improvements! 🚀\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
