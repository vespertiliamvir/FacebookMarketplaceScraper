"""
CSV export module.

Exports processed listings to CSV format with proper encoding and formatting.
"""

import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from scraper.config import OUTPUT_SETTINGS
from scraper.utils import format_image_urls, get_timestamp

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Exports listing data to CSV format.
    
    Uses pandas for robust CSV handling with proper encoding.
    """
    
    def __init__(self):
        """Initialize CSV exporter."""
        self.output_file = None
    
    def prepare_data_for_export(self, listings: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare listing data for CSV export.
        
        Converts to pandas DataFrame with proper column order and formatting.
        
        Args:
            listings: List of processed listing dictionaries
        
        Returns:
            pandas DataFrame ready for export
        """
        logger.info("Preparing data for CSV export...")
        
        # Convert to DataFrame
        df = pd.DataFrame(listings)
        
        # Format image URLs (list to pipe-separated string)
        if 'images' in df.columns:
            df['Image_URLs'] = df['images'].apply(format_image_urls)
        else:
            df['Image_URLs'] = 'N/A'
        
        # Rename columns to match output format
        column_mapping = {
            'deal_ratio': 'Deal_Ratio',
            'price': 'Price',
            'title': 'Title',
            'description': 'Description',
            'mileage': 'Mileage',
            'listing_url': 'Listing_URL',
            'fair_market_price': 'Fair_Market_Price',
            'year': 'Year',
            'make': 'Make',
            'model': 'Model',
            'seller_type': 'Seller_Type',
            'profile_age': 'Profile_Age',
            'is_business': 'Is_Business',
            'seller_rating': 'Seller_Rating',
            'score': 'Score',
            'green_flags': 'Green_Flags',
            'red_flags': 'Red_Flags',
            'notes': 'Notes',
        }
        
        df = df.rename(columns=column_mapping)
        
        # Select and order columns
        available_columns = [col for col in OUTPUT_SETTINGS['columns'] if col in df.columns]
        df = df[available_columns]
        
        # Format numeric columns
        if 'Deal_Ratio' in df.columns:
            df['Deal_Ratio'] = df['Deal_Ratio'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else 'N/A')
        
        if 'Price' in df.columns:
            df['Price'] = df['Price'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else 'N/A')
        
        if 'Fair_Market_Price' in df.columns:
            df['Fair_Market_Price'] = df['Fair_Market_Price'].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else 'N/A'
            )
        
        if 'Mileage' in df.columns:
            df['Mileage'] = df['Mileage'].apply(
                lambda x: f"{int(x):,}" if pd.notna(x) and x != 999999 else '999,999' if x == 999999 else 'N/A'
            )
        
        # Fill NaN values
        df = df.fillna('N/A')
        
        logger.info(f"Prepared {len(df)} rows for export")
        
        return df
    
    def generate_filename(self) -> str:
        """
        Generate timestamped filename.
        
        Returns:
            Filename string
        """
        timestamp = get_timestamp()
        filename = OUTPUT_SETTINGS['output_filename_template'].format(timestamp=timestamp)
        return filename
    
    def export(self, listings: List[Dict[str, Any]], output_file: str = None) -> str:
        """
        Export listings to CSV file.
        
        Args:
            listings: List of processed listing dictionaries
            output_file: Optional custom output filename
        
        Returns:
            Path to created CSV file
        """
        if not listings:
            logger.warning("No listings to export")
            return None
        
        # Generate filename if not provided
        if not output_file:
            output_file = self.generate_filename()
        
        self.output_file = output_file
        
        logger.info(f"Exporting {len(listings)} listings to {output_file}...")
        
        try:
            # Prepare data
            df = self.prepare_data_for_export(listings)
            
            # Export to CSV
            df.to_csv(
                output_file,
                index=False,
                encoding=OUTPUT_SETTINGS['csv_encoding'],
            )
            
            logger.info(f"Successfully exported to {output_file}")
            
            # Log summary
            self._log_export_summary(df)
            
            return output_file
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def _log_export_summary(self, df: pd.DataFrame) -> None:
        """
        Log summary of exported data.
        
        Args:
            df: Exported DataFrame
        """
        logger.info("=" * 60)
        logger.info("EXPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total listings: {len(df)}")
        
        # Count listings with deal ratios
        if 'Deal_Ratio' in df.columns:
            with_ratios = df[df['Deal_Ratio'] != 'N/A'].shape[0]
            logger.info(f"Listings with deal ratios: {with_ratios}")
        
        # Price range
        if 'Price' in df.columns:
            prices = df['Price'].apply(lambda x: float(x.replace('$', '').replace(',', '')) if x != 'N/A' else None)
            prices = prices.dropna()
            if len(prices) > 0:
                logger.info(f"Price range: ${prices.min():,.2f} - ${prices.max():,.2f}")
        
        # Top 5 deals
        if 'Deal_Ratio' in df.columns and 'Title' in df.columns:
            top_deals = df[df['Deal_Ratio'] != 'N/A'].head(5)
            if len(top_deals) > 0:
                logger.info("\nTop 5 Deals:")
                for idx, row in top_deals.iterrows():
                    logger.info(f"  {row['Deal_Ratio']} - {row['Title']}")
        
        logger.info("=" * 60)
