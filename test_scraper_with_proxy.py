#!/usr/bin/env python3
"""
Test API Scraper with Bright Data Proxy
Tests actual GATC scraping through the proxy to ensure it works end-to-end
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.api_scraper import GATCAPIScraper

def test_scraping_with_proxy():
    """Test scraping a small batch of ads through proxy"""
    print("🧪 Testing GATC Scraper with Bright Data Proxy\n")

    # Test competitor: Talabat (known to have ads)
    advertiser_id = "AR14306592000630063105"  # Talabat
    region = "QA"
    max_ads = 10  # Small batch for testing

    print(f"📊 Test Parameters:")
    print(f"   Advertiser: {advertiser_id}")
    print(f"   Region: {region}")
    print(f"   Max ads: {max_ads}\n")

    try:
        # Initialize scraper WITH proxy (default behavior)
        print("1️⃣  Initializing scraper with proxy...")
        scraper = GATCAPIScraper(use_proxy=True)
        print("   ✅ Scraper initialized\n")

        # Attempt to scrape
        print("2️⃣  Scraping ads through proxy...")
        ads = scraper.search_creatives(
            advertiser_id=advertiser_id,
            region=region,
            batch_size=max_ads
        )

        if ads and len(ads) > 0:
            print(f"   ✅ Successfully scraped {len(ads)} ads!\n")

            # Show first ad as sample
            print("3️⃣  Sample ad:")
            sample_ad = ads[0]
            print(f"   Ad Text: {sample_ad.get('ad_text', 'N/A')[:100]}...")
            print(f"   Image URL: {sample_ad.get('image_url', 'N/A')[:60]}...")
            print(f"   Regions: {sample_ad.get('regions', 'N/A')}\n")

            print("✅ Proxy scraping test PASSED!")
            print("\n📝 Summary:")
            print(f"   - Proxy: Working ✅")
            print(f"   - GATC API: Accessible ✅")
            print(f"   - Scraping: Successful ✅")
            print(f"   - Ads fetched: {len(ads)}")

            return True
        else:
            print("   ⚠️  No ads returned (but connection worked)")
            print("   This might mean:")
            print("      - The advertiser has no active ads")
            print("      - Need to authenticate with cookies")
            return False

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("GATC SCRAPER PROXY TEST")
    print("="*80 + "\n")

    success = test_scraping_with_proxy()

    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED - Proxy integration working!")
    else:
        print("❌ TESTS FAILED - Check errors above")
    print("="*80)

    sys.exit(0 if success else 1)
