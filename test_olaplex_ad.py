#!/usr/bin/env python3
"""
Test LLaVA on Olaplex ad - challenging product advertised on marketplace
"""

from agents.vision_extractor import VisionExtractor

print("=" * 80)
print("Testing LLaVA on Olaplex No.6 Bond Smoother ad")
print("=" * 80)

vision_extractor = VisionExtractor(ollama_host="http://localhost:11434")

image_path = "/Users/muhannadsaad/Desktop/ad-intelligence/screenshots/AR12079153035289296897/CR06773155643311259649.jpg"

result = vision_extractor.extract(image_url="", local_path=image_path)

print(f"\n✅ LLaVA Full Analysis ({len(result.llava_analysis)} chars):")
print("-" * 80)
print(result.llava_analysis)
print("-" * 80)

print(f"\n✅ Extracted Text ({len(result.extracted_text)} chars):")
print("-" * 80)
print(result.extracted_text)
print("-" * 80)

print(f"\n📊 Confidence: {result.confidence:.2f}")

# Test brand extraction on this text
print("\n" + "=" * 80)
print("Testing Brand Extraction")
print("=" * 80)

from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

brand_extractor = BrandExtractor(advertiser_brand_map={})

context = AdContext(
    unique_id="test_olaplex",
    advertiser_id="AR12079153035289296897",
    region_hint="QA",
    raw_text=result.extracted_text
)

matches = brand_extractor.extract(context)

print(f"\n✅ Extracted Brand: {context.brand or 'None'}")
print(f"📊 Brand Confidence: {context.brand_confidence:.2f}" if context.brand_confidence else "")
print(f"🔍 All Matches: {context.brand_matches}")
