#!/usr/bin/env python3
"""
Test the two failing ads to debug text extraction and classification
"""

from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

print("=" * 80)
print("🔍 DEBUGGING TWO FAILING ADS")
print("=" * 80)

orchestrator = AdIntelligenceOrchestrator(expected_region="QA")

# Test 1: Pet Food Ad (should be retail/pet_supplies, NOT restaurant)
print("\n\n" + "=" * 80)
print("TEST 1: PET FOOD AD (CR01158896456950611969)")
print("=" * 80)

context1 = AdContext(
    unique_id="CR01158896456950611969",
    advertiser_id="AR12079153035289296897",
    region_hint="QA",
    raw_text="",
    flags={"screenshot_path": "screenshots/AR12079153035289296897/CR01158896456950611969.jpg"}
)

result1 = orchestrator.enrich(context1)

print("\n📊 RESULTS:")
print(f"   Brand: {result1.brand or 'N/A'}")
print(f"   Product Type: {result1.product_type}")
print(f"   Raw Text Extracted: {result1.raw_text[:200]}...")

# Test 2: Burger King Ad (should detect Burger King brand + restaurant)
print("\n\n" + "=" * 80)
print("TEST 2: BURGER KING AD (CR05867155055546728449)")
print("=" * 80)

context2 = AdContext(
    unique_id="CR05867155055546728449",
    advertiser_id="AR12079153035289296897",
    region_hint="QA",
    raw_text="",
    flags={"screenshot_path": "screenshots/AR12079153035289296897/CR05867155055546728449.jpg"}
)

result2 = orchestrator.enrich(context2)

print("\n📊 RESULTS:")
print(f"   Brand: {result2.brand or 'N/A'}")
print(f"   Product Type: {result2.product_type}")
print(f"   Raw Text Extracted: {result2.raw_text[:200]}...")

print("\n\n" + "=" * 80)
print("EXPECTED vs ACTUAL")
print("=" * 80)
print("\nTEST 1 (Pet Food):")
print(f"   Expected Brand: Snoonu")
print(f"   Actual Brand: {result1.brand or 'N/A'}")
print(f"   Expected Product: pet_supplies or retail")
print(f"   Actual Product: {result1.product_type}")
print(f"   ❌ FAILED" if result1.product_type == "restaurant" else "   ✅ PASSED")

print("\nTEST 2 (Burger King):")
print(f"   Expected Brand: Burger King")
print(f"   Actual Brand: {result2.brand or 'N/A'}")
print(f"   Expected Product: restaurant")
print(f"   Actual Product: {result2.product_type}")
print(f"   ❌ FAILED" if result2.brand != "Burger King" or result2.product_type != "restaurant" else "   ✅ PASSED")
