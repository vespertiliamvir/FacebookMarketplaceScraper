"""
Configuration module for Facebook Marketplace Scraper.

Contains default settings, search parameters, and selector strategies.
All settings can be overridden by user preferences.
"""

import os
from typing import Dict, List, Any

# ============================================================================
# DEFAULT SEARCH PARAMETERS
# ============================================================================

DEFAULT_SEARCH_PARAMS = {
    'location': 'atlanta',
    'radius_miles': 50,  # Search radius from location
    'min_price': 250,
    'max_price': 55000,
    'min_mileage': 0,
    'max_mileage': 200000,
    'min_year': 1995,
    'max_year': 2026,
    'max_listings': 500,  # Stop after N listings
    'make': '',  # Empty = all makes
    'model': '',  # Empty = all models
    'scrape_descriptions': False,  # WARNING: Significantly slower (5-10 min extra for 500 listings)
    'num_workers': 1,  # Number of parallel browsers (1-4)
}

# ============================================================================
# SCRAPER SETTINGS
# ============================================================================

SCRAPER_SETTINGS = {
    'headless': False,  # User confirmed visible mode works better
    'scroll_pause_time': 3.0,  # Seconds to wait after each scroll (increased for more loading time)
    'page_load_timeout': 30,  # Seconds to wait for page load
    'element_wait_timeout': 10,  # Seconds to wait for elements
    'max_scroll_attempts': 200,  # Maximum number of scrolls (increased from 100)
    'scroll_increment': 1000,  # Pixels to scroll each time
}

# ============================================================================
# PRICE COMPARISON SETTINGS
# ============================================================================

PRICE_COMPARISON_SETTINGS = {
    'source': 'edmunds',  # Primary source: 'edmunds', 'kbb', or 'both'
    'request_delay': 2.5,  # Seconds between price lookup requests
    'cache_enabled': True,  # Cache results to avoid redundant lookups
    'timeout': 15,  # Seconds to wait for price lookup
}

# ============================================================================
# ROBUST SELECTOR STRATEGIES
# Multiple fallback selectors for each element to survive UI changes
# ============================================================================

SELECTORS = {
    # Container for each listing
    'listing_container': [
        'div[data-testid="marketplace-listing"]',
        'div[role="article"]',
        'div.x9f619.x78zum5.x1r8uery',
        'a[href*="/marketplace/item/"]',
    ],
    
    # Price field
    'price': [
        'span[data-testid="listing-price"]',
        'span.x193iq5w.xeuugli',
        'span:contains("$")',
        'div.x1xmf6yo span',
    ],
    
    # Title field
    'title': [
        'span[data-testid="listing-title"]',
        'h2 span',
        'div.x1lliihq span',
        'span.x1lliihq.x6ikm8r',
    ],
    
    # Mileage field
    'mileage': [
        'span:contains("miles")',
        'span:contains("mi")',
        'span:contains("k miles")',
        'div:contains("Mileage")',
    ],
    
    # Description field
    'description': [
        'div[data-testid="listing-description"]',
        'div.xz9dl7a',
        'span.x193iq5w.xeuugli.x13faqbe',
    ],
    
    # Image URLs
    'images': [
        'img[data-testid="listing-image"]',
        'img.x5yr21d',
        'img[src*="scontent"]',
        'div.x1n2onr6 img',
    ],
    
    # Listing URL
    'listing_url': [
        'a[href*="/marketplace/item/"]',
        'a[data-testid="listing-link"]',
    ],
}

# ============================================================================
# EDMUNDS CONFIGURATION
# ============================================================================

EDMUNDS_CONFIG = {
    'base_url': 'https://www.edmunds.com',
    'appraisal_path': '/appraisal-value/',
    'selectors': {
        'price_table': [
            'div.estimated-values.estimated-values-visible',
            'table.estimated-values-table',
        ],
        'price_cells': [
            'td.text-right',
            'td[class*="text-right"]',
        ],
    },
}

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

OUTPUT_SETTINGS = {
    'csv_encoding': 'utf-8',
    'timestamp_format': '%Y%m%d_%H%M%S',
    'output_filename_template': 'facebook_marketplace_scrape_{timestamp}.csv',
    'columns': [
        'Deal_Ratio',
        'Price',
        'Title',
        'Description',
        'Mileage',
        'Image_URLs',
        'Listing_URL',
        'Fair_Market_Price',
        'Year',
        'Make',
        'Model',
        'Seller_Type',
        'Profile_Age',
        'Is_Business',
        'Seller_Rating',
        'Score',
        'Green_Flags',
        'Red_Flags',
        'Notes',
    ],
}

# ============================================================================
# PREFERENCES FILE
# ============================================================================

PREFERENCES_FILE = 'scraper_preferences.json'

# ============================================================================
# BROWSER PROFILE SETTINGS
# ============================================================================

# Directory for the persistent "Master" profile where user logs in
MASTER_PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".facebook_scraper_master_profile")

# Base directory for temporary worker profiles
WORKER_PROFILE_BASE_DIR = os.path.join(os.path.expanduser("~"), ".fb_scraper_workers")

# ============================================================================
# MISSING DATA PLACEHOLDERS
# ============================================================================

MISSING_DATA = {
    'mileage': 999999,  # User requested this specific value
    'price': None,  # Skip listing if no price
    'title': None,  # Skip listing if no title
    'description': 'N/A',
    'images': 'N/A',
    'fair_market_price': 'N/A',
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'log_file': 'scraper.log',
}

# ============================================================================
# USER AGENT STRINGS (for anti-scraping)
# ============================================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]
