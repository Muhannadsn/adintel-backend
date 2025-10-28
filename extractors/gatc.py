import sys
import os
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from extractors.base import BaseExtractor
from models.ad_creative import Creative, Screenshot
from utils.browser import get_browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GATCIExtractor(BaseExtractor):
    def extract_creative(self, creative: Creative) -> Screenshot:
        """
        Navigates to the Creative URL (not GATC link), takes a screenshot, and returns a Screenshot object.
        Handles proper waiting for ad content to load.
        """
        # Use the Creative field, not the GATC link
        creative_url = creative.creative

        # Skip if Creative field says "Check GATC link" (video ads without direct URL)
        if "Check GATC link" in creative_url:
            print(f"Skipping creative with no direct URL: {creative.format} - {creative.gatc_link}")
            # For these cases, we need to use GATC link instead
            creative_url = creative.gatc_link
            return self._extract_from_gatc(creative, creative_url)

        print(f"Processing creative URL: {creative_url}")
        print(f"Format: {creative.format}")

        browser = get_browser()
        try:
            browser.get(creative_url)

            # Wait for the page to load completely
            WebDriverWait(browser, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for any dynamic content
            time.sleep(2)

            # Create a unique filename for the screenshot
            screenshot_filename = f"creative_{creative.advertiser.replace(' ', '_')}_{int(time.time())}.png"
            screenshot_path = os.path.join(project_root, 'data', 'screenshots', screenshot_filename)

            # Ensure the screenshots directory exists
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

            browser.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")

            return Screenshot(creative_id=hash(creative_url), image_path=screenshot_path)
        except TimeoutException:
            print(f"Timeout waiting for page to load: {creative_url}")
            raise
        except Exception as e:
            print(f"Error processing creative: {creative_url}")
            print(f"Error: {str(e)}")
            raise
        finally:
            browser.quit()

    def _extract_from_gatc(self, creative: Creative, gatc_url: str) -> Screenshot:
        """
        Extracts creative from GATC page by waiting for the ad iframe to load.
        Used for video ads and cases where Creative field is not a direct URL.
        """
        print(f"Extracting from GATC page: {gatc_url}")
        browser = get_browser()
        try:
            browser.get(gatc_url)

            # Wait for page to load
            WebDriverWait(browser, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Wait for the ad iframe to appear (fletch-render-* class)
            try:
                print("Waiting for ad iframe to load...")
                iframe = WebDriverWait(browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[class*='fletch-render']"))
                )
                print(f"Found iframe: {iframe.get_attribute('class')}")

                # Wait a bit more for iframe content to render
                time.sleep(3)

                # Try to switch to iframe and wait for content
                browser.switch_to.frame(iframe)
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                browser.switch_to.default_content()

            except TimeoutException:
                print("Warning: Ad iframe not found or took too long to load. Taking screenshot anyway...")

            # Additional wait for rendering
            time.sleep(2)

            # Create a unique filename for the screenshot
            screenshot_filename = f"creative_{creative.advertiser.replace(' ', '_')}_{int(time.time())}.png"
            screenshot_path = os.path.join(project_root, 'data', 'screenshots', screenshot_filename)

            # Ensure the screenshots directory exists
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

            browser.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")

            return Screenshot(creative_id=hash(gatc_url), image_path=screenshot_path)
        except Exception as e:
            print(f"Error processing GATC page: {gatc_url}")
            print(f"Error: {str(e)}")
            raise
        finally:
            browser.quit()

if __name__ == '__main__':
    # Read the input CSV to get a real creative
    from storage.csv_handler import read_input_csv
    input_file = '/Users/muhannadsaad/Desktop/ad-intelligence/data/input/gatc-scraped-data (1).csv'
    creatives_list = read_input_csv(input_file)

    if creatives_list:
        sample_creative = creatives_list[0]
        print(f"Using creative: {sample_creative.gatc_link}")

        extractor = GATCIExtractor()
        screenshot_data = extractor.extract_creative(sample_creative)
        print(f"Screenshot data: {screenshot_data}")
    else:
        print("No creatives found in the input CSV.")
