#!/usr/bin/env python3
"""
Quick script to show what the vision layer extracted from screenshots
"""

from pathlib import Path
from agents.vision_extractor import VisionExtractor

# Initialize vision extractor
extractor = VisionExtractor()

# Screenshots to analyze
screenshots = [
    "screenshots/AR12079153035289296897/CR04376697774863810561.jpg",
    "screenshots/AR12079153035289296897/CR10519607666597167105.jpg"
]

for screenshot_path in screenshots:
    full_path = Path(__file__).parent / screenshot_path

    if not full_path.exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        continue

    print("\n" + "=" * 80)
    print(f"📸 SCREENSHOT: {screenshot_path}")
    print("=" * 80)

    # Extract with vision
    result = extractor.extract(
        image_url="",
        local_path=str(full_path)
    )

    print(f"\n👁️  VISION EXTRACTION RESULTS:")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Method: {result.method_used}")
    print(f"   Text Length: {len(result.extracted_text)} chars")

    print(f"\n📝 EXTRACTED TEXT:")
    print("-" * 80)
    print(result.extracted_text)
    print("-" * 80)

    print(f"\n🎨 VISUAL DESCRIPTION:")
    print("-" * 80)
    print(result.visual_description)
    print("-" * 80)
