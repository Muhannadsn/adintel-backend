#!/usr/bin/env python3
"""
Test Pet Food ad after adding pet/supplies to generic category filter
"""

from agents.vision_extractor import VisionExtractor
from agents.brand_extractor import BrandExtractor
from agents.context import AdContext

print("=" * 80)
print("TEST: Pet Food Ad - Brand Detection")
print("=" * 80)

# Pet Food ad
image_path = "screenshots/AR12079153035289296897/CR01158896456950611969.jpg"

# Vision Extraction
print("\n📸 Vision Extraction (PaddleOCR)")
print("-" * 80)
vision_extractor = VisionExtractor()
vision_result = vision_extractor.extract(image_url="", local_path=image_path)

print(f"✅ Extracted Text:")
print(f"   {vision_result.extracted_text}")

# Brand Extraction
print("\n🏷️  Brand Extraction")
print("-" * 80)
context = AdContext(
    unique_id="pet_food_test",
    advertiser_id="test",
    region_hint="QA",
    raw_text=vision_result.extracted_text
)
context.vision_extraction = vision_result

brand_extractor = BrandExtractor(advertiser_brand_map={})
matches = brand_extractor.extract(context)

print(f"✅ Brand Matches Found: {len(matches)}")
for match in matches:
    print(f"   - {match.name} ({match.confidence:.2f}) via {match.source} [type: {match.entity_type}]")

print(f"\n📊 Final Result:")
print(f"   context.brand: {context.brand or 'N/A'}")
print(f"   context.brand_confidence: {context.brand_confidence or 'N/A'}")

# Verification
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

checks = [
    ("Text extracted", bool(vision_result.extracted_text)),
    ("'Snoonu' in text", "Snoonu" in vision_result.extracted_text),
    ("'Pet Food' in text", "Pet Food" in vision_result.extracted_text),
    ("'Pet Supplies' NOT detected as brand", context.brand != "Pet Supplies"),
    ("Snoonu (platform) filtered", not any(m.name == "Snoonu" for m in matches)),
    ("Brand is N/A (no specific merchant)", context.brand is None),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")

all_passed = all(result for _, result in checks)
print("\n" + "=" * 80)
if all_passed:
    print("✅ PERFECT! No specific pet brand found (as expected for category ad)")
    print("   This is a Snoonu platform ad promoting the Pet Food CATEGORY,")
    print("   not advertising a specific pet brand like 'PetZone' or 'Pawfect'")
else:
    print("❌ ISSUES DETECTED")
print("=" * 80)
