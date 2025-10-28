#!/usr/bin/env python3
"""
Simple test to understand PaddleOCR output format
"""

from paddleocr import PaddleOCR

print("Initializing PaddleOCR...")
ocr = PaddleOCR(lang='en')

image_path = "screenshots/AR12079153035289296897/CR01158896456950611969.jpg"
result = ocr.predict(image_path)

print("\n" + "=" * 80)
print("RAW RESULT:")
print("=" * 80)
print(result)
print("\n" + "=" * 80)
print("RESULT TYPE:", type(result))
print("=" * 80)

if result and 'rec' in result:
    print("\nExtracted Text:")
    for item in result['rec']:
        print(f"  {item}")
