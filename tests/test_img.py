# test_gatc_links.py
import sys
from pathlib import Path

# Ensure project root is on sys.path so local packages resolve when run directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.csv_handler import read_input_csv
from utils.browser import get_browser

INPUT_FILE = PROJECT_ROOT / "data" / "input" / "gatc-scraped-data (1).csv"
creatives = read_input_csv(str(INPUT_FILE))

browser = get_browser()
browser.get(creatives[0].gatc_link)
print(f"Target URL: {creatives[0].gatc_link}")
print(f"Current URL: {browser.current_url}")
print(f"Page title: {browser.title}")
input("Check browser window, then press Enter to close...")
browser.quit()
