"""
Data processing module.

Handles cleaning, calculating deal ratios, and sorting listings.
"""

import logging
from typing import List, Dict, Any

from scraper.utils import calculate_deal_ratio
from scraper.config import MISSING_DATA

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Processes scraped listing data.
    
    Calculates deal ratios, sorts by best deals, and filters invalid entries.
    """
    
    def __init__(self):
        """Initialize data processor."""
        self.processed_count = 0
        self.filtered_count = 0
    
    def calculate_deal_ratios(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate deal ratio for each listing.
        
        Deal Ratio = Fair Market Price / Asking Price
        Higher ratio = better deal (car is priced below market value)
        
        Args:
            listings: List of listing dictionaries
        
        Returns:
            Listings with 'deal_ratio' field added
        """
        logger.info("Calculating deal ratios...")
        
        for listing in listings:
            asking_price = listing.get('price')
            fair_price = listing.get('fair_market_price')
            
            if asking_price and fair_price:
                ratio = calculate_deal_ratio(asking_price, fair_price)
                listing['deal_ratio'] = ratio
            else:
                listing['deal_ratio'] = None
                logger.debug(f"No deal ratio for: {listing.get('title', 'Unknown')} (missing price data)")
        
        # Count how many have ratios
        with_ratios = sum(1 for l in listings if l.get('deal_ratio') is not None)
        logger.info(f"Calculated {with_ratios}/{len(listings)} deal ratios")
        
        return listings
    
    def sort_by_deal_ratio(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort listings by deal ratio (best deals first).
        
        Listings without deal ratios are placed at the end.
        
        Args:
            listings: List of listing dictionaries
        
        Returns:
            Sorted listings
        """
        logger.info("Sorting listings by deal ratio...")
        
        # Separate listings with and without ratios
        with_ratios = [l for l in listings if l.get('deal_ratio') is not None]
        without_ratios = [l for l in listings if l.get('deal_ratio') is None]
        
        # Sort those with ratios (highest first = best deals)
        with_ratios.sort(key=lambda x: x['deal_ratio'], reverse=True)
        
        # Combine: best deals first, then listings without ratios
        sorted_listings = with_ratios + without_ratios
        
        logger.info(f"Sorted {len(with_ratios)} listings by deal ratio, {len(without_ratios)} without ratios at end")
        
        return sorted_listings
    
    def filter_invalid_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out listings with invalid or missing critical data.
        
        Critical fields: price, title
        
        Args:
            listings: List of listing dictionaries
        
        Returns:
            Filtered listings
        """
        logger.info("Filtering invalid listings...")
        
        valid_listings = []
        for listing in listings:
            # Check critical fields
            if not listing.get('price'):
                logger.debug(f"Filtered: No price - {listing.get('title', 'Unknown')}")
                self.filtered_count += 1
                continue
            
            if not listing.get('title'):
                logger.debug(f"Filtered: No title - Price: ${listing.get('price')}")
                self.filtered_count += 1
                continue
            
            valid_listings.append(listing)
        
        logger.info(f"Filtered {self.filtered_count} invalid listings, {len(valid_listings)} remain")
        
        return valid_listings
    
    def clean_data(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and normalize data fields.
        
        Args:
            listings: List of listing dictionaries
        
        Returns:
            Cleaned listings
        """
        logger.info("Cleaning data...")
        
        for listing in listings:
            # Ensure mileage has placeholder if missing
            if listing.get('mileage') is None:
                listing['mileage'] = MISSING_DATA['mileage']
            
            # Ensure description has placeholder if missing
            if not listing.get('description'):
                listing['description'] = MISSING_DATA['description']
            
            # Ensure images field exists
            if not listing.get('images'):
                listing['images'] = []
            
            # Ensure fair_market_price field exists
            if 'fair_market_price' not in listing:
                listing['fair_market_price'] = None
            
            # Ensure year/make/model fields exist
            for field in ['year', 'make', 'model']:
                if field not in listing:
                    listing[field] = None
        
        logger.info("Data cleaning complete")
        
        return listings
    
    def process(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Full processing pipeline.
        
        1. Filter invalid listings
        2. Clean data
        3. Calculate deal ratios
        4. Sort by deal ratio
        
        Args:
            listings: Raw listing data
        
        Returns:
            Processed and sorted listings
        """
        logger.info(f"Processing {len(listings)} listings...")
        
        # Filter invalid
        listings = self.filter_invalid_listings(listings)
        
        # Clean data
        listings = self.clean_data(listings)
        
        # Calculate deal ratios
        listings = self.calculate_deal_ratios(listings)
        
        # Sort by deal ratio
        listings = self.sort_by_deal_ratio(listings)
        
        self.processed_count = len(listings)
        logger.info(f"Processing complete: {self.processed_count} listings ready for export")
        
        return listings
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing stats
        """
        return {
            'processed': self.processed_count,
            'filtered': self.filtered_count,
        }
