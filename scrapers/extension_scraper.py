#!/usr/bin/env python3
"""
GATC Extension Scraper
Uses Chrome extension "GATC Scraper" to extract ad data automatically.

Setup:
1. Create a dedicated Chrome profile with GATC Scraper extension installed
2. Set default download location in Chrome settings
3. Run this script to automate scraping

Usage:
    python scrapers/extension_scraper.py --competitor "Talabat" --region JO --max-ads 400
"""

import sys
import os
import time
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class ExtensionScraper:
    """
    Automates GATC scraping using the GATC Scraper Chrome extension.
    """

    def __init__(self, chrome_profile_path, download_dir):
        """
        Initialize scraper with Chrome profile that has extension installed.

        Args:
            chrome_profile_path: Path to Chrome profile with GATC Scraper extension
            download_dir: Where Chrome downloads files (will monitor this)
        """
        self.chrome_profile_path = chrome_profile_path
        self.download_dir = download_dir

    def get_browser(self):
        """Launch Chrome with YOUR existing profile that has GATC Scraper extension."""
        chrome_options = Options()

        # Extract user-data-dir and profile-directory from path
        # Path format: /Users/.../Chrome/Profile 1
        parts = self.chrome_profile_path.rsplit('/', 1)
        user_data_dir = parts[0]  # /Users/.../Chrome
        profile_dir = parts[1] if len(parts) > 1 else "Default"  # Profile 1

        # Use YOUR existing profile
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={profile_dir}")

        # Don't run headless - extension needs visible browser
        chrome_options.add_argument("--window-size=1920,1080")

        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            browser = webdriver.Chrome(options=chrome_options)
            print(f"✓ Chrome launched successfully")
            return browser
        except Exception as e:
            print(f"❌ Could not launch Chrome: {e}")
            print(f"\n💡 Make sure Chrome is completely closed before running this script")
            raise

    def scrape_competitor(self, advertiser_url, competitor_name=None, max_ads=400):
        """
        Automate the scraping process for a competitor.

        Args:
            advertiser_url: Direct GATC advertiser URL
            competitor_name: Name for file naming (optional)
            max_ads: Number of ads to scrape (max 1000)
        """
        if not competitor_name:
            # Extract name from URL if not provided
            competitor_name = "competitor"

        print(f"\n🔍 Scraping {competitor_name}")
        print(f"   URL: {advertiser_url}")
        print(f"   Max ads: {max_ads}")

        browser = self.get_browser()

        try:
            # Step 1: Navigate DIRECTLY to advertiser page
            print(f"\n📍 Opening advertiser page...")
            print(f"   Navigating to: {advertiser_url}")

            try:
                browser.get(advertiser_url)
                print(f"   Current URL: {browser.current_url}")
                time.sleep(5)  # Wait for page to load
                print(f"✓ Page loaded - URL: {browser.current_url}")
            except Exception as nav_error:
                print(f"❌ Navigation failed: {nav_error}")
                print(f"   Trying manual trigger instead...")
                return self.fallback_manual_trigger(browser, max_ads)

            # Step 3: Get extension ID
            print(f"\n🔧 Finding GATC Scraper extension...")
            extension_id = self.get_extension_id(browser)

            if not extension_id:
                print(f"⚠️  Could not find extension ID automatically")
                print(f"   Trying direct element interaction...")
                return self.fallback_manual_trigger(browser, max_ads)

            # Step 4: Open extension popup directly via URL
            print(f"📂 Opening extension popup...")
            extension_url = f"chrome-extension://{extension_id}/popup.html"
            browser.execute_script(f"window.open('{extension_url}', '_blank');")
            time.sleep(2)

            # Switch to extension popup window
            original_window = browser.current_window_handle
            for handle in browser.window_handles:
                if handle != original_window:
                    browser.switch_to.window(handle)
                    break

            # Step 5: Set number of ads and trigger scraping
            try:
                print(f"📝 Setting max ads to {max_ads}...")

                # Wait for popup to load
                time.sleep(1)

                # Find the input field for number of ads
                ads_input = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']"))
                )
                ads_input.clear()
                ads_input.send_keys(str(max_ads))
                time.sleep(1)

                print(f"🚀 Clicking 'Scrape Current Page' button...")

                # Find and click the scrape button
                scrape_btn = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "scrape-btn"))
                )
                scrape_btn.click()

                print(f"⏳ Scraping in progress... This may take a while for {max_ads} ads")
                print(f"   Monitoring download directory: {self.download_dir}")

                # Switch back to main window
                browser.switch_to.window(original_window)

                # Step 6: Wait for download to complete
                downloaded_file = self.wait_for_download(max_ads)

                if downloaded_file:
                    print(f"✓ Download complete: {downloaded_file}")
                    return downloaded_file
                else:
                    print(f"⚠️  Download not detected")
                    return None

            except Exception as e:
                print(f"⚠️  Error interacting with extension: {e}")
                print(f"   Trying JavaScript injection method...")
                return self.inject_scrape_script(browser, max_ads)

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return None

        finally:
            print(f"\n⏸️  Keeping browser open for 10 seconds...")
            time.sleep(10)
            browser.quit()

    def get_extension_id(self, browser):
        """
        Get the extension ID by navigating to chrome://extensions and parsing the page.
        """
        try:
            # Go to extensions page
            browser.get("chrome://extensions/")
            time.sleep(2)

            # Execute JavaScript to get extension info
            script = """
            return document.querySelector('extensions-manager')
                .shadowRoot.querySelector('extensions-item-list')
                .shadowRoot.querySelectorAll('extensions-item');
            """

            extensions = browser.execute_script(script)

            for ext in extensions:
                # Get extension details
                name_script = "return arguments[0].shadowRoot.querySelector('#name').textContent;"
                name = browser.execute_script(name_script, ext)

                if "GATC" in name or "gatc" in name.lower():
                    id_script = "return arguments[0].id;"
                    ext_id = browser.execute_script(id_script, ext)
                    print(f"✓ Found extension: {name} (ID: {ext_id})")
                    return ext_id

            return None

        except Exception as e:
            print(f"Could not get extension ID: {e}")
            return None

    def inject_scrape_script(self, browser, max_ads):
        """
        Inject JavaScript directly into the page to trigger scraping.
        This is a backup method if popup interaction fails.
        """
        print(f"💉 Injecting scrape script directly...")

        try:
            # Try to trigger extension's content script
            script = f"""
            // Simulate extension button click
            if (window.startGATCScrape) {{
                window.startGATCScrape({max_ads});
            }} else {{
                console.log('Extension script not found');
            }}
            """

            browser.execute_script(script)
            print(f"✓ Script injected, monitoring for download...")

            # Wait for download
            downloaded_file = self.wait_for_download(max_ads, timeout=600)
            return downloaded_file

        except Exception as e:
            print(f"Failed to inject script: {e}")
            return None

    def fallback_manual_trigger(self, browser, max_ads):
        """
        Fallback: Ask user to manually trigger extension.
        """
        print(f"\n⚠️  MANUAL INTERVENTION NEEDED")
        print(f"=" * 60)
        print(f"Please manually:")
        print(f"1. Click the GATC Scraper extension icon")
        print(f"2. Set number of ads to: {max_ads}")
        print(f"3. Click 'Scrape Current Page'")
        print(f"\nScript will monitor for download...")
        print(f"=" * 60)

        # Wait for user to trigger manually
        downloaded_file = self.wait_for_download(max_ads, timeout=600)
        return downloaded_file

    def wait_for_download(self, max_ads, timeout=600):
        """
        Wait for file to appear in download directory.

        Args:
            max_ads: Number of ads being scraped (for time estimation)
            timeout: Max seconds to wait
        """
        # Estimate time: ~1 second per ad + buffer
        estimated_time = (max_ads * 1) + 30
        actual_timeout = min(timeout, estimated_time)

        print(f"   Estimated time: ~{estimated_time} seconds")

        # Get list of files before scraping
        download_path = Path(self.download_dir)
        existing_files = set(download_path.glob("*.csv"))

        start_time = time.time()

        while time.time() - start_time < actual_timeout:
            # Check for new CSV files
            current_files = set(download_path.glob("*.csv"))
            new_files = current_files - existing_files

            if new_files:
                # Found new file!
                new_file = list(new_files)[0]

                # Wait a bit to ensure download is complete
                time.sleep(2)

                return str(new_file)

            time.sleep(2)  # Check every 2 seconds

        return None

    def move_to_project(self, downloaded_file, competitor_name):
        """Move downloaded file to project data directory with proper naming."""
        if not downloaded_file or not os.path.exists(downloaded_file):
            print(f"❌ File not found: {downloaded_file}")
            return None

        # Create target directory
        target_dir = os.path.join(project_root, 'data', 'input', 'scraped')
        os.makedirs(target_dir, exist_ok=True)

        # Create filename with date
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{competitor_name.replace(' ', '_')}_{timestamp}.csv"
        target_path = os.path.join(target_dir, filename)

        # Move file
        shutil.move(downloaded_file, target_path)
        print(f"💾 Moved to: {target_path}")

        return target_path


def main():
    parser = argparse.ArgumentParser(description='Automate GATC scraping with extension')
    parser.add_argument('--url', type=str, required=True,
                       help='Direct GATC advertiser URL (e.g., https://adstransparency.google.com/advertiser/AR...)')
    parser.add_argument('--name', type=str, default='competitor',
                       help='Competitor name for file naming')
    parser.add_argument('--max-ads', type=int, default=400,
                       help='Number of ads to scrape (default: 400, max: 1000)')
    parser.add_argument('--chrome-profile', type=str, required=True,
                       help='Path to Chrome profile with GATC Scraper extension')
    parser.add_argument('--download-dir', type=str, required=True,
                       help='Chrome download directory to monitor')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"GATC EXTENSION SCRAPER")
    print(f"{'='*80}")

    # Initialize scraper
    scraper = ExtensionScraper(
        chrome_profile_path=args.chrome_profile,
        download_dir=args.download_dir
    )

    # Run scraping
    downloaded_file = scraper.scrape_competitor(
        advertiser_url=args.url,
        competitor_name=args.name,
        max_ads=args.max_ads
    )

    # Move file to project
    if downloaded_file:
        final_path = scraper.move_to_project(downloaded_file, args.name)

        if final_path:
            print(f"\n✅ Scraping complete!")
            print(f"   File: {final_path}")
            print(f"\nNext step: Run analysis")
            print(f"   python run_analysis.py --input {final_path} --analyzer hybrid")
    else:
        print(f"\n❌ Scraping failed or file not found")


if __name__ == '__main__':
    main()
