#!/usr/bin/env python3
"""
GATC (Google Ad Transparency Center) Scraper
Automatically retrieves competitor ads from GATC for specified advertisers.

Usage:
    python scrapers/gatc_scraper.py --advertiser "Talabat" --region QA
"""

import sys
import os
import time
import argparse
from datetime import datetime
import csv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from utils.browser import get_browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GATCScraper:
    """
    Scrapes ad data from Google Ad Transparency Center for specified advertisers.
    """

    def __init__(self, region="QA"):
        self.region = region.upper()
        self.base_url = "https://adstransparency.google.com"

    def search_advertiser(self, advertiser_name):
        """
        Search for an advertiser on GATC and return their advertiser ID.
        """
        print(f"\n🔍 Searching for advertiser: {advertiser_name}")

        browser = get_browser()
        try:
            # Navigate to GATC
            search_url = f"{self.base_url}/?region={self.region}"
            browser.get(search_url)

            # Wait for search box and enter advertiser name
            search_box = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            search_box.clear()
            search_box.send_keys(advertiser_name)
            time.sleep(2)

            # Wait for search results
            try:
                # Look for first search result link
                first_result = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/advertiser/AR']"))
                )

                advertiser_url = first_result.get_attribute('href')
                advertiser_id = advertiser_url.split('/advertiser/')[1].split('?')[0]

                print(f"✓ Found advertiser ID: {advertiser_id}")
                return advertiser_id

            except TimeoutException:
                print(f"✗ No results found for '{advertiser_name}'")
                return None

        finally:
            browser.quit()

    def scrape_advertiser_ads(self, advertiser_id, advertiser_name, max_ads=100):
        """
        Scrape all ads for a given advertiser ID.
        """
        print(f"\n📥 Scraping ads for advertiser ID: {advertiser_id}")

        browser = get_browser()
        ads = []

        try:
            # Navigate to advertiser page
            advertiser_url = f"{self.base_url}/advertiser/{advertiser_id}?region={self.region}"
            browser.get(advertiser_url)

            # Wait for page to load
            time.sleep(3)

            # Scroll to load more ads (lazy loading)
            print("   Scrolling to load ads...")
            for i in range(5):  # Scroll 5 times
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find all ad creative elements
            print("   Extracting ad data...")
            creative_elements = browser.find_elements(By.CSS_SELECTOR, "a[href*='/creative/CR']")

            for idx, element in enumerate(creative_elements[:max_ads], 1):
                try:
                    creative_url = element.get_attribute('href')
                    creative_id = creative_url.split('/creative/')[1].split('?')[0]

                    # Try to get additional info (format, dates, etc.)
                    # Note: This requires inspecting GATC's HTML structure
                    # For now, we'll just collect basic info

                    ad_data = {
                        'advertiser': advertiser_name,
                        'creative_id': creative_id,
                        'gatc_link': creative_url,
                        'format': 'Unknown',  # TODO: Extract from page
                        'scraped_date': datetime.now().strftime('%Y-%m-%d'),
                        'region': self.region
                    }

                    ads.append(ad_data)

                    if idx % 10 == 0:
                        print(f"   Extracted {idx} ads...")

                except Exception as e:
                    print(f"   Warning: Failed to extract ad {idx}: {e}")
                    continue

            print(f"✓ Scraped {len(ads)} ads")
            return ads

        except Exception as e:
            print(f"✗ Error scraping ads: {e}")
            return ads

        finally:
            browser.quit()

    def save_to_csv(self, ads, output_file):
        """Save scraped ads to CSV file."""
        print(f"\n💾 Saving to {output_file}")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if ads:
                fieldnames = ads[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ads)

        print(f"✓ Saved {len(ads)} ads to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Scrape competitor ads from GATC')
    parser.add_argument('--advertiser', type=str, required=True,
                       help='Advertiser name to search for')
    parser.add_argument('--region', type=str, default='QA',
                       help='Region code (e.g., QA, AE, SA)')
    parser.add_argument('--max-ads', type=int, default=100,
                       help='Maximum number of ads to scrape')
    parser.add_argument('--output', type=str, default=None,
                       help='Output CSV file path')

    args = parser.parse_args()

    # Initialize scraper
    scraper = GATCScraper(region=args.region)

    # Step 1: Find advertiser ID
    advertiser_id = scraper.search_advertiser(args.advertiser)

    if not advertiser_id:
        print(f"\n❌ Could not find advertiser '{args.advertiser}'")
        return

    # Step 2: Scrape ads
    ads = scraper.scrape_advertiser_ads(advertiser_id, args.advertiser, max_ads=args.max_ads)

    if not ads:
        print(f"\n❌ No ads found for '{args.advertiser}'")
        return

    # Step 3: Save to CSV
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"data/input/{args.advertiser.replace(' ', '_')}_{timestamp}.csv"

    scraper.save_to_csv(ads, args.output)

    print(f"\n✅ Scraping complete!")
    print(f"   Advertiser: {args.advertiser}")
    print(f"   Ads scraped: {len(ads)}")
    print(f"   Output: {args.output}")


if __name__ == '__main__':
    main()
