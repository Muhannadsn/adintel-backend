#!/usr/bin/env python3
"""
CDP-based Extension Scraper
Uses Chrome DevTools Protocol to interact with the GATC Scraper extension
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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CDPExtensionScraper:
    def __init__(self, chrome_profile, download_dir):
        self.chrome_profile = chrome_profile
        self.download_dir = download_dir
        self.browser = None

    def start_browser(self):
        """Launch Chrome with CDP enabled"""
        chrome_options = Options()

        # Profile setup
        parts = self.chrome_profile.rsplit('/', 1)
        user_data_dir = parts[0]
        profile_dir = parts[1] if len(parts) > 1 else "Default"

        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={profile_dir}")

        # Enable CDP
        chrome_options.add_argument("--remote-debugging-port=9222")

        # Window settings
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.browser = webdriver.Chrome(options=chrome_options)
        print("✓ Browser launched with CDP enabled")
        return self.browser

    def get_extension_id(self):
        """Get GATC Scraper extension ID"""
        try:
            # Navigate to extensions page
            self.browser.get("chrome://extensions/")
            time.sleep(2)

            # Query extensions via shadow DOM
            script = """
            const manager = document.querySelector('extensions-manager');
            if (!manager) return null;

            const itemList = manager.shadowRoot.querySelector('extensions-item-list');
            if (!itemList) return null;

            const items = itemList.shadowRoot.querySelectorAll('extensions-item');

            for (let item of items) {
                const nameEl = item.shadowRoot.querySelector('#name');
                if (nameEl && nameEl.textContent.toLowerCase().includes('gatc')) {
                    return {
                        id: item.id,
                        name: nameEl.textContent
                    };
                }
            }
            return null;
            """

            result = self.browser.execute_script(script)

            if result:
                print(f"✓ Found extension: {result['name']} ({result['id']})")
                return result['id']
            else:
                print("❌ GATC Scraper extension not found")
                return None

        except Exception as e:
            print(f"❌ Error finding extension: {e}")
            return None

    def trigger_extension(self, extension_id, advertiser_url, max_ads):
        """Navigate to page and trigger extension via popup URL"""
        try:
            # Navigate to advertiser page
            print(f"\n📍 Opening: {advertiser_url}")
            self.browser.get(advertiser_url)
            time.sleep(3)
            print(f"✓ Page loaded")

            # Open extension popup in new tab
            print(f"\n🔧 Opening extension popup...")
            popup_url = f"chrome-extension://{extension_id}/popup.html"

            # Store original window
            original_window = self.browser.current_window_handle

            # Open popup in new window
            self.browser.execute_script(f"window.open('{popup_url}', '_blank', 'width=400,height=600');")
            time.sleep(2)

            # Switch to popup window
            for handle in self.browser.window_handles:
                if handle != original_window:
                    self.browser.switch_to.window(handle)
                    break

            print(f"✓ Extension popup opened")

            # Now interact with popup elements
            try:
                # Find number input
                print(f"\n📝 Setting max ads to {max_ads}...")
                ads_input = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']"))
                )
                ads_input.clear()
                ads_input.send_keys(str(max_ads))
                print(f"✓ Set to {max_ads} ads")

                # Click scrape button
                print(f"\n🚀 Clicking 'Scrape Current Page'...")
                scrape_btn = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "scrape-btn"))
                )
                scrape_btn.click()
                print(f"✓ Scraping started!")

                # Close popup and switch back
                self.browser.close()
                self.browser.switch_to.window(original_window)

                return True

            except Exception as e:
                print(f"❌ Could not interact with popup: {e}")
                print(f"\n⚠️ MANUAL MODE:")
                print(f"   The popup is open - please:")
                print(f"   1. Enter {max_ads} ads")
                print(f"   2. Click 'Scrape Current Page'")
                print(f"   Script will monitor for download...")

                # Switch back to main window
                self.browser.switch_to.window(original_window)
                return True

        except Exception as e:
            print(f"❌ Error triggering extension: {e}")
            return False

    def wait_for_download(self, max_ads, timeout=600):
        """Monitor download directory for CSV file"""
        print(f"\n⏳ Monitoring for download...")
        print(f"   Directory: {self.download_dir}")
        print(f"   Estimated time: ~{max_ads} seconds")

        download_path = Path(self.download_dir)
        existing_files = set(download_path.glob("*.csv"))

        start_time = time.time()

        while time.time() - start_time < timeout:
            current_files = set(download_path.glob("*.csv"))
            new_files = current_files - existing_files

            if new_files:
                new_file = list(new_files)[0]
                time.sleep(2)  # Ensure download complete

                print(f"\n✅ Download complete: {new_file.name}")
                return str(new_file)

            time.sleep(2)

        print(f"\n❌ Timeout - no download detected after {timeout}s")
        return None

    def scrape(self, url, name, max_ads):
        """Main scraping workflow"""
        print(f"\n{'='*80}")
        print(f"CDP EXTENSION SCRAPER")
        print(f"{'='*80}\n")
        print(f"Competitor: {name}")
        print(f"Max ads: {max_ads}\n")

        try:
            # Launch browser
            self.start_browser()

            # Get extension ID
            extension_id = self.get_extension_id()
            if not extension_id:
                return None

            # Trigger extension
            success = self.trigger_extension(extension_id, url, max_ads)
            if not success:
                return None

            # Wait for download
            downloaded_file = self.wait_for_download(max_ads)

            if downloaded_file:
                # Rename file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                final_name = f"{name}_{timestamp}.csv"
                final_path = Path(self.download_dir) / final_name

                Path(downloaded_file).rename(final_path)
                print(f"✓ Renamed to: {final_name}")

                print(f"\n{'='*80}")
                print(f"✅ SUCCESS!")
                print(f"{'='*80}")
                print(f"\nFile: {final_path}")
                print(f"\nNext step:")
                print(f"  python run_analysis.py --input {final_path} --analyzer hybrid\n")

                return str(final_path)

            return None

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None

        finally:
            if self.browser:
                print(f"\n⏸️ Closing browser in 10 seconds...")
                time.sleep(10)
                self.browser.quit()


def main():
    parser = argparse.ArgumentParser(description='CDP-based extension scraper')
    parser.add_argument('--url', required=True, help='Advertiser URL')
    parser.add_argument('--name', default='competitor', help='Competitor name')
    parser.add_argument('--max-ads', type=int, default=400, help='Number of ads')
    parser.add_argument('--chrome-profile', required=True, help='Chrome profile path')
    parser.add_argument('--download-dir', required=True, help='Download directory')

    args = parser.parse_args()

    scraper = CDPExtensionScraper(
        chrome_profile=args.chrome_profile,
        download_dir=args.download_dir
    )

    scraper.scrape(
        url=args.url,
        name=args.name,
        max_ads=args.max_ads
    )


if __name__ == '__main__':
    main()
