#!/usr/bin/env python3
"""
Test that web validation correctly SKIPS when no brand is extracted
"""

from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

print("=" * 80)
print("TEST: Web Validation Skip Logic")
print("=" * 80)

orchestrator = AdIntelligenceOrchestrator(
    expected_region="QA",
    ollama_host="http://localhost:11434",
    model="llama3.1:8b"
)

# Test Case 1: No brand extracted (should SKIP web validation)
print("\n" + "=" * 80)
print("TEST CASE 1: No brand extracted - should SKIP web validation")
print("=" * 80)

context1 = AdContext(
    unique_id="test_no_brand",
    advertiser_id="TEST001",
    region_hint="QA",
    raw_text="Get your delivery now! Fast and affordable."
)

enriched1 = orchestrator.enrich(context1)

print(f"\n✅ Brand: {enriched1.brand or 'None'}")
print(f"✅ Product Type: {enriched1.product_type or 'None'}")
print(f"✅ Web Validated: {enriched1.flags.get('web_validated', False)}")
print(f"✅ Classification Source: {enriched1.flags.get('classification_source', 'unknown')}")

# Test Case 2: Brand extracted (should RUN web validation)
print("\n" + "=" * 80)
print("TEST CASE 2: Brand extracted - should RUN web validation")
print("=" * 80)

context2 = AdContext(
    unique_id="test_with_brand",
    advertiser_id="TEST002",
    region_hint="QA",
    raw_text="Get McDonald's delivered to your doorstep! Order now via Talabat."
)

enriched2 = orchestrator.enrich(context2)

print(f"\n✅ Brand: {enriched2.brand or 'None'}")
print(f"✅ Product Type: {enriched2.product_type or 'None'}")
print(f"✅ Web Validated: {enriched2.flags.get('web_validated', False)}")
print(f"✅ Classification Source: {enriched2.flags.get('classification_source', 'unknown')}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
