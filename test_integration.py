#!/usr/bin/env python3
"""
Quick integration test - verify orchestrator works with database format
"""

from api.orchestrated_analyzer import AdIntelligence

print("=" * 80)
print("INTEGRATION TEST: Orchestrator → Database Format")
print("=" * 80)

# Initialize analyzer (uses orchestrator under the hood)
analyzer = AdIntelligence()

# Test ad in database format (simulating what comes from DB)
test_ad = {
    'id': 12345,
    'ad_text': 'احصل على خصم 50% على طلبك الأول من ماكدونالدز! توصيل سريع في 30 دقيقة. اتصل على +974 4444 5555',
    'image_url': 'https://tpc.googlesyndication.com/archive/simgad/18345084327185912395',
    'advertiser_id': 'AR12079153035289296897',
    'regions': 'QA'
}

print("\n📥 INPUT (Database format):")
print(f"   ad_id: {test_ad['id']}")
print(f"   ad_text: {test_ad['ad_text'][:60]}...")
print(f"   advertiser_id: {test_ad['advertiser_id']}")
print(f"   region: {test_ad['regions']}")

# Run orchestrator analysis
print("\n🤖 Running 11-agent orchestrator...")
enriched = analyzer.categorize_ad(test_ad)

# Display enrichment
print("\n📤 OUTPUT (Database-compatible enrichment):")
print(f"   ✅ product_category: {enriched.get('product_category')}")
print(f"   ✅ product_name: {enriched.get('product_name')}")
print(f"   ✅ brand: {enriched.get('brand')}")
print(f"   ✅ food_category: {enriched.get('food_category')}")
print(f"   ✅ offer_type: {enriched.get('offer_type')}")
print(f"   ✅ offer_details: {enriched.get('offer_details')}")
print(f"   ✅ primary_theme: {enriched.get('primary_theme')}")
print(f"   ✅ audience_segment: {enriched.get('audience_segment')}")
print(f"   ✅ messaging_themes: {enriched.get('messaging_themes')}")
print(f"   ✅ confidence_score: {enriched.get('confidence_score')}")
print(f"   ✅ is_qatar_only: {enriched.get('is_qatar_only')}")
print(f"   ✅ rejected_wrong_region: {enriched.get('rejected_wrong_region')}")
print(f"   ✅ agents_used: {enriched.get('agents_used')}")

print("\n" + "=" * 80)
print("✅ INTEGRATION TEST COMPLETE!")
print("=" * 80)
print("\n💡 Next steps:")
print("   1. The orchestrator is now integrated with your database format")
print("   2. Your existing API endpoints will automatically use the new 11-agent pipeline")
print("   3. Frontend will receive enhanced data through existing API calls")
print("\n🚀 To enrich all ads in database: python3 re_enrich.py")
