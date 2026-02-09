"""
Parallel Scraper Manager module.

Manages multiple browser instances running in parallel to maximize listing extraction.
Splits the search space by price ranges to bypass Facebook's 500-listing scroll limit.
"""

import multiprocessing
import os
import shutil
import logging
import time
import random
from typing import List, Dict, Any, Tuple
from multiprocessing import Pool, Manager
from colorama import Fore, Style

from scraper.facebook_scraper import FacebookMarketplaceScraper
from scraper.config import DEFAULT_SEARCH_PARAMS, USER_AGENTS, MASTER_PROFILE_DIR

logger = logging.getLogger(__name__)

def worker_scrape_task(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Worker function to run a single scraper instance.
    
    Args:
        args: Dictionary containing:
            - search_params: specific search params for this worker (e.g. price range)
            - worker_id: unique ID for this worker
            - profile_path: unique path for Chrome profile
            
    Returns:
        List of scraped listings
    """
    worker_id = args.get('worker_id')
    params = args.get('search_params')
    profile_path = args.get('profile_path')
    
    # Configure logging for this worker
    worker_logger = logging.getLogger(f"Worker-{worker_id}")
    worker_logger.info(f"Starting worker {worker_id} for price range ${params.get('min_price')} - ${params.get('max_price')}")
    
    # DEBUG: Verify params inside worker process
    print(f"\n{Fore.MAGENTA}[Worker {worker_id} INTERNAL] Received Params: Min=${params.get('min_price')} | Max=${params.get('max_price')}{Style.RESET_ALL}")
    
    # Clean up profile if exists
    if os.path.exists(profile_path):
        try:
            shutil.rmtree(profile_path)
        except Exception as e:
            worker_logger.warning(f"Could not clean profile {profile_path}: {e}")
            
    # Strategy: Clone Master Profile to Worker Profile
    # This carries over the login session/cookies
    if os.path.exists(MASTER_PROFILE_DIR):
        try:
            # We ignore lock files to prevent 'Chrome is running' errors
            shutil.copytree(
                MASTER_PROFILE_DIR, 
                profile_path, 
                ignore=shutil.ignore_patterns('Lockfile', 'Singleton*', '*.lock')
            )
            worker_logger.info(f"Cloned Master Profile to worker profile")
        except Exception as e:
            worker_logger.error(f"Failed to copy Master Profile: {e}")
            # Fallback to creating fresh directory
            os.makedirs(profile_path, exist_ok=True)
    else:
        worker_logger.warning("No Master Profile found - starting with fresh session (Expect Login Prompts)")
        os.makedirs(profile_path, exist_ok=True)
            
    # Build URL for this specific range
            
    # Build URL for this specific range
    # We need to manually construct the URL here or use a helper
    # For simplicity, we'll instantiate the scraper and let it handle the URL if we pass it correctly,
    # but the scraper class currently takes a URL in init.
    
    # Let's reconstruct the URL building logic briefly here for the worker
    # In a refactor, this should be a shared utility
    import urllib.parse
    
    base_url = "https://www.facebook.com/marketplace"
    location = params.get('location', 'atlanta')
    # URL encode location (e.g. "New York" -> "New%20York")
    encoded_location = urllib.parse.quote(location.strip())
    
    url = f"{base_url}/{encoded_location}/search/?query=Vehicles&category_id=546583916084032&exact=false"
    
    url_params = []
    if params.get('min_price'): url_params.append(f"minPrice={params['min_price']}")
    if params.get('max_price'): url_params.append(f"maxPrice={params['max_price']}")
    if params.get('radius_miles'): url_params.append(f"radius={params['radius_miles']}")
    if params.get('min_mileage'): url_params.append(f"minMileage={params['min_mileage']}")
    if params.get('max_mileage'): url_params.append(f"maxMileage={params['max_mileage']}")
    if params.get('min_year'): url_params.append(f"minYear={params['min_year']}")
    if params.get('max_year'): url_params.append(f"maxYear={params['max_year']}")
    
    full_url = url + "&" + "&".join(url_params)
    
    # Initialize Scraper
    scraper = FacebookMarketplaceScraper(
        url=full_url,
        max_listings=params.get('max_listings', 500),
        make_filter=params.get('make'),
        model_filter=params.get('model'),
        scrape_descriptions=params.get('scrape_descriptions', False),
        min_price=params.get('min_price'),
        max_price=params.get('max_price')
    )
    
    # Monkey patch setup_driver to use unique profile
    original_setup = scraper.setup_driver
    
    def unique_setup_driver():
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path}")
        
        # Suppress "Welcome to Chrome" / "Sign in" popups
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-search-engine-choice-screen")
        options.add_argument("--disable-fre")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # Random user agent
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f'user-agent={user_agent}')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Stagger startup to prevent race conditions/high load
        # Worker 1 starts immediately, others wait
        if worker_id > 1:
            time.sleep((worker_id - 1) * 3)

        # Randomize window position to verify visual separation
        # Use cascading layout for larger windows
        # worker_id is 1-based
        offset = (worker_id - 1) * 50
        x_pos = 50 + offset
        y_pos = 50 + offset
        
        options.add_argument(f'--window-position={x_pos},{y_pos}')
        # Increased size to ensure sidebar filters are visible (hidden on small screens)
        options.add_argument('--window-size=1280,850')
        
        service = Service(ChromeDriverManager().install())
        scraper.driver = webdriver.Chrome(service=service, options=options)
        scraper.driver.set_page_load_timeout(60)
        
    scraper.setup_driver = unique_setup_driver
    
    try:
        listings = scraper.scrape()
        return listings
    except Exception as e:
        worker_logger.error(f"Worker {worker_id} failed: {e}")
        return []
    finally:
        # Cleanup
        try:
            shutil.rmtree(profile_path, ignore_errors=True)
        except:
            pass

class ParallelScraperManager:
    """
    Orchestrates multiple scraper workers.
    """
    
    def __init__(self, base_preferences: Dict[str, Any], num_workers: int = 3):
        self.prefs = base_preferences
        self.num_workers = num_workers
        
        # Pre-flight check for Master Profile
        from scraper.auth import AuthManager
        if not AuthManager.master_profile_exists():
            raise ValueError("Master Profile not found. Please run login setup first.")
        
    def _generate_price_ranges(self, min_p: int, max_p: int, chunks: int) -> List[Tuple[int, int]]:
        """
        Split price range into chunks.
        Example: 0-10000, 3 chunks -> 0-3333, 3334-6666, 6667-10000
        """
        if max_p <= min_p:
            return [(min_p, max_p)]
            
        total_range = max_p - min_p
        
        # Enforce minimum range per worker to avoid "too close" ranges
        # Set to $200 per user request to ensure distinct results
        min_range_per_worker = 200
        if total_range / chunks < min_range_per_worker:
            adjusted_chunks = max(1, total_range // min_range_per_worker)
            if adjusted_chunks < chunks:
                print(f"  [!] Total range (${total_range}) is too small for {chunks} workers (need ${min_range_per_worker}/worker).")
                print(f"      Reducing to {adjusted_chunks} worker(s) to avoid duplicate results.")
                chunks = adjusted_chunks
        
        step = total_range // chunks
        
        ranges = []
        current_min = min_p
        
        for i in range(chunks):
            current_max = current_min + step
            if i == chunks - 1:
                current_max = max_p # Ensure last chunk hits the max
            
            ranges.append((current_min, current_max))
            current_min = current_max + 1
            
        return ranges
        
    def run(self) -> List[Dict[str, Any]]:
        """
        Execute parallel scraping.
        """
        min_price = self.prefs.get('min_price', 0)
        max_price = self.prefs.get('max_price', 100000)
        
        # Calculate ranges
        ranges = self._generate_price_ranges(min_price, max_price, self.num_workers)
        
        # Prepare worker arguments
        tasks = []
        temp_dir_base = os.path.join(os.path.expanduser("~"), ".fb_scraper_workers")
        os.makedirs(temp_dir_base, exist_ok=True)
        
        for i, (start_p, end_p) in enumerate(ranges):
            worker_prefs = self.prefs.copy()
            worker_prefs['min_price'] = start_p
            worker_prefs['max_price'] = end_p
            
            print(f"  [debug] Worker {i+1} assigned range: ${start_p} - ${end_p}")
            
            task_args = {
                'worker_id': i + 1,
                'search_params': worker_prefs,
                'profile_path': os.path.join(temp_dir_base, f"profile_{i+1}")
            }
            tasks.append(task_args)
            
        print(f"\n{Fore.CYAN}>> Launching {len(tasks)} parallel workers...{Style.RESET_ALL}")
        for t in tasks:
            p = t['search_params']
            w_id = t['worker_id']
            # Loud debug print for user verification
            print(f"{Fore.MAGENTA}  [Worker {w_id}] ASSIGNED RANGE: {Fore.YELLOW}${p['min_price']} - ${p['max_price']}{Style.RESET_ALL}")
            
        # Run workers
        results = []
        with Pool(processes=self.num_workers) as pool:
            # Map returns results in order
            worker_results = pool.map(worker_scrape_task, tasks)
            
            for res in worker_results:
                results.extend(res)
                
        print(f"\n+ All workers finished. Total listings: {len(results)}")
        return results
