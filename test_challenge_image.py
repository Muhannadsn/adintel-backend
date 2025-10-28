#!/usr/bin/env python3
"""
Test LLaVA on challenging ad image
"""

from agents.vision_extractor import VisionExtractor

print("=" * 80)
print("Testing LLaVA on challenging ad image")
print("=" * 80)

vision_extractor = VisionExtractor(ollama_host="http://localhost:11434")

# The image from the user
image_path = "/var/folders/22/m0g15zgd31v6m88b9w33cl300000gn/T/AppTranslocation/BF7E6DDF-C2E1-4CD2-983A-86C5EBF4A08F/d/Claude Code.app/Contents/Resources/vscode-workspace-temp/image-0-89c76ebd-68cd-4c28-b6a7-a83da2f3f5a5"

try:
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
except Exception as e:
    print(f"❌ Error: {e}")
