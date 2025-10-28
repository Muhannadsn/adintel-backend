#!/usr/bin/env python3
"""
Test a single Rafeeq ad with the FIXED text extraction logic
"""

from agents.context import AdContext
from orchestrator import AdIntelligenceOrchestrator

# Use one of the actual Rafeeq screenshot files
screenshot_path = "screenshots/AR08778154730519003137/CR13970748080891363329.jpg"

print("=" * 80)
print("TESTING RAFEEQ AD WITH FIXED TEXT EXTRACTION")
print("=" * 80)

# Create context for the ad
context = AdContext(
    unique_id="CR13970748080891363329",
    advertiser_id="AR08778154730519003137",
    region_hint="QA",
    raw_text=""  # Will be populated by vision extractor
)

# Set screenshot path
context.set_flag('screenshot_path', screenshot_path)

# Run orchestrator
orchestrator = AdIntelligenceOrchestrator(
    expected_region="QA",
    ollama_host="http://localhost:11434",
    model="llama3.1:8b"
)

enriched = orchestrator.enrich(context)

print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)
print(f"Brand: {enriched.brand}")
print(f"Product Type: {enriched.product_type}")
print(f"Confidence: {enriched.product_type_confidence:.2f}")
print(f"Classification Source: {enriched.flags.get('classification_source', 'N/A')}")

# Check web validation data
if enriched.flags.get('web_validation_data'):
    web_data = enriched.flags['web_validation_data']
    print(f"\nWeb Validation:")
    print(f"  Type: {web_data.get('product_type')}")
    print(f"  Category: {web_data.get('category')}")
    print(f"  Confidence: {web_data.get('confidence'):.2f}")
    print(f"  Search Source: {web_data.get('search_source')}")
