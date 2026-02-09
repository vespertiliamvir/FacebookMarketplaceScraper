"""
Description scraper module for Facebook Marketplace.

Handles scraping full descriptions from individual listing detail pages.
"""

import logging
import time
from typing import Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure INFO level messages show up

import re


def extract_seller_info(lines: list) -> Dict[str, Any]:
    """
    Extract seller profile information from page text lines.
    
    Helps identify private sellers vs car flippers/dealers.
    
    Red flags for flippers:
    - Multiple listings (5+)
    - Business listing flag
    - New Facebook account
    - Generic descriptions
    
    Good signs for private sellers:
    - Only 1-2 listings
    - Old Facebook account (joined years ago)
    - Personal descriptions
    - Good marketplace ratings
    """
    seller_info = {
        'seller_name': '',
        'profile_age': '',
        'is_business': False,
        'seller_rating': '',
        'listing_count': '',
        'seller_type': 'Unknown'  # Will be: 'Private', 'Possible Flipper', 'Dealer/Business'
    }
    
    full_text = ' '.join(lines)
    
    # Check for business listing flag
    if 'listing on behalf of a business' in full_text.lower():
        seller_info['is_business'] = True
        seller_info['seller_type'] = 'Dealer/Business'
    
    # Extract profile age (e.g., "Joined Facebook in 2015")
    for line in lines:
        if 'joined facebook in' in line.lower():
            match = re.search(r'Joined Facebook in (\d{4})', line, re.IGNORECASE)
            if match:
                seller_info['profile_age'] = match.group(1)
                break
    
    # Extract seller ratings/badges
    rating_keywords = ['highly rated', 'very responsive', 'fast shipper', 'reliable']
    ratings_found = []
    for line in lines:
        line_lower = line.lower()
        for keyword in rating_keywords:
            if keyword in line_lower:
                ratings_found.append(keyword.title())
    if ratings_found:
        seller_info['seller_rating'] = ', '.join(set(ratings_found))
    
    # Try to extract listing count (e.g., "See seller's other items (12)")
    for line in lines:
        if 'other items' in line.lower() or 'other listings' in line.lower():
            match = re.search(r'\((\d+)\)', line)
            if match:
                seller_info['listing_count'] = match.group(1)
                break
    
    # Determine seller type based on indicators
    if not seller_info['is_business']:
        listing_count = int(seller_info['listing_count']) if seller_info['listing_count'].isdigit() else 0
        profile_year = int(seller_info['profile_age']) if seller_info['profile_age'].isdigit() else 0
        current_year = 2026
        
        # Scoring system for flipper detection
        flipper_score = 0
        
        if listing_count >= 10:
            flipper_score += 3  # High indicator
        elif listing_count >= 5:
            flipper_score += 2  # Medium indicator
        elif listing_count >= 3:
            flipper_score += 1  # Low indicator
        
        if profile_year >= current_year - 1:  # Account less than 1 year old
            flipper_score += 2
        elif profile_year >= current_year - 2:  # Account 1-2 years old
            flipper_score += 1
        
        if flipper_score >= 3:
            seller_info['seller_type'] = 'Possible Flipper'
        elif flipper_score == 0 and profile_year > 0 and profile_year <= current_year - 3:
            seller_info['seller_type'] = 'Likely Private'
        else:
            seller_info['seller_type'] = 'Unknown'
    
    return seller_info


def scrape_listing_description(driver, listing_url: str, timeout: int = 10) -> tuple:
    """
    Scrape full description and seller info from a listing detail page.
    
    Args:
        driver: Selenium WebDriver instance
        listing_url: URL of the listing detail page
        timeout: Seconds to wait for page load
    
    Returns:
        Tuple of (description, seller_info_dict)
    """
    seller_info = {
        'seller_name': '',
        'profile_age': '',
        'is_business': False,
        'seller_rating': '',
        'listing_count': '',
        'seller_type': 'Unknown'
    }
    try:
        # Navigate to listing detail page
        driver.get(listing_url)
        time.sleep(3)  # Wait for page to load
        
        description = ""
        
        # Strategy 1: Click "See more" button if it exists to expand full description
        try:
            # Look for "See more" button/link and click it
            see_more_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'See more')]")
            
            if see_more_elements:
                try:
                    see_more_elements[0].click()
                    time.sleep(2)  # Wait longer for expansion
                except:
                    pass
        except Exception as e:
            pass
        
        # Strategy 2: Get all body text and parse it
        lines = []
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            full_text = body.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # Extract seller info from page text
            seller_info = extract_seller_info(lines)
            
            # Look for "Seller's description" or just "Description" header
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Check if this is a description header
                if ("seller's description" in line_lower or 
                    (line_lower == "description" and len(line) < 20)):
                    
                    # Collect all substantial lines after the header until we hit UI elements
                    description_parts = []
                    for j in range(i + 1, min(i + 20, len(lines))):
                        potential_desc = lines[j]
                        
                        # Stop if we hit UI elements or other sections
                        if any(word in potential_desc.lower() for word in ['message seller', 'share', 'save', 'report', 'listing details', 'vehicle information']):
                            break
                        
                        # Skip short lines, prices, and "See more" text
                        if (len(potential_desc) > 20 and 
                            not potential_desc.startswith('$') and
                            not potential_desc.endswith('miles') and
                            'see more' not in potential_desc.lower()):
                            
                            description_parts.append(potential_desc)
                    
                    # Join all parts to get full description
                    if description_parts:
                        description = ' '.join(description_parts).strip()
                        
                        # Remove common Facebook UI junk text
                        junk_phrases = [
                            'Location is approximate',
                            'Joined Facebook in',
                            'NYS RV & Camping Show',
                            'Send seller a message',
                            'See less',
                            'See more'
                        ]
                        for junk in junk_phrases:
                            description = description.replace(junk, '')
                        
                        # Clean up extra whitespace
                        description = ' '.join(description.split()).strip()
                        
                        # Remove Unicode object replacement characters
                        description = description.replace('\ufffc', '').strip()
                        
                        if description and len(description) > 30:
                            break
        except Exception as e:
            pass
        
        # Strategy 2: Look for spans containing car description text patterns
        if not description or len(description) < 30:
            try:
                # Find all spans with dir="auto" attribute
                spans = driver.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
                for span in spans:
                    text = span.text.strip()
                    # Look for text that mentions car-related terms and is substantial
                    if (len(text) > 50 and 
                        any(keyword in text.lower() for keyword in ['miles', 'engine', 'transmission', 'warranty', 'clean title', 'runs', 'drives', 'condition'])):
                        # Remove "See more" if present
                        description = text.replace("See more", "").replace("... ", "").strip()
                        logger.debug(f"Found description via car keywords: {description[:50]}...")
                        break
            except Exception as e:
                logger.debug(f"Strategy 2 (car keywords) failed: {e}")
        
        # Strategy 3: Look for any substantial text block
        if not description or len(description) < 30:
            try:
                spans = driver.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
                for span in spans:
                    text = span.text.strip()
                    # Get any text >50 chars that's not UI elements
                    if (len(text) > 50 and 
                        not text.startswith('$') and
                        not any(word in text.lower() for word in ['facebook', 'marketplace', 'message seller', 'share', 'save', 'report'])):
                        description = text.replace("See more", "").replace("... ", "").strip()
                        if description:
                            logger.debug(f"Found description via text block: {description[:50]}...")
                            break
            except Exception as e:
                logger.debug(f"Strategy 3 (text block) failed: {e}")
        
        # Strategy 4: Get body text and parse
        if not description or len(description) < 30:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                full_text = body.text
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                
                # Look for line after "Seller's description"
                for i, line in enumerate(lines):
                    if "seller's description" in line.lower() and i + 1 < len(lines):
                        potential_desc = lines[i + 1]
                        if len(potential_desc) > 30:
                            description = potential_desc.replace("See more", "").strip()
                            logger.debug(f"Found description in body text: {description[:50]}...")
                            break
            except Exception as e:
                logger.debug(f"Strategy 4 (body text) failed: {e}")
        
        return (description if description else "", seller_info)
    
    except Exception as e:
        logger.warning(f"Failed to scrape description from {listing_url}: {e}")
        return ("", seller_info)


def batch_scrape_descriptions(driver, listings: List[Dict[str, Any]], delay: float = 1.0) -> None:
    """
    Scrape full descriptions for multiple listings in batch.
    
    Updates the listings in-place with full descriptions.
    
    Args:
        driver: Selenium WebDriver instance
        listings: List of listing dictionaries
        delay: Delay between requests in seconds
    """
    total = len(listings)
    
    for i, listing in enumerate(listings, 1):
        listing_url = listing.get('listing_url')
        
        if not listing_url or listing_url == 'N/A':
            continue
        
        try:
            # Show clean progress indicator
            title = listing.get('title', 'Unknown')[:50]
            print(f"  [{i}/{total}] {title}...", end='\r')
            
            # Scrape full description and seller info
            full_description, seller_info = scrape_listing_description(driver, listing_url)
            
            if full_description:
                listing['description'] = full_description
            
            # Add seller info to listing
            listing['seller_type'] = seller_info.get('seller_type', 'Unknown')
            listing['profile_age'] = seller_info.get('profile_age', '')
            listing['is_business'] = seller_info.get('is_business', False)
            listing['seller_rating'] = seller_info.get('seller_rating', '')
            
            # Delay to avoid rate limiting
            if i < total:
                time.sleep(delay)
        
        except Exception as e:
            # Check for critical driver failures (window closed, disconnected)
            msg = str(e).lower()
            if 'no such window' in msg or 'target window already closed' in msg or 'disconnected' in msg:
                print(f"\n  [!] Browser window closed unexpectedly. Stopping description extraction.")
                logger.error("Browser window closed. Aborting batch description scrape.")
                break
                
            continue
    
    # Clear the progress line
    print(" " * 80, end='\r')
