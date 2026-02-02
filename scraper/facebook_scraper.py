"""
Facebook Marketplace scraper module.

Robust scraper with multiple fallback selectors and visible browser mode.
Designed for longevity - survives Facebook UI changes.
"""

import time
import logging
import random
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from scraper.config import SELECTORS, SCRAPER_SETTINGS, USER_AGENTS, MISSING_DATA
from scraper.utils import clean_price, clean_mileage, validate_listing

logger = logging.getLogger(__name__)


class FacebookMarketplaceScraper:
    """
    Scrapes car listings from Facebook Marketplace.
    
    Uses multiple fallback selector strategies for robustness.
    Visible browser mode for reliability (headless causes issues).
    """
    
    def __init__(self, url: str, max_listings: int = 500):
        """
        Initialize scraper.
        
        Args:
            url: Facebook Marketplace search URL
            max_listings: Maximum number of listings to scrape
        """
        self.url = url
        self.max_listings = max_listings
        self.driver = None
        self.listings_data = []
        
    def setup_driver(self) -> None:
        """Set up Chrome WebDriver with appropriate options."""
        logger.info("Setting up Chrome WebDriver...")
        
        options = webdriver.ChromeOptions()
        
        # Visible mode (user confirmed headless doesn't work well)
        if SCRAPER_SETTINGS['headless']:
            options.add_argument('--headless')
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f'user-agent={user_agent}')
        
        # Performance options
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set timeouts
        self.driver.set_page_load_timeout(SCRAPER_SETTINGS['page_load_timeout'])
        
        logger.info("WebDriver setup complete")
    
    def load_page(self) -> bool:
        """
        Load Facebook Marketplace page.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading URL: {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            time.sleep(5)
            
            logger.info("Page loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load page: {e}")
            return False
    
    def scroll_page(self) -> int:
        """
        Scroll page to load more listings.
        
        Uses intelligent scrolling - stops when no new content loads.
        
        Returns:
            Number of listings found after scrolling
        """
        logger.info("Starting page scroll to load listings...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        no_change_count = 0
        
        while scroll_attempts < SCRAPER_SETTINGS['max_scroll_attempts']:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content to load
            time.sleep(SCRAPER_SETTINGS['scroll_pause_time'])
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Check if we've reached the bottom
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:  # No new content after 3 attempts
                    logger.info("Reached end of listings")
                    break
            else:
                no_change_count = 0
            
            last_height = new_height
            scroll_attempts += 1
            
            # Check if we have enough listings
            current_count = len(self._find_listing_containers())
            logger.info(f"Scroll {scroll_attempts}: Found {current_count} listings")
            
            if current_count >= self.max_listings:
                logger.info(f"Reached target of {self.max_listings} listings")
                break
        
        final_count = len(self._find_listing_containers())
        logger.info(f"Scrolling complete. Total listings found: {final_count}")
        return final_count
    
    def _find_listing_containers(self) -> List:
        """
        Find all listing containers using multiple fallback selectors.
        
        Returns:
            List of WebElement containers
        """
        for selector in SELECTORS['listing_container']:
            try:
                if selector.startswith('div[data-testid'):
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                elif selector.startswith('div[role'):
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                elif selector.startswith('a[href'):
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if containers:
                    logger.debug(f"Found {len(containers)} containers with selector: {selector}")
                    return containers
            except Exception as e:
                logger.debug(f"Selector failed: {selector} - {e}")
                continue
        
        logger.warning("No listing containers found with any selector")
        return []
    
    def _extract_with_fallbacks(self, container, field_name: str) -> Optional[str]:
        """
        Extract field using multiple fallback selectors.
        
        Args:
            container: WebElement or BeautifulSoup element
            field_name: Name of field in SELECTORS config
        
        Returns:
            Extracted text or None
        """
        selectors = SELECTORS.get(field_name, [])
        
        for selector in selectors:
            try:
                # Try with Selenium first
                if hasattr(container, 'find_element'):
                    if ':contains' in selector:
                        # BeautifulSoup for :contains
                        soup = BeautifulSoup(container.get_attribute('innerHTML'), 'html.parser')
                        text = selector.split(':contains("')[1].split('")')[0]
                        element = soup.find(text=lambda t: text.lower() in t.lower() if t else False)
                        if element:
                            return element.strip()
                    else:
                        element = container.find_element(By.CSS_SELECTOR, selector)
                        return element.text.strip()
                
                # Try with BeautifulSoup
                elif hasattr(container, 'select_one'):
                    element = container.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            
            except Exception as e:
                logger.debug(f"Selector failed for {field_name}: {selector} - {e}")
                continue
        
        return None
    
    def _extract_images(self, container) -> List[str]:
        """
        Extract all image URLs from listing.
        
        Args:
            container: WebElement or BeautifulSoup element
        
        Returns:
            List of image URLs
        """
        image_urls = []
        
        for selector in SELECTORS['images']:
            try:
                if hasattr(container, 'find_elements'):
                    images = container.find_elements(By.CSS_SELECTOR, selector)
                    for img in images:
                        src = img.get_attribute('src')
                        if src and 'scontent' in src:  # Facebook image URLs contain 'scontent'
                            image_urls.append(src)
                else:
                    images = container.select(selector)
                    for img in images:
                        src = img.get('src')
                        if src and 'scontent' in src:
                            image_urls.append(src)
                
                if image_urls:
                    break
            except Exception as e:
                logger.debug(f"Image extraction failed with selector: {selector} - {e}")
                continue
        
        return image_urls
    
    def _extract_listing_url(self, container) -> Optional[str]:
        """
        Extract listing URL.
        
        Args:
            container: WebElement or BeautifulSoup element
        
        Returns:
            Full listing URL or None
        """
        for selector in SELECTORS['listing_url']:
            try:
                if hasattr(container, 'find_element'):
                    link = container.find_element(By.CSS_SELECTOR, selector)
                    href = link.get_attribute('href')
                else:
                    link = container.select_one(selector)
                    href = link.get('href') if link else None
                
                if href:
                    # Ensure full URL
                    if href.startswith('/'):
                        href = f"https://www.facebook.com{href}"
                    return href
            except Exception as e:
                logger.debug(f"URL extraction failed: {selector} - {e}")
                continue
        
        return None
    
    def extract_listing_data(self, container) -> Optional[Dict[str, Any]]:
        """
        Extract all data from a single listing container.
        
        Args:
            container: WebElement containing listing
        
        Returns:
            Dictionary of listing data or None if extraction fails
        """
        try:
            # Convert to BeautifulSoup for more flexible parsing
            html = container.get_attribute('innerHTML')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract fields with fallbacks
            title = self._extract_with_fallbacks(soup, 'title')
            price_text = self._extract_with_fallbacks(soup, 'price')
            description = self._extract_with_fallbacks(soup, 'description')
            mileage_text = self._extract_with_fallbacks(soup, 'mileage')
            
            # Extract images and URL from original container
            images = self._extract_images(container)
            listing_url = self._extract_listing_url(container)
            
            # Clean and validate data
            price = clean_price(price_text) if price_text else None
            mileage = clean_mileage(mileage_text) if mileage_text else MISSING_DATA['mileage']
            
            # Build listing dictionary
            listing = {
                'title': title,
                'price': price,
                'description': description or MISSING_DATA['description'],
                'mileage': mileage,
                'images': images,
                'listing_url': listing_url,
            }
            
            # Validate required fields
            if not validate_listing(listing):
                logger.debug(f"Listing failed validation: {title}")
                return None
            
            return listing
        
        except Exception as e:
            logger.warning(f"Failed to extract listing data: {e}")
            return None
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method.
        
        Returns:
            List of listing dictionaries
        """
        try:
            # Setup
            self.setup_driver()
            
            # Load page
            if not self.load_page():
                return []
            
            # Scroll to load listings
            self.scroll_page()
            
            # Find all listing containers
            containers = self._find_listing_containers()
            logger.info(f"Processing {len(containers)} listings...")
            
            # Extract data from each listing
            for i, container in enumerate(containers[:self.max_listings], 1):
                try:
                    listing_data = self.extract_listing_data(container)
                    if listing_data:
                        self.listings_data.append(listing_data)
                        logger.info(f"Extracted listing {i}/{min(len(containers), self.max_listings)}: {listing_data.get('title', 'N/A')}")
                    
                    # Small delay to avoid detection
                    time.sleep(0.5)
                
                except StaleElementReferenceException:
                    logger.warning(f"Stale element at index {i}, skipping")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing listing {i}: {e}")
                    continue
            
            logger.info(f"Scraping complete. Extracted {len(self.listings_data)} valid listings")
            return self.listings_data
        
        finally:
            self.close()
    
    def close(self) -> None:
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
