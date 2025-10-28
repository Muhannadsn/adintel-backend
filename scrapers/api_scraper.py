#!/usr/bin/env python3
"""
GATC API Scraper - Native Python implementation
Reverse engineered from Chrome extension
No browser needed - pure HTTP requests!
Now with AI enrichment support via local Ollama models
"""
import requests
import json
import urllib.parse
import argparse
import csv
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from orchestrator import AdIntelligenceOrchestrator
    from agents.context import AdContext
    from api.database import AdDatabase
    AI_AVAILABLE = True
except ImportError:
    print("⚠️  AI modules not found. Install dependencies or check paths.")
    AI_AVAILABLE = False


class GATCAPIScraper:
    """Direct API scraper for Google Ad Transparency Center"""

    BASE_URL = "https://adstransparency.google.com"
    API_ENDPOINT = "/anji/_/rpc/SearchService/SearchCreatives"

    def __init__(self, cookies=None):
        """
        Initialize with cookies for authentication

        Args:
            cookies: Dict of cookies from authenticated session
        """
        self.session = requests.Session()

        # Set default headers (copied from your browser)
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://adstransparency.google.com',
            'pragma': 'no-cache',
            'referer': 'https://adstransparency.google.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'x-same-domain': '1',
        })

        if cookies:
            self.session.cookies.update(cookies)

    def search_creatives(self, advertiser_id, region='QA', batch_size=40):
        """
        Fetch ads using SearchCreatives API

        Args:
            advertiser_id: Advertiser ID (e.g., 'AR13676304484790173697')
            region: Region code (e.g., 'QA', 'AE', 'US')
            batch_size: Number of ads per request (max 40)

        Returns:
            List of ad dictionaries
        """
        url = f"{self.BASE_URL}{self.API_ENDPOINT}?authuser=0"

        # Build request payload (reverse engineered from extension)
        payload = {
            "2": batch_size,  # Number of ads to fetch
            "3": {
                "12": {
                    "1": "",
                    "2": True
                },
                "13": {
                    "1": [advertiser_id]  # Advertiser ID list
                }
            },
            "7": {
                "1": 1,
                "2": 29,
                "3": 2840
            }
        }

        # Apply region filter if provided
        if region:
            payload.setdefault("3", {}).setdefault("13", {}).setdefault("4", {})["1"] = [region]

        # URL-encode the payload (this is how GATC expects it)
        encoded_payload = f"f.req={urllib.parse.quote(json.dumps(payload))}"

        print(f"📡 Fetching ads for {advertiser_id} in region {region}...")
        print(f"   Batch size: {batch_size}")
        print(f"   Payload: {payload}")

        try:
            response = self.session.post(url, data=encoded_payload)

            if response.status_code != 200:
                print(f"❌ API returned status {response.status_code}")
                print(f"   Response text: {response.text[:500]}")
                return []

            # Parse response
            data = response.json()

            # Extract ads from response
            ads = self._parse_response(data)

            print(f"✅ Fetched {len(ads)} ads")
            return ads

        except Exception as e:
            print(f"❌ Error fetching ads: {e}")
            return []

    def _parse_response(self, response_data):
        """Parse API response and extract ad data"""
        ads = []

        try:
            # The response structure can vary - look for the ads list
            raw_ads = None

            if isinstance(response_data, dict):
                # Try different possible structures
                if "1" in response_data:
                    raw_ads = response_data["1"]
                elif 1 in response_data:
                    raw_ads = response_data[1]
            elif isinstance(response_data, list):
                raw_ads = response_data

            if not raw_ads:
                print("⚠️  Could not find ads in response")
                print(f"🔍 Response sample: {str(response_data)[:500]}")
                return []

            for ad in raw_ads:
                try:
                    parsed_ad = self._parse_ad(ad)
                    if parsed_ad:
                        ads.append(parsed_ad)
                except Exception as e:
                    print(f"⚠️  Error parsing ad: {e}")
                    continue

            return ads

        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_ad(self, ad_data):
        """Parse individual ad from API response"""
        try:
            # The API uses STRING keys in the response, not integers!
            advertiser_id = ad_data.get("1", "")
            creative_id = ad_data.get("2", "")

            # Creative content is in field "3"
            creative_content = ad_data.get("3", {})

            # HTML content with image URL is in field "3" -> "3" -> "2"
            html_content = ""
            if isinstance(creative_content, dict):
                inner_content = creative_content.get("3", {})
                if isinstance(inner_content, dict):
                    html_content = inner_content.get("2", "")

            # Extract image URL from HTML
            image_url = self._extract_image_url(html_content)

            # First shown date (field "4")
            first_shown_data = ad_data.get("4", {})
            first_shown = first_shown_data.get("1", "") if isinstance(first_shown_data, dict) else ""

            # Last shown date (field "6")
            last_shown_data = ad_data.get("6", {})
            last_shown = last_shown_data.get("1", "") if isinstance(last_shown_data, dict) else ""

            # Advertiser info (field "12")
            advertiser_info = ad_data.get("12", {})
            advertiser_name = "Unknown"
            if isinstance(advertiser_info, dict):
                if advertiser_info.get("1"):
                    advertiser_name = advertiser_info["1"]
                else:
                    candidate = None
                    if isinstance(advertiser_info.get("2"), list) and advertiser_info["2"]:
                        candidate = advertiser_info["2"][0].get("1")
                    if not candidate and isinstance(advertiser_info.get("3"), list) and advertiser_info["3"]:
                        candidate = advertiser_info["3"][0].get("1")
                    if candidate:
                        advertiser_name = candidate

            # Regions (field "7")
            regions = ad_data.get("7", [])
            region_list = []
            if isinstance(regions, list):
                for r in regions:
                    if isinstance(r, dict):
                        region_list.append(r.get("2", ""))

            return {
                'advertiser_id': advertiser_id,
                'creative_id': creative_id,
                'advertiser_name': advertiser_name,
                'image_url': image_url,
                'creative_url': image_url,  # For compatibility with existing code
                'first_shown': first_shown,
                'last_shown': last_shown,
                'regions': ','.join(region_list),
                'region_list': region_list,
                'html_content': html_content
            }

        except Exception as e:
            print(f"⚠️  Error parsing ad data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_image_url(self, html_content):
        """Extract image URL from HTML content"""
        if not html_content:
            return ""

        # Look for src="..." in HTML
        try:
            import re
            match = re.search(r'src="([^"]+)"', html_content)
            if match:
                return match.group(1)
        except:
            pass

        return html_content

    def scrape_advertiser(self, advertiser_id, region='QA', max_ads=400,
                          enrich=False, save_to_db=False):
        """
        Scrape all ads for an advertiser with optional AI enrichment

        Args:
            advertiser_id: Advertiser ID
            region: Region code
            max_ads: Maximum number of ads to fetch
            enrich: If True, analyze ads with AI (SLOW: ~2-3sec per ad)
            save_to_db: If True, save to database instead of/in addition to CSV

        Returns:
            List of ads (enriched if enrich=True)
        """
        all_ads = []
        batch_size = 40  # Max per API call

        print(f"\n{'='*80}")
        print(f"GATC API SCRAPER")
        print(f"{'='*80}\n")
        print(f"Advertiser ID: {advertiser_id}")
        print(f"Region: {region}")
        print(f"Max ads: {max_ads}")
        print(f"AI Enrichment: {'✅ Enabled (SLOW)' if enrich else '❌ Disabled (FAST)'}")
        print(f"Save to Database: {'✅ Yes' if save_to_db else '❌ CSV only'}\n")

        # Scraping phase (fast)
        seen_creatives = set()
        ads_with_images = []
        ads_without_images = []
        max_batches = 3  # Maximum 3 batches to avoid infinite loops
        batches_fetched = 0

        print(f"🎯 Strategy: Prioritizing ads with images for vision analysis\n")

        while batches_fetched < max_batches and len(ads_with_images) < max_ads:
            # Fetch batch
            ads = self.search_creatives(advertiser_id, region, batch_size)
            batches_fetched += 1

            if not ads:
                print("🔚 No more ads available from API")
                break

            new_ads_this_batch = 0
            # Categorize ads by image availability
            for ad in ads:
                creative_id = ad.get('creative_id')

                if not creative_id:
                    continue

                # CRITICAL: Skip duplicates BEFORE processing
                if creative_id in seen_creatives:
                    continue

                seen_creatives.add(creative_id)
                new_ads_this_batch += 1

                # Filter creatives that are explicitly outside the requested region
                region_list = ad.get('region_list') or []
                if region and region_list and region not in region_list:
                    continue

                ad['ad_text'] = ad.get('advertiser_name', '')
                ad['advertiser_id'] = advertiser_id

                # Separate ads with/without images
                if ad.get('image_url'):
                    ads_with_images.append(ad)
                    if len(ads_with_images) <= 5:  # Only log first 5
                        print(f"   ✅ Ad with image: {creative_id}")
                else:
                    ads_without_images.append(ad)

            total_unique = len(seen_creatives)
            images_found = len(ads_with_images)
            print(f"📊 Batch {batches_fetched}: +{new_ads_this_batch} new ads | Total: {total_unique} unique ({images_found} with images, {len(ads_without_images)} without)")

            # If we got NO new ads, API is returning duplicates - stop immediately
            if new_ads_this_batch == 0:
                print("🔚 API returning duplicates - stopping")
                break

            # If we got less than batch_size NEW ads, we've likely reached the end
            if new_ads_this_batch < batch_size / 2:
                print("🔚 Fewer new ads - likely reached end")
                break

            # Stop if we have enough ads with images
            if len(ads_with_images) >= max_ads:
                print(f"🎯 Target reached: {len(ads_with_images)} ads with images!")
                break

        # Prioritize ads with images, then add some without images if needed
        all_ads = ads_with_images[:max_ads]

        # If we don't have enough ads with images, add some without
        if len(all_ads) < max_ads and ads_without_images:
            remaining = max_ads - len(all_ads)
            all_ads.extend(ads_without_images[:remaining])
            print(f"⚠️  Added {min(remaining, len(ads_without_images))} ads WITHOUT images to reach target")

        print(f"\n✅ Scraped {len(all_ads)} ads total ({len([a for a in all_ads if a.get('image_url')])} with images)")

        self._sanity_check(all_ads, advertiser_id, region)

        # Enrichment phase (slow - optional)
        if enrich and AI_AVAILABLE:
            print(f"\n{'='*80}")
            print(f"VISION + AI ENRICHMENT PHASE")
            print(f"{'='*80}")
            print(f"⚠️  This will take ~{len(all_ads) * 10 / 60:.1f} minutes")
            print(f"   ({len(all_ads)} ads × ~10 seconds each with vision extraction)\n")

            # Initialize orchestrator (includes vision layer!)
            orchestrator = AdIntelligenceOrchestrator(
                expected_region=region,
                ollama_host="http://localhost:11434",
                model="llama3.1:8b"
            )

            # Download screenshots and enrich each ad
            enriched_ads = []
            screenshots_dir = Path("screenshots") / advertiser_id
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            for idx, ad in enumerate(all_ads):
                print(f"\n[{idx+1}/{len(all_ads)}] Processing {ad.get('creative_id', 'unknown')}...")

                # Download screenshot
                screenshot_path = None
                if ad.get('image_url'):
                    try:
                        screenshot_path = screenshots_dir / f"{ad['creative_id']}.jpg"
                        response = requests.get(ad['image_url'], timeout=10)
                        response.raise_for_status()
                        screenshot_path.write_bytes(response.content)
                        print(f"   📸 Downloaded screenshot: {screenshot_path}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to download screenshot: {e}")

                # Create context
                context = AdContext(
                    unique_id=ad.get('creative_id', f'ad_{idx}'),
                    advertiser_id=ad.get('advertiser_id'),
                    region_hint=region,
                    raw_text=""  # Vision will populate this!
                )

                # Set screenshot path for vision layer
                if screenshot_path and screenshot_path.exists():
                    context.set_flag('screenshot_path', str(screenshot_path))

                # Run full orchestrator pipeline (with vision!)
                enriched_context = orchestrator.enrich(context)

                # Convert context back to dict for storage (DATABASE COMPATIBLE)
                enriched_ad = ad.copy()
                enriched_ad.update({
                    # Vision-extracted fields
                    'brand': enriched_context.brand,
                    'brand_confidence': enriched_context.brand_confidence,
                    'food_category': enriched_context.flags.get('food_category'),  # From Agent 7
                    'detected_region': enriched_context.region_validation.detected_region if enriched_context.region_validation else None,
                    'rejected_wrong_region': enriched_context.flags.get('rejected_wrong_region', False),

                    # Core classification
                    'product_type': enriched_context.product_type,
                    'product_category': enriched_context.product_type,  # Map to DB field
                    'product_name': enriched_context.brand,  # Use brand as product_name
                    'product_type_confidence': enriched_context.product_type_confidence,

                    # Enrichment fields
                    'offer_type': enriched_context.offer.offer_type if enriched_context.offer else 'none',
                    'offer_details': enriched_context.offer.offer_details if enriched_context.offer else None,
                    'audience_segment': enriched_context.audience.target_audience if enriched_context.audience else None,
                    'target_audience': enriched_context.audience.target_audience if enriched_context.audience else None,  # Keep both for compatibility
                    'primary_theme': enriched_context.themes.primary_theme if enriched_context.themes else None,
                    'messaging_themes': enriched_context.themes.messaging_themes if enriched_context.themes else {},

                    # Metadata
                    'confidence_score': enriched_context.product_type_confidence,
                    'analysis_model': 'orchestrator',
                    'vision_confidence': enriched_context.vision_extraction.confidence if enriched_context.vision_extraction else None,
                    'extracted_text': enriched_context.raw_text[:500] if enriched_context.raw_text else None,  # First 500 chars for CSV
                })

                enriched_ads.append(enriched_ad)

            all_ads = enriched_ads
            print(f"\n✅ Vision + AI enrichment complete!")

        # Save to database (optional)
        if save_to_db and AI_AVAILABLE:
            print(f"\n{'='*80}")
            print(f"SAVING TO DATABASE")
            print(f"{'='*80}\n")

            db = AdDatabase()
            stats = db.save_ads(all_ads, advertiser_id)

            print(f"✅ Database saved: {stats}")

        return all_ads

    def save_to_csv(self, ads, filename):
        """Save ads to CSV file"""
        if not ads:
            print("⚠️  No ads to save")
            return

        # Ensure directory exists
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # Get all unique keys from ads
            fieldnames = list(ads[0].keys())

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ads)

        print(f"💾 Saved to: {filename}")

    def _sanity_check(self, ads, advertiser_id, region):
        """Run lightweight QA checks on scraped ads."""
        if not ads:
            return

        region_counts = {}
        unknown_names = 0

        for ad in ads:
            regions = (ad.get('regions') or '').split(',') if ad.get('regions') else []
            for r in regions or ['UNKNOWN']:
                region_counts[r] = region_counts.get(r, 0) + 1

            advertiser_name = (ad.get('advertiser_name') or '').lower()
            if not advertiser_name or advertiser_name == "unknown":
                unknown_names += 1

        print("\n🔍 SANITY CHECK")
        print(f"   Regions observed: {region_counts}")

        if region and region_counts and any(r != region for r in region_counts if r != 'UNKNOWN'):
            print(f"   ⚠️  WARNING: creatives detected outside requested region '{region}'.")

        if unknown_names:
            print(f"   ⚠️  WARNING: {unknown_names} creatives returned without advertiser names.")

        duplicate_count = len(ads) - len({ad.get('creative_id') for ad in ads})
        if duplicate_count:
            print(f"   ⚠️  WARNING: {duplicate_count} duplicate creative IDs were removed during scraping.")


def parse_advertiser_url(url):
    """
    Extract advertiser ID and region from GATC URL

    Args:
        url: Full GATC URL like 'https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA'

    Returns:
        tuple: (advertiser_id, region) or (None, None) if parsing fails

    Examples:
        >>> parse_advertiser_url('https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA')
        ('AR14306592000630063105', 'QA')
    """
    import re
    from urllib.parse import urlparse, parse_qs

    try:
        # Extract advertiser ID from URL path
        # Pattern: /advertiser/AR... or /advertiser/AR.../
        advertiser_match = re.search(r'/advertiser/(AR\d+)', url)

        if not advertiser_match:
            return None, None

        advertiser_id = advertiser_match.group(1)

        # Extract region from query parameters
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        region = query_params.get('region', ['QA'])[0]  # Default to QA if not specified

        return advertiser_id, region

    except Exception as e:
        print(f"⚠️  Error parsing URL: {e}")
        return None, None


def parse_cookies_from_curl(curl_command):
    """Parse cookies from cURL command"""
    cookies = {}

    # Look for -b flag with cookie string
    if '-b' in curl_command or '--cookie' in curl_command:
        # Extract cookie string
        import re
        cookie_match = re.search(r"-b '([^']+)'", curl_command)
        if not cookie_match:
            cookie_match = re.search(r'-b "([^"]+)"', curl_command)

        if cookie_match:
            cookie_string = cookie_match.group(1)

            # Parse cookies
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value

    return cookies


def main():
    parser = argparse.ArgumentParser(
        description='GATC API Scraper with AI Enrichment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Fast scrape (default - no AI analysis)
  python scrapers/api_scraper.py --url "https://adstransparency.google.com/advertiser/AR.../region=QA"

  # Scrape + AI enrichment (slow but strategic insights)
  python scrapers/api_scraper.py --url "..." --enrich

  # Scrape + save to database
  python scrapers/api_scraper.py --url "..." --save-db

  # Full pipeline: scrape + enrich + save to database
  python scrapers/api_scraper.py --url "..." --enrich --save-db
        '''
    )
    parser.add_argument('--url', help='Full GATC URL (e.g., https://adstransparency.google.com/advertiser/AR.../region=QA)')
    parser.add_argument('--advertiser-id', help='Advertiser ID (e.g., AR13676304484790173697)')
    parser.add_argument('--region', default='QA', help='Region code')
    parser.add_argument('--max-ads', type=int, default=400, help='Max ads to scrape')
    parser.add_argument('--output', help='Output CSV file')
    parser.add_argument('--cookies-file', help='File containing cookies (JSON format)')
    parser.add_argument('--enrich', action='store_true', help='Enable AI enrichment (SLOW: ~2-3sec per ad)')
    parser.add_argument('--save-db', action='store_true', help='Save to database (enables strategic insights)')

    args = parser.parse_args()

    # Parse URL if provided
    advertiser_id = args.advertiser_id
    region = args.region

    if args.url:
        print(f"📎 Parsing URL: {args.url}")
        parsed_id, parsed_region = parse_advertiser_url(args.url)

        if parsed_id:
            advertiser_id = parsed_id
            region = parsed_region
            print(f"✅ Extracted: Advertiser ID = {advertiser_id}, Region = {region}")
        else:
            print(f"❌ Could not parse URL. Please provide --advertiser-id manually")
            return

    if not advertiser_id:
        print(f"❌ Error: Please provide either --url or --advertiser-id")
        parser.print_help()
        return

    # Load cookies if provided
    cookies = None
    if args.cookies_file:
        with open(args.cookies_file, 'r') as f:
            cookies = json.load(f)

    # Initialize scraper
    scraper = GATCAPIScraper(cookies=cookies)

    # Scrape ads (with optional enrichment)
    ads = scraper.scrape_advertiser(
        advertiser_id=advertiser_id,
        region=region,
        max_ads=args.max_ads,
        enrich=args.enrich,
        save_to_db=args.save_db
    )

    # Save to CSV
    if ads:
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/input/{advertiser_id}_{timestamp}.csv"

        scraper.save_to_csv(ads, output_file)

        print(f"\n{'='*80}")
        print(f"✅ SUCCESS!")
        print(f"{'='*80}")
        print(f"\nNext step:")
        print(f"  python run_analysis.py --input {output_file} --analyzer hybrid\n")


if __name__ == '__main__':
    main()
