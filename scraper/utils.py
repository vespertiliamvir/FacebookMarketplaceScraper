"""
Utility functions for the Facebook Marketplace Scraper.

Contains helper functions for data cleaning, parsing, and validation.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price from text containing dollar signs and commas.
    
    Args:
        price_text: Raw price text (e.g., "$12,500", "12500", "$12.5k")
    
    Returns:
        Float price value, or None if parsing fails
    
    Examples:
        "$12,500" -> 12500.0
        "$12.5k" -> 12500.0
        "12500" -> 12500.0
        "invalid" -> None
    """
    if not price_text:
        return None
    
    try:
        # Remove dollar signs, commas, and spaces
        cleaned = re.sub(r'[$,\s]', '', price_text)
        
        # Handle "k" notation (e.g., "12.5k" -> 12500)
        if 'k' in cleaned.lower():
            cleaned = cleaned.lower().replace('k', '')
            return float(cleaned) * 1000
        
        return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse price: {price_text} - {e}")
        return None


def clean_mileage(mileage_text: str) -> Optional[int]:
    """
    Extract numeric mileage from text.
    
    Args:
        mileage_text: Raw mileage text (e.g., "50k miles", "50,000 mi", "50000")
    
    Returns:
        Integer mileage value, or None if parsing fails
    
    Examples:
        "50k miles" -> 50000
        "50,000 mi" -> 50000
        "50000" -> 50000
        "invalid" -> None
    """
    if not mileage_text:
        return None
    
    try:
        # Remove non-numeric characters except 'k'
        cleaned = re.sub(r'[^\d.k]', '', mileage_text.lower())
        
        # Handle "k" notation
        if 'k' in cleaned:
            cleaned = cleaned.replace('k', '')
            return int(float(cleaned) * 1000)
        
        return int(float(cleaned))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse mileage: {mileage_text} - {e}")
        return None


def parse_car_title(title: str) -> Dict[str, Optional[str]]:
    """
    Parse year, make, and model from car title.
    
    Args:
        title: Car listing title (e.g., "2015 Honda Civic LX")
    
    Returns:
        Dictionary with 'year', 'make', 'model' keys
    
    Examples:
        "2015 Honda Civic LX" -> {'year': '2015', 'make': 'Honda', 'model': 'Civic'}
        "Honda Civic 2015" -> {'year': '2015', 'make': 'Honda', 'model': 'Civic'}
    """
    result = {'year': None, 'make': None, 'model': None}
    
    if not title:
        return result
    
    # Extract 4-digit year
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
    if year_match:
        result['year'] = year_match.group(1)
    
    # Remove year from title for easier parsing
    title_no_year = re.sub(r'\b(19\d{2}|20\d{2})\b', '', title).strip()
    
    # Split into words
    words = title_no_year.split()
    
    # First word is usually make, second is usually model
    if len(words) >= 1:
        result['make'] = words[0]
    if len(words) >= 2:
        result['model'] = words[1]
    
    return result


def calculate_deal_ratio(asking_price: float, fair_market_price: float) -> Optional[float]:
    """
    Calculate deal ratio (higher is better deal).
    
    Args:
        asking_price: Price seller is asking
        fair_market_price: Fair market value from Edmunds/KBB
    
    Returns:
        Ratio of fair_market_price / asking_price, or None if invalid
    
    Examples:
        asking=10000, fair=12000 -> 1.2 (good deal, 20% below market)
        asking=12000, fair=10000 -> 0.83 (bad deal, 20% above market)
    """
    if not asking_price or not fair_market_price or asking_price <= 0:
        return None
    
    try:
        return round(fair_market_price / asking_price, 3)
    except (ZeroDivisionError, TypeError):
        return None


def format_image_urls(image_list: List[str]) -> str:
    """
    Format list of image URLs for CSV storage.
    
    Args:
        image_list: List of image URL strings
    
    Returns:
        Pipe-separated string of URLs
    
    Examples:
        ["url1", "url2"] -> "url1|url2"
        [] -> "N/A"
    """
    if not image_list:
        return "N/A"
    
    return "|".join(image_list)


def parse_image_urls(image_string: str) -> List[str]:
    """
    Parse pipe-separated image URLs back to list.
    
    Args:
        image_string: Pipe-separated URLs
    
    Returns:
        List of URL strings
    
    Examples:
        "url1|url2" -> ["url1", "url2"]
        "N/A" -> []
    """
    if not image_string or image_string == "N/A":
        return []
    
    return image_string.split("|")


def validate_listing(listing_data: Dict[str, Any]) -> bool:
    """
    Validate that listing has required fields.
    
    Args:
        listing_data: Dictionary of listing data
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['price', 'title']
    
    for field in required_fields:
        if field not in listing_data or listing_data[field] is None:
            logger.debug(f"Listing missing required field: {field}")
            return False
    
    return True


def get_timestamp() -> str:
    """
    Get current timestamp in standard format.
    
    Returns:
        Timestamp string (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length for display.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text with "..." if needed
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."
