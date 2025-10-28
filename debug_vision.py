#!/usr/bin/env python3
"""
Debug vision extraction to see full output
"""

from api.ai_analyzer import AdIntelligence

def main():
    analyzer = AdIntelligence()

    # Talabat Pro image
    url = "https://tpc.googlesyndication.com/archive/simgad/4877814780854923256"

    print("Extracting text from Talabat Pro image...")
    extracted = analyzer._extract_text_from_image(url)

    print("\n" + "=" * 80)
    print("FULL EXTRACTED TEXT:")
    print("=" * 80)
    print(extracted)
    print("=" * 80)

    # Check for keywords
    subscription_keywords = ['talabat pro', 'برو', 'deliveroo plus', 'subscription', 'اشتراك']
    extracted_lower = extracted.lower()

    print("\nKeyword check:")
    for keyword in subscription_keywords:
        if keyword in extracted_lower:
            print(f"  ✅ Found: '{keyword}'")
        else:
            print(f"  ❌ Not found: '{keyword}'")

if __name__ == "__main__":
    main()
