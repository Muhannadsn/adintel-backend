#!/usr/bin/env python3
"""
Advanced GATC Scraper - Fast scrolling scraper that extracts all ads
No extension needed - pure Selenium automation
"""

import sys
import os
import time
import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class AdvancedGATCScraper:
    """Fast GATC scraper that scrolls and extracts all ads"""

    def __init__(self, headless=False):
        self.headless = headless
        self.ads_data = []

    def get_browser(self):
        """Launch Chrome browser"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Faster page loads
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Don't load images
        }
        chrome_options.add_experimental_option("prefs", prefs)

        browser = webdriver.Chrome(options=chrome_options)
        print("✓ Browser launched")
        return browser

    def scroll_to_load_ads(self, browser, max_ads=1000, max_scroll_time=120):
        """
        Scroll the page to load all ads dynamically.
        GATC loads ads as you scroll, so we need to scroll to the bottom.
        """
        print(f"\n📜 Scrolling to load ads (max: {max_ads})...")

        start_time = time.time()
        last_height = 0
        scroll_pause = 0.5  # Fast scrolling
        no_new_content_count = 0

        while True:
            # Check if we've been scrolling too long
            if time.time() - start_time > max_scroll_time:
                print(f"⏱️  Scroll timeout reached ({max_scroll_time}s)")
                break

            # Scroll to bottom
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

            # Check current number of ads loaded
            try:
                ad_elements = browser.find_elements(By.CSS_SELECTOR, '[data-creative-id]')
                current_count = len(ad_elements)

                if current_count >= max_ads:
                    print(f"✓ Reached target: {current_count} ads loaded")
                    break

                # Check if new content loaded
                new_height = browser.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_content_count += 1
                    if no_new_content_count >= 5:  # No new content after 5 tries
                        print(f"✓ No more ads loading: {current_count} total ads")
                        break
                else:
                    no_new_content_count = 0
                    print(f"   Loaded {current_count} ads...", end='\r')

                last_height = new_height

            except Exception as e:
                print(f"Warning: {e}")
                break

        # Final count
        ad_elements = browser.find_elements(By.CSS_SELECTOR, '[data-creative-id]')
        print(f"\n✓ Scrolling complete: {len(ad_elements)} ads loaded")
        return ad_elements

    def extract_ad_data(self, ad_element, browser):
        """Extract data from a single ad element"""
        try:
            # Get creative ID
            creative_id = ad_element.get_attribute('data-creative-id') or ''

            # Try to get advertiser ID from parent elements or page context
            advertiser_id = browser.execute_script("""
                const match = window.location.href.match(/advertiser\\/(AR[0-9]+)/);
                return match ? match[1] : '';
            """)

            # Extract ad image/video
            image_url = ''
            try:
                img = ad_element.find_element(By.CSS_SELECTOR, 'img')
                image_url = img.get_attribute('src') or ''
            except:
                pass

            # Extract text content
            text_content = ''
            try:
                text_content = ad_element.text or ''
            except:
                pass

            # Extract dates (first shown, last shown)
            first_shown = ''
            last_shown = ''
            try:
                # Look for date elements - GATC usually has date ranges
                date_elements = ad_element.find_elements(By.CSS_SELECTOR, '[aria-label*="date"], [aria-label*="Date"]')
                if date_elements:
                    date_text = date_elements[0].text
                    # Parse dates from text like "Jan 1 - Jan 15, 2025"
                    # You can enhance this parsing
                    last_shown = date_text
            except:
                pass

            # Get HTML content
            html_content = ''
            try:
                html_content = ad_element.get_attribute('innerHTML') or ''
            except:
                pass

            # Extract regions
            regions = ''
            try:
                # Check URL for region
                url = browser.current_url
                if 'region=' in url:
                    regions = url.split('region=')[1].split('&')[0]
            except:
                pass

            return {
                'advertiser_id': advertiser_id,
                'creative_id': creative_id,
                'advertiser_name': 'Unknown',  # Will be set later
                'image_url': image_url,
                'creative_url': image_url,
                'first_shown': first_shown,
                'last_shown': last_shown,
                'regions': regions,
                'html_content': html_content[:500] if html_content else '',  # Limit size
                'text_content': text_content[:200] if text_content else '',
            }

        except Exception as e:
            print(f"Warning: Could not extract ad data: {e}")
            return None

    def scrape_advertiser(self, url, max_ads=1000, days_back=None):
        """
        Scrape ads from an advertiser page

        Args:
            url: GATC advertiser URL
            max_ads: Maximum number of ads to scrape
            days_back: Only get ads from last N days (optional)
        """
        print(f"\n{'='*80}")
        print(f"ADVANCED GATC SCRAPER")
        print(f"{'='*80}")
        print(f"URL: {url}")
        print(f"Max ads: {max_ads}")
        if days_back:
            print(f"Date filter: Last {days_back} days")
        print(f"{'='*80}\n")

        browser = self.get_browser()

        try:
            # Navigate to page
            print(f"📍 Loading page...")
            browser.get(url)
            time.sleep(3)  # Wait for initial load

            # Wait for ads to start appearing
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-creative-id]'))
                )
                print(f"✓ Ads container loaded")
            except TimeoutException:
                print(f"❌ No ads found on page")
                return []

            # Scroll to load all ads
            ad_elements = self.scroll_to_load_ads(browser, max_ads)

            if not ad_elements:
                print(f"❌ No ads found")
                return []

            # Extract data from each ad
            print(f"\n📊 Extracting ad data...")
            ads_data = []

            for i, ad_element in enumerate(ad_elements):
                if i >= max_ads:
                    break

                ad_data = self.extract_ad_data(ad_element, browser)
                if ad_data:
                    ads_data.append(ad_data)

                if (i + 1) % 50 == 0:
                    print(f"   Processed {i + 1}/{len(ad_elements)} ads...")

            print(f"✓ Extracted {len(ads_data)} ads")

            # Filter by date if specified
            if days_back and ads_data:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                # TODO: Implement date filtering based on last_shown field
                print(f"   Date filtering: {days_back} days (implementation needed)")

            return ads_data

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []

        finally:
            browser.quit()
            print(f"✓ Browser closed")

    def save_to_csv(self, ads_data, output_file):
        """Save ads to CSV file"""
        if not ads_data:
            print(f"No data to save")
            return

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ads_data[0].keys())
            writer.writeheader()
            writer.writerows(ads_data)

        print(f"\n💾 Saved to: {output_file}")
        print(f"   Total ads: {len(ads_data)}")


def main():
    parser = argparse.ArgumentParser(description='Advanced GATC Scraper')
    parser.add_argument('--url', type=str, required=True,
                       help='GATC advertiser URL')
    parser.add_argument('--name', type=str, default='competitor',
                       help='Competitor name for file naming')
    parser.add_argument('--max-ads', type=int, default=1000,
                       help='Maximum number of ads to scrape (default: 1000)')
    parser.add_argument('--days-back', type=int, default=None,
                       help='Only scrape ads from last N days (optional)')
    parser.add_argument('--headless', action='store_true',
                       help='Run in headless mode (no browser window)')
    parser.add_argument('--output-dir', type=str,
                       default='data/input',
                       help='Output directory (default: data/input)')

    args = parser.parse_args()

    # Initialize scraper
    scraper = AdvancedGATCScraper(headless=args.headless)

    # Scrape ads
    ads_data = scraper.scrape_advertiser(
        url=args.url,
        max_ads=args.max_ads,
        days_back=args.days_back
    )

    # Save to file
    if ads_data:
        # Extract advertiser ID from URL
        import re
        match = re.search(r'advertiser/(AR\d+)', args.url)
        advertiser_id = match.group(1) if match else 'unknown'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{args.output_dir}/{advertiser_id}_{timestamp}.csv"

        scraper.save_to_csv(ads_data, output_file)

        print(f"\n✅ Scraping complete!")
        print(f"\nNext steps:")
        print(f"   1. View in dashboard: http://localhost:3001")
        print(f"   2. Run analysis: python run_analysis.py --input {output_file}")
    else:
        print(f"\n❌ No ads scraped")


if __name__ == '__main__':
    main()
