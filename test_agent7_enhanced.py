#!/usr/bin/env python3
"""Test Agent 7 Enhanced: Smart category detection (Mexican, Acai, etc.)"""

from agents.context import AdContext
from agents.food_category_classifier import FoodCategoryClassifier


def test_smart_categories():
    """Test the enhanced smart category detection"""
    print("=" * 70)
    print("AGENT 7 ENHANCED - SMART CATEGORY DETECTION")
    print("=" * 70)

    classifier = FoodCategoryClassifier()

    # Test 1: Mexican (Taco)
    context1 = AdContext(
        unique_id="test1",
        advertiser_id="AR123",
        raw_text="Get 2 tacos for QAR 15! Fresh guacamole and salsa included.",
        product_type="restaurant"
    )

    print("\n--- Test 1: Mexican Keywords (Tacos + Guacamole) ---")
    decision1 = classifier.classify(context1)
    print(f"✅ Category: {decision1.food_category}")
    print(f"✅ Confidence: {decision1.confidence:.2f}")
    print(f"✅ Signals: {decision1.signals}")
    assert "Mexican" in decision1.food_category, "Should detect Mexican"

    # Test 2: Acai Bowl (Healthy)
    context2 = AdContext(
        unique_id="test2",
        advertiser_id="AR123",
        raw_text="Fresh acai bowl with superfood toppings! Organic and healthy.",
        product_type="restaurant"
    )

    print("\n--- Test 2: Acai Bowl (Healthy/Organic) ---")
    decision2 = classifier.classify(context2)
    print(f"✅ Category: {decision2.food_category}")
    print(f"✅ Confidence: {decision2.confidence:.2f}")
    print(f"✅ Signals: {decision2.signals}")
    assert "Healthy" in decision2.food_category, "Should detect Healthy (acai)"

    # Test 3: Smoothie Bowl (Healthy)
    context3 = AdContext(
        unique_id="test3",
        advertiser_id="AR123",
        raw_text="Delicious smoothie bowl with fresh kale and quinoa!",
        product_type="restaurant"
    )

    print("\n--- Test 3: Smoothie Bowl with Kale + Quinoa ---")
    decision3 = classifier.classify(context3)
    print(f"✅ Category: {decision3.food_category}")
    print(f"✅ Confidence: {decision3.confidence:.2f}")
    print(f"✅ Signals: {decision3.signals}")
    assert "Healthy" in decision3.food_category, "Should detect Healthy (smoothie/kale/quinoa)"

    # Test 4: Chipotle (Known brand → Mexican)
    context4 = AdContext(
        unique_id="test4",
        advertiser_id="AR123",
        raw_text="Chipotle burrito bowl with extra guacamole!",
        brand="Chipotle",
        product_type="restaurant"
    )

    print("\n--- Test 4: Chipotle (Fast Path → Mexican) ---")
    decision4 = classifier.classify(context4)
    print(f"✅ Category: {decision4.food_category}")
    print(f"✅ Confidence: {decision4.confidence:.2f}")
    assert decision4.food_category == "Mexican & Tex-Mex", "Chipotle should map to Mexican"

    # Test 5: Poke Bowl (Healthy)
    context5 = AdContext(
        unique_id="test5",
        advertiser_id="AR123",
        raw_text="Fresh poke bowl with salmon, avocado, and edamame!",
        product_type="restaurant"
    )

    print("\n--- Test 5: Poke Bowl (Healthy) ---")
    decision5 = classifier.classify(context5)
    print(f"✅ Category: {decision5.food_category}")
    print(f"✅ Confidence: {decision5.confidence:.2f}")
    print(f"✅ Signals: {decision5.signals}")
    # Poke can be Asian or Healthy - both are acceptable
    acceptable = "Healthy" in decision5.food_category or "Asian" in decision5.food_category
    assert acceptable, "Poke should be Healthy or Asian"

    # Test 6: Cold Pressed Juice (Healthy)
    context6 = AdContext(
        unique_id="test6",
        advertiser_id="AR123",
        raw_text="Cold pressed green juice with detox benefits!",
        product_type="restaurant"
    )

    print("\n--- Test 6: Cold Pressed Juice + Detox ---")
    decision6 = classifier.classify(context6)
    print(f"✅ Category: {decision6.food_category}")
    print(f"✅ Confidence: {decision6.confidence:.2f}")
    print(f"✅ Signals: {decision6.signals}")
    assert "Healthy" in decision6.food_category, "Should detect Healthy (juice/detox)"

    # Test 7: Arabic Burrito (should NOT confuse with Mexican)
    context7 = AdContext(
        unique_id="test7",
        advertiser_id="AR123",
        raw_text="بوريتو طازج مع صلصة لذيذة",  # "Fresh burrito with delicious salsa" in Arabic
        product_type="restaurant"
    )

    print("\n--- Test 7: Arabic Burrito Text (Should Detect Mexican) ---")
    decision7 = classifier.classify(context7)
    print(f"✅ Category: {decision7.food_category}")
    print(f"✅ Confidence: {decision7.confidence:.2f}")
    print(f"✅ Signals: {decision7.signals}")
    # Should detect "burrito" keyword even in Arabic text
    assert "Mexican" in decision7.food_category, "Should detect Mexican from Arabic burrito"

    # Test 8: Vegan Restaurant (Healthy)
    context8 = AdContext(
        unique_id="test8",
        advertiser_id="AR123",
        raw_text="100% vegan and organic restaurant. Fresh salads daily!",
        product_type="restaurant"
    )

    print("\n--- Test 8: Vegan + Organic + Salad ---")
    decision8 = classifier.classify(context8)
    print(f"✅ Category: {decision8.food_category}")
    print(f"✅ Confidence: {decision8.confidence:.2f}")
    print(f"✅ Signals: {decision8.signals}")
    assert "Healthy" in decision8.food_category, "Should detect Healthy (vegan/organic/salad)"

    # Test 9: Sweetgreen (Known brand → Healthy)
    context9 = AdContext(
        unique_id="test9",
        advertiser_id="AR123",
        raw_text="Sweetgreen fresh salad bowl",
        brand="Sweetgreen",
        product_type="restaurant"
    )

    print("\n--- Test 9: Sweetgreen (Fast Path → Healthy) ---")
    decision9 = classifier.classify(context9)
    print(f"✅ Category: {decision9.food_category}")
    print(f"✅ Confidence: {decision9.confidence:.2f}")
    assert decision9.food_category == "Healthy/Organic Food", "Sweetgreen should map to Healthy"

    # Test 10: Jamba Juice (Known brand → Healthy)
    context10 = AdContext(
        unique_id="test10",
        advertiser_id="AR123",
        raw_text="Jamba Juice smoothies with protein",
        brand="Jamba Juice",
        product_type="restaurant"
    )

    print("\n--- Test 10: Jamba Juice (Fast Path → Healthy) ---")
    decision10 = classifier.classify(context10)
    print(f"✅ Category: {decision10.food_category}")
    print(f"✅ Confidence: {decision10.confidence:.2f}")
    assert decision10.food_category == "Healthy/Organic Food", "Jamba Juice should map to Healthy"

    print("\n" + "=" * 70)
    print("🎉 ALL SMART CATEGORY TESTS PASSED!")
    print("=" * 70)
    print("\n✅ Mexican Detection: Working (tacos, burritos, guacamole)")
    print("✅ Acai/Smoothie Bowls: Working (acai, superfood, smoothie bowl)")
    print("✅ Healthy Keywords: Working (kale, quinoa, poke, vegan, organic)")
    print("✅ Juice/Detox: Working (cold pressed, green juice, detox)")
    print("✅ Known Brand Mapping: Working (Chipotle, Sweetgreen, Jamba Juice)")
    print("✅ Bilingual Support: Working (Arabic + English)")
    print("\nAgent 7 is incredibly smart now! 🧠🚀\n")


if __name__ == "__main__":
    test_smart_categories()
