"""
Facebook Marketplace scraper module.

Robust scraper with multiple fallback selectors and visible browser mode.
Designed for longevity - survives Facebook UI changes.
"""

import time
import logging
import random
import os
import shutil
import subprocess
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from colorama import Fore, Style

from scraper.config import SELECTORS, SCRAPER_SETTINGS, USER_AGENTS, MISSING_DATA, MASTER_PROFILE_DIR
from scraper.utils import clean_price, clean_mileage, validate_listing
from scraper.description_scraper import batch_scrape_descriptions

logger = logging.getLogger(__name__)


class FacebookMarketplaceScraper:
    """
    Scrapes car listings from Facebook Marketplace.
    
    Uses multiple fallback selector strategies for robustness.
    Visible browser mode for reliability (headless causes issues).
    """
    
    def __init__(self, url: str, max_listings: int = 500, make_filter: str = None, model_filter: str = None, scrape_descriptions: bool = False, min_price: int = None, max_price: int = None):
        """
        Initialize scraper.
        
        Args:
            url: Facebook Marketplace URL to scrape
            max_listings: Maximum number of listings to scrape
            make_filter: Optional make to filter by (e.g., 'toyota')
            model_filter: Optional model to filter by (e.g., 'camry')
            scrape_descriptions: Whether to scrape full descriptions (slower)
            min_price: Minimum price filter (UI based)
            max_price: Maximum price filter (UI based)
        """
        self.url = url
        self.max_listings = max_listings
        self.driver = None
        self.listings_data = []
        self.make_filter = make_filter.lower() if make_filter else None
        self.model_filter = model_filter.lower() if model_filter else None
        self.scrape_descriptions = scrape_descriptions
        self.min_price = min_price
        self.max_price = max_price
        self.use_master_profile = False  # Flag to use persistent master profile
        
    def setup_driver(self) -> None:
        """Set up Chrome WebDriver with appropriate options."""
        logger.info("Setting up Chrome WebDriver...")
        
        options = webdriver.ChromeOptions()
        
        # Determine which profile to use
        if self.use_master_profile:
            profile_dir = MASTER_PROFILE_DIR
            logger.info(f"Using MASTER profile: {profile_dir}")
        else:
            # Use a temporary profile directory to avoid conflicts
            # This is usually overridden by ParallelManager for workers
            profile_dir = os.path.join(os.path.expanduser("~"), ".facebook_scraper_profile")
            logger.info(f"Using temporary profile: {profile_dir}")
            
            # CLONE MASTER PROFILE STRATEGY
            # If Master Profile exists, clone it to this temporary profile
            # so we inherit the login session.
            if os.path.exists(MASTER_PROFILE_DIR):
                logger.info(f"Cloning Master Profile to {profile_dir}...")
                try:
                    # Remove existing temp profile to ensure clean clone
                    if os.path.exists(profile_dir):
                        try:
                            shutil.rmtree(profile_dir)
                        except Exception as e:
                            logger.warning(f"Could not clean existing profile {profile_dir}: {e}")
                    
                    # Copy master to temp
                    # Ignore lock files to prevent 'Chrome is running' errors
                    shutil.copytree(
                        MASTER_PROFILE_DIR, 
                        profile_dir, 
                        ignore=shutil.ignore_patterns('Lockfile', 'Singleton*', '*.lock')
                    )
                    logger.info("Master Profile cloned successfully")
                except Exception as e:
                    logger.error(f"Failed to clone Master Profile: {e}")
                    # Continue anyway, might just start with fresh profile
            
        os.makedirs(profile_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
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
    
    def _dismiss_login_popup(self) -> None:
        """
        Attempt to dismiss the 'Log in' popup if it appears.
        Strategies:
        1. Press ESC
        2. Click 'Close' button
        3. Click backdrop
        """
        try:
            # Strategy 1: Press ESC on body
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            
            # Strategy 2: Look for close button
            # Common selectors for Facebook close buttons
            close_selectors = [
                'div[aria-label="Close"]',
                'div[role="button"][aria-label="Close"]',
                'i[data-visualcompletion="css-img"]', # sometimes the X icon itself
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if close_btn.is_displayed():
                        close_btn.click()
                        logger.info("Dismissed popup via Close button")
                        return
                except:
                    pass
            
            # Strategy 3: REMOVED
            # Clicking background proved too risky (accidental listing clicks)
            
        except Exception as e:
            # It's fine if this fails, just means no popup or couldn't close
            pass

    def set_custom_price_range(self) -> bool:
        """
        Manually set price range using UI inputs.
        Required because Facebook sometimes ignores URL parameters.
        """
        if self.min_price is None and self.max_price is None:
            return True

        logger.info(f"Setting custom price range via UI: {self.min_price} - {self.max_price}")
        
        try:
            # CHECK 1: Are inputs visible? If not, try clicking "Filters" or "Price" dropdown
            inputs_visible = False
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Minimum Range"]')
                inputs_visible = True
            except:
                pass
                
            if not inputs_visible:
                logger.info("Price inputs not found immediately. Attempting to expand 'Price' section...")
                try:
                    # Strategy A: Click "Filters" button first if present
                    filters_btns = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(text(), 'Filters')]")
                    if filters_btns and filters_btns[0].is_displayed():
                        filters_btns[0].click()
                        logger.info("Clicked 'Filters' button")
                        time.sleep(1)
                    
                    # Strategy B: Click "Price" header to expand
                    # Look for "Price" text that seems to be a header
                    price_toggles = self.driver.find_elements(By.XPATH, "//span[text()='Price']")
                    for toggle in price_toggles:
                        try:
                            # Click the parent or the element itself
                            toggle.click()
                            logger.info("Clicked 'Price' text/header")
                            time.sleep(1)
                            # Check if inputs appeared
                            if self.driver.find_elements(By.CSS_SELECTOR, 'input[aria-label="Minimum Range"]'):
                                inputs_visible = True
                                break
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Error expanding filter menus: {e}")

            def type_humanly(element, text):
                try:
                    element.click()
                    time.sleep(0.2)
                    # Standard OS clear: Ctrl+A -> Backspace
                    element.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.1)
                    element.send_keys(Keys.BACK_SPACE)
                    time.sleep(0.1)
                    
                    # Type value
                    element.send_keys(str(text))
                    time.sleep(0.2)
                except Exception as e:
                    logger.warning(f"Typing error: {e}")

            def attempt_set_prices():
                # 1. Set Minimum Price
                if self.min_price is not None:
                    try:
                        logger.info(f"Locating Min Price input for target: {self.min_price}")
                        min_input = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Minimum Range"]')
                        type_humanly(min_input, self.min_price)
                        # Press Enter to lock value (some UIs require this)
                        min_input.send_keys(Keys.RETURN)
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Could not set minimum price UI: {e}")

                # 2. Set Maximum Price
                if self.max_price is not None:
                    try:
                        logger.info(f"Locating Max Price input for target: {self.max_price}")
                        max_input = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Maximum Range"]')
                        type_humanly(max_input, self.max_price)
                        
                        # Press Enter to apply
                        max_input.send_keys(Keys.RETURN)
                        logger.info("Pressed Enter on max price")
                        time.sleep(1)
                        
                        # CHECK: Is there an explicit "Apply" arrow button next to the inputs?
                        # Usually a div with role='button' containing an SVG, adjacent to the inputs
                        try:
                            # Search around the max input for a button
                            # Go up to the container holding min/max/button
                            container = max_input.find_element(By.XPATH, "./../../..")
                            
                            # Look for any clickable div that has an svg inside
                            potential_btns = container.find_elements(By.XPATH, ".//div[@role='button']//svg/..")
                            
                            found_arrow = False
                            for icon_parent in potential_btns:
                                if icon_parent.is_displayed():
                                    # This is likely the arrow button
                                    icon_parent.click()
                                    logger.info("Clicked detected 'Apply' arrow button")
                                    found_arrow = True
                                    time.sleep(2)
                                    break
                            
                            if not found_arrow:
                                # Fallback: Look for "See results" text button
                                see_results = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'See results')]")
                                for sr in see_results:
                                    if sr.is_displayed():
                                        sr.click()
                                        logger.info("Clicked 'See results' text button")
                                        break
                        except Exception as btn_err:
                            logger.debug(f"Apply button search failed: {btn_err}")
                            pass
                            
                    except Exception as e:
                        logger.warning(f"Could not set maximum price UI: {e}")
                
                # Trigger Blur just in case
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').click()
                except:
                    pass

                # MANUAL INTERVENTION PAUSE
                # Per user request: give them a chance to fix it if it's wrong
                print(f"\n{Fore.YELLOW}  [verify] Prices set to {self.min_price}-{self.max_price}. Pausing 30s for manual check...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  If prices didn't update, CLICK THE BOXES and HIT ENTER now.{Style.RESET_ALL}")
                time.sleep(30) # Increased to 30s per user request for "backup plan"

                # Verify
                try:
                    min_val = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Minimum Range"]').get_attribute('value')
                    max_val = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Maximum Range"]').get_attribute('value')
                    
                    # Sanitize
                    import re
                    min_clean = re.sub(r'\D', '', min_val) if min_val else "0"
                    max_clean = re.sub(r'\D', '', max_val) if max_val else "0"
                    
                    logger.info(f"Verification - UI shows: {min_clean}-{max_clean}, Target: {self.min_price}-{self.max_price}")
                    
                    if (self.min_price is not None and str(self.min_price) != min_clean):
                        return False
                    if (self.max_price is not None and str(self.max_price) != max_clean):
                        return False
                    return True
                except:
                    return False

            # First Attempt
            if attempt_set_prices():
                return True
            
            # Retry once
            logger.warning("First attempt to set prices failed verification. Retrying...")
            if attempt_set_prices():
                return True

            raise Exception("Price verification failed after retries")
            
        except Exception as e:
            logger.error(f"Failed to set custom price range: {e}")
            print(f"\n{Fore.RED}[!] AUTO-PRICE SETTING FAILED{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please manually set Min: {self.min_price} and Max: {self.max_price} in the browser window NOW.{Style.RESET_ALL}")
            print(f"Resuming in 15 seconds...")
            time.sleep(15)
            return False

    def load_page(self) -> bool:
        """
        Load Facebook Marketplace page.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {self.url}")
            logger.info("Please wait while the page loads...")
            
            self.driver.get(self.url)
            logger.info(f"Current URL after navigation: {self.driver.current_url}")
            
            # Wait for initial page load
            logger.info("Waiting 5 seconds for page to load...")
            time.sleep(5)
            
            # Dismiss potential login popup immediately
            self._dismiss_login_popup()
            
            # Check current URL again
            current_url = self.driver.current_url
            logger.info(f"Current URL after wait: {current_url}")
            
            # Check if login is required
            if "login" in current_url.lower() or "checkpoint" in current_url.lower():
                print("\n" + "=" * 70)
                print("FACEBOOK LOGIN REQUIRED")
                print("=" * 70)
                print("Please log into Facebook in the browser window.")
                print("Complete any 2FA verification on your phone if needed.")
                print("After you're logged in and see the Marketplace, press Enter here...")
                print("=" * 70)
                input()
                
                # Navigate to marketplace again after login
                logger.info("Navigating to Facebook Marketplace...")
                self.driver.get(self.url)
                time.sleep(5)
                logger.info(f"Current URL after login: {self.driver.current_url}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load page: {e}", exc_info=True)
            return False
    
    def _scroll_to_load_listings(self) -> int:
        """
        Scroll page to load more listings AND extract data during scroll.
        
        Extracts data immediately since Facebook removes listings from DOM as you scroll.
        
        Returns:
            Number of unique listings extracted
        """
        print(f"\n{'='*70}")
        print(f"  SCROLLING & EXTRACTING LISTINGS")
        print(f"{'='*70}\n")
        
        seen_item_ids = set()
        scroll_attempts = 0
        no_new_listings_count = 0
        extracted_count = 0
        prev_unique_count = 0
        
        while scroll_attempts < SCRAPER_SETTINGS['max_scroll_attempts']:
            # Safety Check: Are we still on the search page?
            # Sometimes popups or accidental clicks navigate us to a single item
            current_url = self.driver.current_url
            if '/marketplace/item/' in current_url:
                logger.warning("Detected navigation to single listing. Going back to search results...")
                try:
                    self.driver.back()
                    time.sleep(3)
                    
                    # If still on item page, force reload original URL
                    if '/marketplace/item/' in self.driver.current_url:
                        logger.warning("Back button failed. Re-loading search URL...")
                        self.driver.get(self.url)
                        time.sleep(5)
                except Exception as e:
                    logger.error(f"Error recovering from wrong page: {e}")
                    # Try force reload
                    self.driver.get(self.url)
                    time.sleep(5)

            # Handle popups that might appear during scroll
            if scroll_attempts % 5 == 0:
                self._dismiss_login_popup()

            # Get current listings
            containers = self._find_listing_containers()
            
            # Extract data from new listings immediately
            for container in containers:
                try:
                    href = container.get_attribute('href')
                    if href and '/marketplace/item/' in href:
                        # Extract item ID
                        item_id = href.split('/marketplace/item/')[1].split('/')[0].split('?')[0]
                        
                        # Skip if already processed
                        if item_id in seen_item_ids:
                            continue
                        
                        seen_item_ids.add(item_id)
                        
                        # Extract listing data immediately
                        listing_data = self.extract_listing_data(container)
                        if listing_data:
                            self.listings_data.append(listing_data)
                            extracted_count += 1
                            if extracted_count % 50 == 0:
                                print(f"  [+] {len(self.listings_data)} listings extracted", end='\r')
                except Exception as e:
                    logger.debug(f"Error processing container: {e}")
                    continue
            
            # Check for progress - compare current unique count with previous
            current_unique_count = len(seen_item_ids)
            if current_unique_count == prev_unique_count:
                no_new_listings_count += 1
            else:
                no_new_listings_count = 0
                prev_unique_count = current_unique_count
            
            print(f"  Scroll {scroll_attempts}: {len(self.listings_data)} listings extracted", end='\r')
            
            # Check stopping conditions
            if no_new_listings_count >= 5:
                logger.info("No new listings after 5 scrolls - reached end")
                break
            
            if extracted_count >= self.max_listings:
                logger.info(f"Reached target of {self.max_listings} extracted listings")
                break
            
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content to load
            time.sleep(SCRAPER_SETTINGS['scroll_pause_time'])
            
            scroll_attempts += 1
        
        logger.info(f"Scrolling complete. Extracted {extracted_count} valid listings from {len(seen_item_ids)} unique URLs")
        return extracted_count
    
    def _get_item_id(self, container) -> str:
        """Helper to extract item ID from container."""
        try:
            href = container.get_attribute('href')
            if href and '/marketplace/item/' in href:
                return href.split('/marketplace/item/')[1].split('/')[0].split('?')[0]
        except:
            pass
        return None
    
    def _find_listing_containers(self) -> List:
        """
        Find all listing containers by looking for links to marketplace items.
        
        Returns:
            List of WebElement containers (the <a> tags themselves)
        """
        try:
            # Find all links that point to marketplace items
            # These are the actual listing links
            containers = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/marketplace/item/"]')
            
            if containers:
                logger.info(f"Found {len(containers)} listing links")
                return containers
            
            # Fallback: try other selectors
            for selector in SELECTORS['listing_container']:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        logger.debug(f"Found {len(containers)} containers with selector: {selector}")
                        return containers
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error finding containers: {e}")
        
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
        Extract all data from a single listing container using text-based approach.
        
        Args:
            container: WebElement containing listing
        
        Returns:
            Dictionary of listing data or None if extraction fails
        """
        try:
            # Get all text content
            text = container.text
            html = container.get_attribute('innerHTML')
            
            # Skip if this is a category menu or collection
            if 'Collection of Marketplace' in text or 'Shop by Category' in text:
                return None
            
            # Extract price (look for $ followed by numbers)
            import re
            price_match = re.search(r'\$[\d,]+', text)
            price_text = price_match.group(0) if price_match else None
            price = clean_price(price_text) if price_text else None
            
            # Extract mileage (look for numbers followed by K or miles)
            mileage_match = re.search(r'([\d,]+)\s*[Kk]?\s*(?:miles?|mi)', text, re.IGNORECASE)
            mileage_text = mileage_match.group(0) if mileage_match else None
            mileage = clean_mileage(mileage_text) if mileage_text else MISSING_DATA['mileage']
            
            # Extract listing URL - container IS the link now
            listing_url = None
            try:
                # Container is the <a> tag itself
                href = container.get_attribute('href')
                if href and 'marketplace' in href:
                    listing_url = href if href.startswith('http') else f"https://www.facebook.com{href}"
            except:
                pass
            
            # Extract images
            images = []
            try:
                imgs = container.find_elements(By.TAG_NAME, 'img')
                for img in imgs:
                    src = img.get_attribute('src')
                    if src and ('scontent' in src or 'fbcdn' in src):
                        images.append(src)
            except:
                pass
            
            # Extract title - look for year + make + model pattern
            title = None
            year = None
            make = None
            model = None
            
            # Split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != price_text]
            
            # Look for a line with year (4 digits starting with 19 or 20)
            for line in lines:
                year_match = re.search(r'(19\d{2}|20\d{2})', line)
                if year_match:
                    year = year_match.group(1)
                    # This line likely contains the car info
                    title = line
                    
                    # Try to extract make and model
                    # Pattern: YEAR MAKE MODEL [rest of text]
                    parts = line.split()
                    if len(parts) >= 3:
                        # Find year position
                        year_idx = None
                        for i, part in enumerate(parts):
                            if year in part:
                                year_idx = i
                                break
                        
                        if year_idx is not None and year_idx + 2 < len(parts):
                            make = parts[year_idx + 1]
                            model = parts[year_idx + 2]
                    break
            
            # If no year found, it might still be a valid listing
            # Don't filter out - let validation handle it
            if not year:
                logger.debug(f"No year found in text: {text[:100]}")
                # Don't return None yet - continue processing
            
            # Filter out non-cars (motorcycles, boats, etc.)
            non_car_keywords = [
                'seadoo', 'sea-doo', 'jet ski', 'boat', 'motorcycle', 'bike', 'atv', 'rv', 'camper', 
                'trailer', 'crf', 'ninja', 'harley', 'gsx-r', 'gsxr', 'kawasaki', 'yamaha r1', 'r6',
                'ducati', 'triumph', 'vtx', 'intruder', 'r1150', 'gs.5000', 'sportster', 'dyna',
                'cbr', 'yzf-r', 'yzf r', 'hayabusa', 'victory', 'sv650', 'fz6', 'spyder', 'johnny pag'
            ]
            title_lower = title.lower() if title else ''
            text_lower = text.lower() if text else ''
            
            # Check both title and full text for motorcycle keywords
            if any(keyword in title_lower or keyword in text_lower for keyword in non_car_keywords):
                logger.debug(f"Filtered out non-car: {title}")
                return None
            
            # Filter out junk data (like "1234 1234")
            if make and (make.isdigit() or make == '1234'):
                logger.debug(f"Filtered out junk listing: {title}")
                return None
            
            # Description is remaining text (preview only)
            description = text[:200] if text else MISSING_DATA['description']
            
            # Build listing dictionary
            listing = {
                'title': title,
                'price': price,
                'description': description,
                'mileage': mileage,
                'images': images,
                'listing_url': listing_url,
                'year': year,
                'make': make,
                'model': model,
            }
            
            # Validate required fields
            if not validate_listing(listing):
                return None
            
            return listing
        
        except Exception as e:
            logger.warning(f"Failed to extract listing data: {e}")
            logger.exception("Full error:")
            return None
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method.
        
        Returns:
            List of listing dictionaries
        """
        try:
            # Setup
            print(f"\n{'='*70}")
            print(f"  INITIALIZING BROWSER")
            print(f"{'='*70}")
            self.setup_driver()
            print(f"  [+] Browser ready\n")
            
            # Load page
            print(f"{'='*70}")
            print(f"  LOADING FACEBOOK MARKETPLACE")
            print(f"{'='*70}")
            if not self.load_page():
                print(f"\n  [!] Failed to load page")
                input("Press Enter to close browser and exit...")
                return []
            
            print(f"  [+] Page loaded\n")
            
            # Apply custom price range via UI if needed
            if self.min_price is not None or self.max_price is not None:
                print(f"  [setup] Applying price filters via UI...")
                self.set_custom_price_range()
                print(f"  [+] Price filters applied\n")
            
            # Wait for page to fully load
            print(f"  [wait] Waiting for page to render...")
            time.sleep(10)
            print(f"  [+] Page ready\n")
            
            # Scroll to load listings (extraction happens during scroll now)
            extracted_count = self._scroll_to_load_listings()
            
            print(f"\n[+] Extracted {len(self.listings_data)} listings\n")
            
            # Scrape full descriptions if enabled
            if self.scrape_descriptions and self.listings_data:
                print(f"\n{'='*70}")
                print(f"  EXTRACTING FULL DESCRIPTIONS")
                print(f"{'='*70}")
                print(f"  [time] Estimated time: {len(self.listings_data) * 9 / 60:.1f} minutes\n")
                batch_scrape_descriptions(self.driver, self.listings_data, delay=1.0)
                print(f"\n[+] Description extraction complete\n")
            
            # Apply make/model filters if specified
            if self.make_filter or self.model_filter:
                filtered = []
                for listing in self.listings_data:
                    make = listing.get('make', '').lower()
                    model = listing.get('model', '').lower()
                    
                    # Check make filter
                    if self.make_filter and self.make_filter not in make:
                        continue
                    
                    # Check model filter (only if specified and not 'any')
                    if self.model_filter and self.model_filter != 'any' and self.model_filter not in model:
                        continue
                    
                    filtered.append(listing)
                
                logger.info(f"Filtered to {len(filtered)} listings matching make/model criteria")
                return filtered
            
            return self.listings_data
        
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}", exc_info=True)
            logger.error("Keeping browser open for inspection")
            input("Press Enter to close browser and exit...")
            return []
        
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
