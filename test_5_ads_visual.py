#!/usr/bin/env python3
"""
Test 5 ads with the NEW web search fixes and show detailed output
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext
from api.database import AdDatabase

def test_5_ads():
    print("=" * 80)
    print("TESTING 5 ADS WITH NEW WEB SEARCH FIXES")
    print("=" * 80)
    
    # Get 5 ads from database
    db = AdDatabase()
    
    # Get diverse ads - different advertisers
    query = """
    SELECT creative_id, advertiser_id, platform, image_url
    FROM ads
    WHERE image_url IS NOT NULL
    LIMIT 5
    """
    
    import sqlite3
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute(query)
    ads = cursor.fetchall()
    conn.close()
    
    if not ads:
        print("No ads with images found in database!")
        return
    
    print(f"\nFound {len(ads)} ads to test\n")
    
    # Initialize orchestrator with NEW fixes
    orchestrator = AdIntelligenceOrchestrator(
        expected_region="QA",
        ollama_host="http://localhost:11434",
        model="llama3.1:8b"
    )
    
    for idx, (creative_id, advertiser_id, platform, image_url) in enumerate(ads):
        print("\n" + "=" * 80)
        print(f"TEST {idx + 1}/5: {creative_id}")
        print("=" * 80)
        
        # Check for local screenshot
        screenshot_path = Path("screenshots") / advertiser_id / f"{creative_id}.jpg"
        
        if not screenshot_path.exists():
            print(f"⚠️  No screenshot found at {screenshot_path}")
            print(f"   Image URL: {image_url}")
            continue
        
        print(f"📸 Screenshot: {screenshot_path}")
        print(f"🏢 Advertiser: {advertiser_id}")
        print(f"📱 Platform: {platform}")
        
        # Create context
        context = AdContext(
            unique_id=creative_id,
            advertiser_id=advertiser_id,
            region_hint="QA",
            raw_text=""
        )
        
        # Set screenshot path
        context.set_flag('screenshot_path', str(screenshot_path))
        
        # Run enrichment
        enriched = orchestrator.enrich(context)
        
        # Display results
        print("\n" + "=" * 80)
        print(f"📊 RESULTS FOR {creative_id}")
        print("=" * 80)
        
        print(f"\n1️⃣  VISION EXTRACTION:")
        if enriched.vision_extraction:
            extracted_text = enriched.vision_extraction.extracted_text[:300]
            print(f"   Text extracted: {len(enriched.vision_extraction.extracted_text)} chars")
            print(f"   Preview: {extracted_text}...")
            print(f"   Confidence: {enriched.vision_extraction.confidence:.2f}")
        else:
            print("   ❌ No vision extraction")
        
        print(f"\n2️⃣  BRAND DETECTION:")
        print(f"   Brand: {enriched.brand or 'N/A'}")
        print(f"   Confidence: {enriched.brand_confidence or 0:.2f}")
        
        print(f"\n3️⃣  WEB SEARCH (NEW FIXES):")
        web_data = enriched.flags.get('web_validation_data')
        if web_data:
            print(f"   Search performed: ✅")
            print(f"   Product type: {web_data.get('product_type')}")
            print(f"   Category: {web_data.get('category')}")
            print(f"   Confidence: {web_data.get('confidence', 0):.2f}")
            print(f"   Source: {enriched.flags.get('classification_source', 'unknown')}")
        else:
            print("   ❌ No web validation")
        
        print(f"\n4️⃣  FINAL CLASSIFICATION:")
        print(f"   Product Type: {enriched.product_type or 'N/A'}")
        print(f"   Confidence: {enriched.product_type_confidence or 0:.2f}")
        
        if enriched.offer:
            print(f"\n5️⃣  OFFER:")
            print(f"   Type: {enriched.offer.offer_type}")
            print(f"   Details: {enriched.offer.offer_details}")
        
        print("\n" + "=" * 80)
        print("END OF TEST")
        print("=" * 80)
        
        # Pause between tests
        if idx < len(ads) - 1:
            print("\n⏸️  Press Enter to continue to next ad...")
            input()

if __name__ == "__main__":
    test_5_ads()
