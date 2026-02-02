"""
Price comparison module for Edmunds.com.

Fetches fair market values for vehicles to calculate deal ratios.
Includes caching to avoid redundant requests.
"""

import time
import logging
import pickle
import os
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from scraper.config import EDMUNDS_CONFIG, PRICE_COMPARISON_SETTINGS
from scraper.utils import parse_car_title, clean_price

logger = logging.getLogger(__name__)


class PriceComparator:
    """
    Fetches fair market values from Edmunds.com.
    
    Uses caching to minimize requests and improve performance.
    """
    
    def __init__(self, cache_file: str = 'price_cache.pkl'):
        """
        Initialize price comparator.
        
        Args:
            cache_file: Path to cache file for storing price lookups
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.driver = None
        self.request_count = 0
    
    def _load_cache(self) -> Dict:
        """
        Load price cache from file.
        
        Returns:
            Dictionary of cached prices
        """
        if PRICE_COMPARISON_SETTINGS['cache_enabled'] and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                logger.info(f"Loaded {len(cache)} cached prices")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Save price cache to file."""
        if PRICE_COMPARISON_SETTINGS['cache_enabled']:
            try:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.cache, f)
                logger.debug(f"Saved {len(self.cache)} prices to cache")
            except Exception as e:
                logger.warning(f"Failed to save cache: {e}")
    
    def _get_cache_key(self, year: str, make: str, model: str) -> str:
        """
        Generate cache key for a vehicle.
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
        
        Returns:
            Cache key string
        """
        return f"{year}_{make}_{model}".lower().replace(' ', '_')
    
    def setup_driver(self) -> None:
        """Set up Chrome WebDriver for Edmunds scraping."""
        if self.driver is not None:
            return
        
        logger.info("Setting up WebDriver for price comparison...")
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Headless is fine for Edmunds
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(PRICE_COMPARISON_SETTINGS['timeout'])
        
        logger.info("WebDriver ready for price comparison")
    
    def build_edmunds_url(self, year: str, make: str, model: str) -> str:
        """
        Build Edmunds appraisal URL.
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
        
        Returns:
            Complete Edmunds URL
        """
        base = EDMUNDS_CONFIG['base_url']
        path = EDMUNDS_CONFIG['appraisal_path']
        
        # Format: https://www.edmunds.com/honda/civic/2015/appraisal-value/
        url = f"{base}/{make.lower()}/{model.lower()}/{year}{path}"
        return url
    
    def fetch_edmunds_price(self, year: str, make: str, model: str) -> Optional[float]:
        """
        Fetch fair market value from Edmunds.
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
        
        Returns:
            Average fair market price or None if lookup fails
        """
        # Check cache first
        cache_key = self._get_cache_key(year, make, model)
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {year} {make} {model}")
            return self.cache[cache_key]
        
        # Build URL
        url = self.build_edmunds_url(year, make, model)
        logger.info(f"Fetching price from: {url}")
        
        try:
            # Setup driver if needed
            self.setup_driver()
            
            # Load page
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            # Extract price table
            prices = self._extract_prices()
            
            if prices:
                # Calculate average of all condition prices
                avg_price = sum(prices) / len(prices)
                logger.info(f"Found price for {year} {make} {model}: ${avg_price:,.0f}")
                
                # Cache result
                self.cache[cache_key] = avg_price
                self._save_cache()
                
                # Rate limiting
                self.request_count += 1
                time.sleep(PRICE_COMPARISON_SETTINGS['request_delay'])
                
                return avg_price
            else:
                logger.warning(f"No prices found for {year} {make} {model}")
                return None
        
        except TimeoutException:
            logger.warning(f"Timeout fetching price for {year} {make} {model}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching price for {year} {make} {model}: {e}")
            return None
    
    def _extract_prices(self) -> List[float]:
        """
        Extract prices from Edmunds page.
        
        Uses multiple fallback selectors from config.
        
        Returns:
            List of price values
        """
        prices = []
        
        try:
            # Get page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try to find price table
            table_found = False
            for table_selector in EDMUNDS_CONFIG['selectors']['price_table']:
                table = soup.select_one(table_selector)
                if table:
                    table_found = True
                    logger.debug(f"Found price table with selector: {table_selector}")
                    
                    # Extract price cells
                    for cell_selector in EDMUNDS_CONFIG['selectors']['price_cells']:
                        cells = table.select(cell_selector)
                        if cells:
                            for cell in cells:
                                price_text = cell.get_text(strip=True)
                                price = clean_price(price_text)
                                if price and price > 0:
                                    prices.append(price)
                            break
                    break
            
            if not table_found:
                logger.debug("Price table not found, trying alternative extraction")
                # Alternative: Look for any element with price-like text
                price_elements = soup.find_all(text=lambda t: t and '$' in t and any(c.isdigit() for c in t))
                for elem in price_elements[:10]:  # Limit to first 10 matches
                    price = clean_price(elem)
                    if price and 1000 < price < 200000:  # Reasonable car price range
                        prices.append(price)
        
        except Exception as e:
            logger.warning(f"Error extracting prices: {e}")
        
        # Remove duplicates and outliers
        if prices:
            prices = list(set(prices))
            # Filter outliers (keep prices within reasonable range)
            prices = [p for p in prices if 1000 < p < 200000]
        
        return prices
    
    def get_price_for_listing(self, listing: Dict) -> Optional[float]:
        """
        Get fair market price for a listing.
        
        Parses title to extract year/make/model, then fetches price.
        
        Args:
            listing: Listing dictionary with 'title' field
        
        Returns:
            Fair market price or None
        """
        title = listing.get('title', '')
        if not title:
            return None
        
        # Parse title
        parsed = parse_car_title(title)
        year = parsed.get('year')
        make = parsed.get('make')
        model = parsed.get('model')
        
        if not all([year, make, model]):
            logger.debug(f"Could not parse year/make/model from: {title}")
            return None
        
        # Fetch price
        return self.fetch_edmunds_price(year, make, model)
    
    def enrich_listings(self, listings: List[Dict]) -> List[Dict]:
        """
        Enrich all listings with fair market prices.
        
        Args:
            listings: List of listing dictionaries
        
        Returns:
            Enriched listings with 'fair_market_price', 'year', 'make', 'model' fields
        """
        logger.info(f"Enriching {len(listings)} listings with price data...")
        
        enriched = []
        for i, listing in enumerate(listings, 1):
            try:
                # Parse title
                parsed = parse_car_title(listing.get('title', ''))
                listing['year'] = parsed.get('year')
                listing['make'] = parsed.get('make')
                listing['model'] = parsed.get('model')
                
                # Get fair market price
                fair_price = self.get_price_for_listing(listing)
                listing['fair_market_price'] = fair_price
                
                enriched.append(listing)
                
                if i % 10 == 0:
                    logger.info(f"Processed {i}/{len(listings)} listings")
            
            except Exception as e:
                logger.warning(f"Error enriching listing {i}: {e}")
                # Still include listing even if price lookup fails
                listing['fair_market_price'] = None
                enriched.append(listing)
        
        logger.info(f"Enrichment complete. {sum(1 for l in enriched if l.get('fair_market_price'))} listings have price data")
        return enriched
    
    def close(self) -> None:
        """Close the browser and save cache."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Price comparator browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
        
        self._save_cache()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
