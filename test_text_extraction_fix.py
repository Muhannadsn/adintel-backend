#!/usr/bin/env python3
"""
Test the fixed text extraction logic that skips LLaVA's numbered list prefixes
"""

import re

def extract_search_term_OLD(raw_text: str) -> str:
    """OLD broken logic"""
    text_sample = raw_text[:200].strip()
    first_line = text_sample.split('\n')[0].strip()
    cleaned = re.sub(r'http\S+|www\S+|QR \d+|\d+%|order now|call|download|free delivery|🔥|📱|💯', '', first_line, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_search_term_NEW(raw_text: str) -> str:
    """NEW fixed logic"""
    text_sample = raw_text[:300].strip()
    lines = text_sample.split('\n')
    useful_line = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip LLaVA's meta-text lines
        if re.match(r'^\d+\.', line):  # Starts with "1.", "2.", etc.
            meta_words = ['visible text', 'text in the image', 'all text', 'image', 'extracted text']
            if any(meta in line.lower() for meta in meta_words):
                continue  # Skip this line

        # Found actual content!
        useful_line = line
        break

    if useful_line:
        cleaned = re.sub(r'http\S+|www\S+|QR \d+|\d+%|order now|call|download|free delivery|🔥|📱|💯', '', useful_line, flags=re.IGNORECASE)
        return cleaned.strip()
    return ""

# Test cases from actual Rafeeq ads
test_cases = [
    """1. The visible text in the image is:
Rafeeq
Download the Rafeeq app
Free delivery on your first order
Order now and save 10%""",

    """1. ALL visible text:
Rafeeq Pro
Get 10% off your first order
Download now
Free delivery available""",

    """1. Text in the image:
Anuage Biolance
10% OFF
First order discount
Free delivery""",

    """1. Visible Text:
Raja Car Rental
Best rates in Qatar
Book now
Call +974 1234 5678"""
]

print("=" * 80)
print("TEXT EXTRACTION FIX TEST")
print("=" * 80)

for i, text in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"Test Case {i}:")
    print(f"{'='*80}")
    print(f"Raw text (first 100 chars):\n{text[:100]}...\n")

    old_result = extract_search_term_OLD(text)
    new_result = extract_search_term_NEW(text)

    print(f"❌ OLD LOGIC: '{old_result}'")
    print(f"✅ NEW LOGIC: '{new_result}'")

    if "visible text" in old_result.lower() or "image" in old_result.lower():
        print("   🚨 OLD = BROKEN (captured LLaVA's meta-text)")
    else:
        print("   ✅ OLD = OK")

    if new_result and "visible text" not in new_result.lower() and "image" not in new_result.lower():
        print("   ✅ NEW = FIXED (skipped meta-text, got actual content)")
    else:
        print("   ⚠️  NEW = needs work")

print("\n" + "=" * 80)
print("SUMMARY: The NEW logic should skip LLaVA's numbered prefixes")
print("=" * 80)
