#!/usr/bin/env python3
"""
Verify PaddleOCR integration with brand_extractor and agents
"""

from agents.vision_extractor import VisionExtractor
from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

print("=" * 80)
print("INTEGRATION CHECK: PaddleOCR → Brand Extractor")
print("=" * 80)

# Test image with Burger King
image_path = "screenshots/AR12079153035289296897/CR05867155055546728449.jpg"

# Step 1: Vision Extraction with PaddleOCR
print("\n📸 STEP 1: Vision Extraction (PaddleOCR)")
print("-" * 80)
vision_extractor = VisionExtractor()
vision_result = vision_extractor.extract(image_url="", local_path=image_path)

print(f"✅ Extracted Text ({len(vision_result.extracted_text)} chars):")
print(f"   {vision_result.extracted_text[:200]}...")
print(f"📊 Method Used: {vision_result.method_used}")
print(f"📊 Confidence: {vision_result.confidence}")

# Step 2: Create AdContext
print("\n🧠 STEP 2: Create AdContext with extracted text")
print("-" * 80)
context = AdContext(
    unique_id="integration_test",
    advertiser_id="test",
    region_hint="QA",
    raw_text=vision_result.extracted_text  # THIS is the key integration point
)
context.vision_extraction = vision_result

print(f"✅ Context created")
print(f"   context.raw_text: {context.raw_text[:100]}...")

# Step 3: Brand Extraction
print("\n🏷️  STEP 3: Brand Extraction from context.raw_text")
print("-" * 80)
brand_extractor = BrandExtractor(advertiser_brand_map={})
matches = brand_extractor.extract(context)

print(f"✅ Brand Matches Found: {len(matches)}")
for match in matches:
    print(f"   - {match.name} ({match.confidence:.2f}) via {match.source} [type: {match.entity_type}]")

print(f"\n📊 Final Context State:")
print(f"   context.brand: {context.brand}")
print(f"   context.brand_confidence: {context.brand_confidence}")
print(f"   context.brand_source: {context.brand_source}")

# Verification
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

checks = [
    ("PaddleOCR extracted text", bool(vision_result.extracted_text)),
    ("Text contains 'Burger King'", "Burger King" in vision_result.extracted_text),
    ("Text contains 'Snoonu'", "Snoonu" in vision_result.extracted_text),
    ("Context received text", bool(context.raw_text)),
    ("Brand extractor found brands", len(matches) > 0),
    ("Burger King detected", context.brand == "Burger King"),
    ("Snoonu filtered (platform)", not any(m.name == "Snoonu" for m in matches)),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")

# Final verdict
all_passed = all(result for _, result in checks)
print("\n" + "=" * 80)
if all_passed:
    print("✅ INTEGRATION WORKING CORRECTLY!")
else:
    print("❌ INTEGRATION ISSUES DETECTED")
print("=" * 80)
