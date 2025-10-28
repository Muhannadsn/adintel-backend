#!/usr/bin/env python3
"""
Test LLaVA on TGI Friday's image to see what it extracts
"""

from agents.vision_extractor import VisionExtractor

print("=" * 80)
print("Testing LLaVA on TGI Friday's Mozzarella Sticks ad")
print("=" * 80)

vision_extractor = VisionExtractor(ollama_host="http://localhost:11434")

image_path = "screenshots/AR12079153035289296897/CR04376697774863810561.jpg"

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
