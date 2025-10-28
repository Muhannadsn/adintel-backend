#!/usr/bin/env python3
"""
Test Papa John's brand extraction
"""

from agents.vision_extractor import VisionExtractor
from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

print("=" * 80)
print("Testing Papa John's Brand Extraction")
print("=" * 80)

# Extract vision
vision_extractor = VisionExtractor(ollama_host="http://localhost:11434")
image_path = "screenshots/AR12079153035289296897/CR10519607666597167105.jpg"

result = vision_extractor.extract(image_url="", local_path=image_path)

print(f"\n✅ LLaVA Analysis ({len(result.llava_analysis)} chars):")
print("-" * 80)
print(result.llava_analysis)
print("-" * 80)

print(f"\n✅ Extracted Text ({len(result.extracted_text)} chars):")
print("-" * 80)
print(result.extracted_text)
print("-" * 80)

# Test brand extraction
print("\n" + "=" * 80)
print("Testing Brand Extraction")
print("=" * 80)

brand_extractor = BrandExtractor(advertiser_brand_map={})

context = AdContext(
    unique_id="test_papa_johns",
    advertiser_id="AR12079153035289296897",
    region_hint="QA",
    raw_text=result.extracted_text
)

matches = brand_extractor.extract(context)

print(f"\n✅ Extracted Brand: {context.brand or 'None'}")
print(f"📊 Brand Confidence: {context.brand_confidence:.2f}" if context.brand_confidence else "")
print(f"🔍 All Matches: {context.brand_matches}")
