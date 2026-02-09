
import sys
import os
import time
import shutil
import logging
from selenium import webdriver

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scraper.facebook_scraper import FacebookMarketplaceScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_test_scraper():
    # Use a unique profile for testing
    test_profile = os.path.join(os.path.expanduser("~"), ".facebook_scraper_query_test")
    if os.path.exists(test_profile):
        try:
            shutil.rmtree(test_profile)
        except:
            pass
            
    scraper = FacebookMarketplaceScraper("https://www.facebook.com/marketplace")
    
    # Custom setup
    def test_setup():
        print("Setting up test driver...")
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={test_profile}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1280,720')
        
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = Service(ChromeDriverManager().install())
        scraper.driver = webdriver.Chrome(service=service, options=options)
        scraper.driver.set_page_load_timeout(30)
        
    scraper.setup_driver = test_setup
    scraper.setup_driver()
    return scraper

def test_query(scraper, query_text, expected_keyword):
    print(f"\n{'='*80}")
    print(f"  [TEST] TESTING QUERY: '{query_text}'")
    print(f"{'='*80}")
    
    # Construct URL manually as the current builder might be broken
    location = "atlanta"
    # category_id for Vehicles = 546583916084032
    url = f"https://www.facebook.com/marketplace/{location}/search/?query={query_text}&category_id=546583916084032&exact=false"
    
    scraper.url = url
    scraper.listings_data = []
    
    if not scraper.load_page():
        print("[X] Failed to load page")
        return

    print("[wait] Waiting for results...")
    time.sleep(5)
    
    containers = scraper._find_listing_containers()
    print(f"[!] Found {len(containers)} listings")
    
    matches = 0
    for container in containers[:5]:
        text = container.text.lower()
        if expected_keyword.lower() in text:
            matches += 1
            print(f"  [+] Match: {text.splitlines()[0]}")
        else:
            print(f"  [-] No match: {text.splitlines()[0]}")
            
    if matches > 0:
        print(f"\n[+] CONCLUSION: Query '{query_text}' WORKS!")
    else:
        print(f"\n[-] CONCLUSION: Query '{query_text}' FAILED to find relevant results.")

def main():
    scraper = setup_test_scraper()
    try:
        # Test 1: Generic "Vehicles" (Current behavior)
        # test_query(scraper, "Vehicles", "Toyota") # Unlikely to match specifically Toyota
        
        # Test 2: Specific Make "Toyota"
        test_query(scraper, "Toyota", "Toyota")
        
        # Test 3: Specific Model "Honda Civic"
        test_query(scraper, "Honda Civic", "Civic")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
