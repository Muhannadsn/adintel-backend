#!/usr/bin/env python3
"""
Test the Moroccan Dejellaba ad you showed in the screenshot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext

def test_moroccan_ad():
    print("=" * 80)
    print("TESTING MOROCCAN DEJELLABA AD (Snoonu)")
    print("=" * 80)
    
    # Text from your screenshot
    raw_text = """Men's Moroccan Dejellaba Kaftan Jalabiya

A traditional Moroccan men's garment that combines elegance with comfort. This full-length Dejellaba Kaftan Jalabiya features a classic V-neckline with decorative trim, short sleeves, and a loose-flowing...

Restaurants & Cafes · Millions Await · Restaurants"""
    
    print(f"\n📝 Input Text ({len(raw_text)} chars):")
    print(f"   {raw_text[:150]}...")
    
    # Create context
    context = AdContext(
        unique_id="test_moroccan_ad",
        advertiser_id="snoonu",
        region_hint="QA",
        raw_text=raw_text
    )
    
    # Initialize orchestrator
    print(f"\n🤖 Initializing orchestrator with NEW fixes...")
    orchestrator = AdIntelligenceOrchestrator(
        expected_region="QA",
        ollama_host="http://localhost:11434",
        model="llama3.1:8b"
    )
    
    # Run enrichment
    print(f"\n🚀 Running enrichment pipeline...\n")
    enriched = orchestrator.enrich(context)
    
    # Display detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    
    print(f"\n1️⃣  BRAND EXTRACTION:")
    print(f"   Brand Detected: {enriched.brand or 'N/A'}")
    print(f"   Confidence: {enriched.brand_confidence or 0:.2f}")
    if enriched.brand_matches:
        print(f"   All matches: {[m.name for m in enriched.brand_matches[:3]]}")
    
    print(f"\n2️⃣  WEB SEARCH STRATEGY (NEW FIXES):")
    print(f"   What did we search for? Check logs above ☝️")
    
    print(f"\n3️⃣  WEB VALIDATION RESULTS:")
    web_data = enriched.flags.get('web_validation_data')
    if web_data:
        print(f"   ✅ Web search completed")
        print(f"   Product Type: {web_data.get('product_type')}")
        print(f"   Category: {web_data.get('category')}")
        print(f"   Confidence: {web_data.get('confidence', 0):.2f}")
        print(f"   Reasoning: {web_data.get('metadata', {}).get('reasoning', 'N/A')[:200]}")
    else:
        print(f"   ❌ No web validation performed")
    
    print(f"\n4️⃣  FINAL CLASSIFICATION:")
    print(f"   Product Type: {enriched.product_type or 'N/A'}")
    print(f"   Confidence: {enriched.product_type_confidence or 0:.2f}")
    print(f"   Source: {enriched.flags.get('classification_source', 'unknown')}")
    
    print(f"\n5️⃣  OFFER DETECTION:")
    if enriched.offer:
        print(f"   Offer Type: {enriched.offer.offer_type}")
        print(f"   Details: {enriched.offer.offer_details}")
    else:
        print(f"   No offer detected")
    
    print(f"\n6️⃣  AUDIENCE:")
    if enriched.audience:
        print(f"   Target: {enriched.audience.target_audience}")
    else:
        print(f"   No audience detected")
    
    print("\n" + "=" * 80)
    print("KEY QUESTION: Did it search 'Moroccan Dejellaba' or 'restaurant'?")
    print("Look at the logs above for 'Search strategy' and 'Searching via DuckDuckGo'")
    print("=" * 80)

if __name__ == "__main__":
    test_moroccan_ad()
