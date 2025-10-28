#!/usr/bin/env python3
"""
Quick test of brand-first search strategy
"""

from agents.context import AdContext
from orchestrator import AdIntelligenceOrchestrator

print("=" * 80)
print("TESTING BRAND-FIRST SEARCH STRATEGY")
print("=" * 80)

# Simulate a Rafeeq ad with "Anuage Biolance" merchant
context = AdContext(
    unique_id="TEST_001",
    advertiser_id="AR08778154730519003137",
    region_hint="QA",
    raw_text="Anuage Biolance skincare products\n10% OFF\nFree delivery"
)

# Set brand (as the brand extractor would)
context.brand = "Anuage Biolance"
context.brand_confidence = 0.85

# Set product type (as classifier would)
context.product_type = "subscription"
context.product_type_confidence = 0.80

print(f"\n📋 Input:")
print(f"   Brand: {context.brand}")
print(f"   Product Type: {context.product_type}")
print(f"   Raw Text: {context.raw_text[:50]}...")

# Create orchestrator
orchestrator = AdIntelligenceOrchestrator(
    expected_region="QA",
    ollama_host="http://localhost:11434",
    model="llama3.1:8b"
)

# Manually build search term (mimicking what orchestrator does)
search_term = None
if context.brand and context.brand.lower() not in ['n/a', 'unknown', 'the']:
    search_term = context.brand
    print(f"\n✅ Search strategy: Using brand name (merchant) '{search_term}'")

# Test web search
if search_term:
    print(f"\n🔍 Testing DuckDuckGo search for: {search_term}")
    validation = orchestrator.web_search_validator.validate_product(search_term)

    print(f"\n📊 Results:")
    print(f"   Type: {validation.get('product_type')}")
    print(f"   Category: {validation.get('category')}")
    print(f"   Confidence: {validation.get('confidence'):.2f}")
    print(f"   Search Source: {validation.get('search_source')}")

    if validation.get('confidence', 0) > 0.5:
        print(f"\n✅ HIGH CONFIDENCE - Would override LLM classification!")
        print(f"   LLM said: {context.product_type}")
        print(f"   DuckDuckGo says: {validation.get('product_type')}")
    else:
        print(f"\n⚠️  LOW CONFIDENCE - Would keep LLM classification")

print("\n" + "=" * 80)
