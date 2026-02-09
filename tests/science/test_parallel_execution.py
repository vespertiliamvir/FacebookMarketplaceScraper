
import sys
import os
import logging
import time

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scraper.parallel_manager import ParallelScraperManager

# Configure logging to see worker output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_parallel_execution():
    print(f"\n{'='*80}")
    print("[TEST] TESTING PARALLEL SCRAPER (2 Workers)")
    print(f"{'='*80}")
    
    # Test preferences
    prefs = {
        'location': 'atlanta',
        'min_price': 1000,
        'max_price': 5000,
        'radius_miles': 20,
        'max_listings': 5, # Keep it very small for speed
        'scrape_descriptions': False,
        'make': '',
        'model': ''
    }
    
    # Initialize manager with 2 workers
    manager = ParallelScraperManager(prefs, num_workers=2)
    
    start_time = time.time()
    listings = manager.run()
    end_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"[+] TEST COMPLETE in {end_time - start_time:.2f} seconds")
    print(f"[!] Total Listings: {len(listings)}")
    print(f"{'='*80}")
    
    if len(listings) > 0:
        print("Sample Listings:")
        for i, l in enumerate(listings[:3]):
            print(f"  {i+1}. {l.get('price')} - {l.get('title')}")
    else:
        print("[X] No listings returned (Check if Facebook blocked requests or selectors failed)")

if __name__ == "__main__":
    # Windows multiprocessing support
    from multiprocessing import freeze_support
    freeze_support()
    
    test_parallel_execution()
