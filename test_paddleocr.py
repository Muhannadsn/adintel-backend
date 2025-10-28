#!/usr/bin/env python3
"""
Test PaddleOCR on the two failing images
"""

from paddleocr import PaddleOCR

print("=" * 80)
print("🔍 Testing PaddleOCR on Failing Images")
print("=" * 80)

# Initialize PaddleOCR
print("\n⚙️  Initializing PaddleOCR...")
ocr = PaddleOCR(
    use_textline_orientation=True,  # Enable angle classification for rotated text
    lang='en'                        # English + numbers
)
print("✅ PaddleOCR initialized")

# Test 1: Pet Food Ad
print("\n\n" + "=" * 80)
print("TEST 1: PET FOOD AD")
print("=" * 80)

image_path_1 = "screenshots/AR12079153035289296897/CR01158896456950611969.jpg"
result_1 = ocr.predict(image_path_1)

print("\n📝 Extracted Text:")
print("-" * 80)
extracted_text_1 = []
for line in result_1[0]:
    text = line[1][0]  # Extract text from tuple
    confidence = line[1][1]  # Extract confidence
    extracted_text_1.append(text)
    print(f"   {text} (confidence: {confidence:.2f})")

full_text_1 = " ".join(extracted_text_1)
print("-" * 80)
print(f"\n✅ Full Text: {full_text_1}")
print(f"📊 Contains 'Snoonu': {'Snoonu' in full_text_1}")
print(f"📊 Contains 'Pet Food': {'Pet Food' in full_text_1 or 'pet food' in full_text_1.lower()}")

# Test 2: Burger King Ad
print("\n\n" + "=" * 80)
print("TEST 2: BURGER KING AD")
print("=" * 80)

image_path_2 = "screenshots/AR12079153035289296897/CR05867155055546728449.jpg"
result_2 = ocr.predict(image_path_2)

print("\n📝 Extracted Text:")
print("-" * 80)
extracted_text_2 = []
for line in result_2[0]:
    text = line[1][0]
    confidence = line[1][1]
    extracted_text_2.append(text)
    print(f"   {text} (confidence: {confidence:.2f})")

full_text_2 = " ".join(extracted_text_2)
print("-" * 80)
print(f"\n✅ Full Text: {full_text_2}")
print(f"📊 Contains 'Burger King': {'Burger King' in full_text_2}")
print(f"📊 Contains 'Snoonu': {'Snoonu' in full_text_2}")
print(f"📊 Contains '70%': {'70%' in full_text_2}")

# Summary
print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nTest 1 (Pet Food):")
print(f"   ✅ Correctly extracted 'Snoonu'" if 'Snoonu' in full_text_1 else "   ❌ Failed to extract 'Snoonu'")
print(f"   ✅ Correctly extracted 'Pet Food'" if 'Pet Food' in full_text_1 or 'pet food' in full_text_1.lower() else "   ❌ Failed to extract 'Pet Food'")

print("\nTest 2 (Burger King):")
print(f"   ✅ Correctly extracted 'Burger King'" if 'Burger King' in full_text_2 else "   ❌ Failed to extract 'Burger King'")
print(f"   ✅ Correctly extracted '70%'" if '70%' in full_text_2 else "   ❌ Failed to extract '70%'")
