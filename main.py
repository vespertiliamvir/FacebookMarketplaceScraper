"""
Facebook Marketplace Car Scraper - Main Entry Point

User-friendly terminal interface for scraping car deals.
Designed to be simple enough for non-technical users.
"""

import sys
import logging
from colorama import Fore, Style, init
from tqdm import tqdm

from scraper.preferences import PreferencesManager
from scraper.facebook_scraper import FacebookMarketplaceScraper
from scraper.price_comparator import PriceComparator
from scraper.data_processor import DataProcessor
from scraper.csv_exporter import CSVExporter
from scraper.config import LOGGING_CONFIG

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Display welcome banner."""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}  FACEBOOK MARKETPLACE CAR SCRAPER - 2026 Edition")
    print(f"{Fore.CYAN}  Find the best car deals with AI-powered price comparison")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")


def print_step(step_num: int, total_steps: int, description: str):
    """Print step header."""
    print(f"\n{Fore.YELLOW}[Step {step_num}/{total_steps}] {description}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'-'*70}{Style.RESET_ALL}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def main():
    """Main execution flow."""
    try:
        # Banner
        print_banner()
        
        # Step 1: Setup preferences
        print_step(1, 5, "Configure Search Preferences")
        prefs_manager = PreferencesManager()
        
        if not prefs_manager.interactive_setup():
            print_info("Scraping cancelled by user.")
            return 0
        
        # Build Facebook URL
        facebook_url = prefs_manager.build_facebook_url()
        max_listings = prefs_manager.get('max_listings', 500)
        
        print_success(f"Configuration complete! Searching for up to {max_listings} listings")
        
        # Step 2: Scrape Facebook Marketplace
        print_step(2, 5, "Scraping Facebook Marketplace")
        print_info("Opening browser... This may take a moment.")
        print_info(f"Target URL: {facebook_url}")
        print_info("TIP: The browser will be visible. Don't close it manually!")
        
        scraper = FacebookMarketplaceScraper(facebook_url, max_listings)
        
        try:
            listings = scraper.scrape()
            
            if not listings:
                print_error("No listings found. Try adjusting your search parameters.")
                return 1
            
            print_success(f"Scraped {len(listings)} listings from Facebook Marketplace")
        
        except Exception as e:
            print_error(f"Scraping failed: {e}")
            logger.error(f"Scraping error: {e}", exc_info=True)
            return 1
        
        # Step 3: Fetch fair market prices
        print_step(3, 5, "Fetching Fair Market Prices")
        print_info("Comparing prices with Edmunds.com...")
        print_info("This may take a few minutes depending on number of listings.")
        
        with PriceComparator() as comparator:
            try:
                # Show progress bar
                print()
                with tqdm(total=len(listings), desc="Price lookups", unit="car") as pbar:
                    enriched_listings = []
                    for listing in listings:
                        # Enrich single listing
                        comparator.get_price_for_listing(listing)
                        enriched_listings.append(listing)
                        pbar.update(1)
                
                # Final enrichment pass to add parsed fields
                enriched_listings = comparator.enrich_listings(listings)
                
                with_prices = sum(1 for l in enriched_listings if l.get('fair_market_price'))
                print_success(f"Retrieved prices for {with_prices}/{len(enriched_listings)} listings")
            
            except Exception as e:
                print_error(f"Price comparison failed: {e}")
                logger.error(f"Price comparison error: {e}", exc_info=True)
                # Continue with listings even without prices
                enriched_listings = listings
        
        # Step 4: Process data
        print_step(4, 5, "Processing Data")
        print_info("Calculating deal ratios and sorting...")
        
        processor = DataProcessor()
        processed_listings = processor.process(enriched_listings)
        
        stats = processor.get_stats()
        print_success(f"Processed {stats['processed']} listings")
        if stats['filtered'] > 0:
            print_info(f"Filtered out {stats['filtered']} invalid listings")
        
        # Step 5: Export to CSV
        print_step(5, 5, "Exporting Results")
        print_info("Creating CSV file...")
        
        exporter = CSVExporter()
        
        try:
            output_file = exporter.export(processed_listings)
            
            if output_file:
                print_success(f"Results exported to: {output_file}")
                print()
                print(f"{Fore.CYAN}{'='*70}")
                print(f"{Fore.GREEN}✓ SCRAPING COMPLETE!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                print()
                print(f"{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
                print(f"  1. Open the CSV file: {output_file}")
                print(f"  2. Sort by 'Deal_Ratio' column (highest = best deals)")
                print(f"  3. Review top listings for potential purchases")
                print(f"  4. Use 'Listing_URL' column to view cars on Facebook")
                print()
                print(f"{Fore.CYAN}TIP: Listings with high deal ratios (>1.2) are priced")
                print(f"     significantly below market value!{Style.RESET_ALL}")
                print()
                
                return 0
            else:
                print_error("Export failed - no output file created")
                return 1
        
        except Exception as e:
            print_error(f"Export failed: {e}")
            logger.error(f"Export error: {e}", exc_info=True)
            return 1
    
    except KeyboardInterrupt:
        print()
        print_info("Scraping cancelled by user (Ctrl+C)")
        return 130
    
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
