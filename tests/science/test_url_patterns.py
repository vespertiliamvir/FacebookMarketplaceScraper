
import sys
import os
import time
import logging
from typing import List, Dict, Any

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scraper.facebook_scraper import FacebookMarketplaceScraper
from scraper.config import USER_AGENTS
from selenium import webdriver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_url_pattern(name: str, url: str, scraper: FacebookMarketplaceScraper):
    print(f"\n{'='*80}")
    print(f"  [TEST] TESTING PATTERN: {name}")
    print(f"  [URL] URL: {url}")
    print(f"{'='*80}")
    
    scraper.url = url
    scraper.listings_data = [] # Reset data
    
    if not scraper.load_page():
        print(f"  [X] Failed to load page for {name}")
        return

    print("  [wait] Waiting for results to render...")
    time.sleep(5)
    
    # Try to count results immediately
    containers = scraper._find_listing_containers()
    count = len(containers)
    
    print(f"  [!] Result Count: {count}")
    
    if count > 0:
        print(f"  [+] Pattern '{name}' appears to WORK!")
        # Print first few titles to verify relevance
        print("SAMPLE LISTINGS:")
        for i, container in enumerate(containers[:3]):
            try:
                text = container.text.split('\n')[0]
                href = container.get_attribute('href')
                print(f"  {i+1}. Text: '{text}' | URL: {href}")
            except:
                pass
    else:
        print(f"  [-] Pattern '{name}' returned NO results.")

def main():
    location = "atlanta" 
    base_url = f"https://www.facebook.com/marketplace/{location}"
    
    # Initialize scraper with dummy URL just to get driver
    # Use a unique profile for testing to avoid conflicts
    import shutil
    test_profile = os.path.join(os.path.expanduser("~"), ".facebook_scraper_test_profile")
    if os.path.exists(test_profile):
        try:
            shutil.rmtree(test_profile)
        except:
            pass
            
    scraper = FacebookMarketplaceScraper("https://www.facebook.com/marketplace")
    
    # Monkey patch the setup_driver to use test profile
    original_setup = scraper.setup_driver
    
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
    
    try:
        # --- EXPERIMENT 1: MAKE/MODEL FILTERING ---
        
        # 1. Current Method (Query Params on Search)
        # url_1 = f"{base_url}/search/?query=Toyota%20Camry&category_id=546583916084032&exact=false"
        # test_url_pattern("Query Param Search (Toyota Camry)", url_1, scraper)
        
        # 2. Path Based (If it exists) - mimicking /marketplace/category/vehicles
        # url_2 = f"{base_url}/cars/toyota/camry" # This is a guess at the structure
        # test_url_pattern("Path Based Structure (guess)", url_2, scraper)

        # 3. Just 'vehicles' category with query
        # url_3 = f"{base_url}/vehicles?query=Toyota%20Camry"
        # test_url_pattern("Vehicles Category + Query", url_3, scraper)
        
        # --- EXPERIMENT 2: RADIUS ---
        
        # 4. Radius 500 miles
        url_4 = f"{base_url}/search/?query=Vehicles&radius=500"
        test_url_pattern("Radius 500 Test", url_4, scraper)
        
        # 5. Radius 10 miles
        url_5 = f"{base_url}/search/?query=Vehicles&radius=10"
        test_url_pattern("Radius 10 Test", url_5, scraper)

        # --- EXPERIMENT 3: CATEGORY PATH RADIUS ---
        
        # 6. Category Path Radius 500
        # Try /vehicles path instead of /search
        url_6 = f"{base_url}/vehicles?radius=500"
        test_url_pattern("Category Path Radius 500", url_6, scraper)

        # 7. Category Path Radius 10
        url_7 = f"{base_url}/vehicles?radius=10"
        test_url_pattern("Category Path Radius 10", url_7, scraper)

    except Exception as e:
        logger.error(f"Experiment failed: {e}")
    finally:
        print("\nExperiments complete. Keeping browser open for manual inspection for 60 seconds...")
        time.sleep(60)
        scraper.close()

if __name__ == "__main__":
    main()
