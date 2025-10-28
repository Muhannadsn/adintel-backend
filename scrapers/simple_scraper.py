#!/usr/bin/env python3
"""
Simple GATC Scraper - Opens Chrome and waits for YOU to click extension
No complex automation - just opens the page and monitors for download
"""
import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def open_browser_and_wait(url, chrome_profile, download_dir, competitor_name, max_ads):
    """
    Open Chrome to the advertiser page and wait for manual extension trigger
    """
    print(f"\n{'='*80}")
    print(f"SIMPLE GATC SCRAPER")
    print(f"{'='*80}\n")

    print(f"Competitor: {competitor_name}")
    print(f"URL: {url}")
    print(f"Max ads: {max_ads}\n")

    # Setup Chrome
    chrome_options = Options()

    parts = chrome_profile.rsplit('/', 1)
    user_data_dir = parts[0]
    profile_dir = parts[1] if len(parts) > 1 else "Default"

    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument(f"--profile-directory={profile_dir}")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    print("🚀 Launching Chrome...")
    browser = webdriver.Chrome(options=chrome_options)
    print("✓ Chrome opened\n")

    print(f"📍 Navigating to advertiser page...")
    browser.get(url)
    time.sleep(3)
    print(f"✓ Page loaded: {browser.current_url}\n")

    print("=" * 80)
    print("⚠️  MANUAL STEP REQUIRED")
    print("=" * 80)
    print(f"\nPlease do the following:")
    print(f"  1. Click the GATC Scraper extension icon (in Chrome toolbar)")
    print(f"  2. Enter {max_ads} in the 'Number of ads' field")
    print(f"  3. Click 'Scrape Current Page' button")
    print(f"\n   Script is monitoring {download_dir} for the CSV file...")
    print(f"   It will automatically detect when download is complete.")
    print("=" * 80 + "\n")

    # Get existing files
    download_path = Path(download_dir)
    existing_files = set(download_path.glob("*.csv"))

    # Monitor for new file
    start_time = time.time()
    timeout = 600  # 10 minutes

    while time.time() - start_time < timeout:
        current_files = set(download_path.glob("*.csv"))
        new_files = current_files - existing_files

        if new_files:
            new_file = list(new_files)[0]
            time.sleep(2)  # Ensure download is complete

            print(f"\n✅ Download detected: {new_file.name}")
            print(f"   Waiting 10 seconds before closing browser...")
            time.sleep(10)
            browser.quit()

            # Move file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_name = f"{competitor_name}_{timestamp}.csv"
            final_path = download_path / final_name

            if new_file != final_path:
                new_file.rename(final_path)
                print(f"   Renamed to: {final_name}")

            print(f"\n{'='*80}")
            print(f"✅ SUCCESS!")
            print(f"{'='*80}")
            print(f"\nFile saved: {final_path}")
            print(f"\nNext step - Run analysis:")
            print(f"  python run_analysis.py --input {final_path} --analyzer hybrid\n")

            return str(final_path)

        time.sleep(2)

    print(f"\n❌ Timeout - no file downloaded after {timeout} seconds")
    browser.quit()
    return None


def main():
    parser = argparse.ArgumentParser(description='Simple GATC scraper with manual extension trigger')
    parser.add_argument('--url', type=str, required=True, help='Advertiser URL')
    parser.add_argument('--name', type=str, default='competitor', help='Competitor name')
    parser.add_argument('--max-ads', type=int, default=400, help='Number of ads')
    parser.add_argument('--chrome-profile', type=str, required=True, help='Chrome profile path')
    parser.add_argument('--download-dir', type=str, required=True, help='Download directory')

    args = parser.parse_args()

    open_browser_and_wait(
        url=args.url,
        chrome_profile=args.chrome_profile,
        download_dir=args.download_dir,
        competitor_name=args.name,
        max_ads=args.max_ads
    )


if __name__ == '__main__':
    main()
