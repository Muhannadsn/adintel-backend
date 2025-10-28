import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import atexit

def get_browser():
    """
    Initializes and returns a Selenium Chrome WebDriver instance using a temporary copy of a specific user profile.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Path to the original profile
    original_profile_path = "/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1"

    # Path to the new profile in the temporary directory
    new_profile_path = f"{temp_dir}/Profile 1"

    # Copy the profile
    shutil.copytree(original_profile_path, new_profile_path, dirs_exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    chrome_options.add_argument(f"--profile-directory=Profile 1")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    browser = webdriver.Chrome(options=chrome_options)

    # Register a cleanup function to remove the temporary directory on exit
    atexit.register(lambda: shutil.rmtree(temp_dir))

    return browser

if __name__ == '__main__':
    driver = get_browser()
    driver.get("https://www.google.com")
    print(driver.title)
    driver.quit()