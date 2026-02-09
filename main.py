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
    print(f"{Fore.GREEN}[+] {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message."""
    print(f"{Fore.RED}[!] {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message."""
    print(f"{Fore.CYAN}[*] {message}{Style.RESET_ALL}")


def main():
    """Main execution flow."""
    try:
        # Banner
        print_banner()
        
        # Step 1: Setup preferences
        print_step(1, 5, "Configure Search Preferences")
        prefs_manager = PreferencesManager()
        
        # Check if we need to run login setup (Manual override via prefs)
        if not prefs_manager.interactive_setup():
            print_info("Scraping cancelled by user.")
            return 0
            
        # Handle manual "Run Login Setup" request from menu
        if prefs_manager.get('run_login_setup', False):
            from scraper.auth import AuthManager
            AuthManager.interactive_login_flow()
            prefs_manager.set('run_login_setup', False)
            prefs_manager.save_preferences()

        # ============================================================================
        # AUTHENTICATION CHECK (Auto-Login System)
        # ============================================================================
        from scraper.auth import AuthManager
        
        print_info("Verifying Facebook session before scraping...")
        
        # 1. Check if Master Profile exists and is valid
        if not AuthManager.master_profile_exists() or not AuthManager.validate_session(headless=True):
            print_error("Session invalid, expired, or missing.")
            print_info("Initiating automatic login flow to restore access...")
            
            # Launch interactive login
            AuthManager.interactive_login_flow()
            
            # Final validation
            if not AuthManager.validate_session(headless=True):
                print_error("Login verification failed.")
                print_info("You may continue, but the scraper will likely hit login walls.")
                if not prefs_manager._get_yes_no("Continue anyway? (y/n): ", default='n'):
                    return 0
            else:
                print_success("Session verified! Proceeding with scrape...")
        else:
            print_success("Session verified! Ready to scrape.")

        # ============================================================================
        # GRID SEARCH SETUP (Multi-Location)
        # ============================================================================
        raw_location = prefs_manager.get('location', 'atlanta')
        locations = [loc.strip() for loc in raw_location.split(',') if loc.strip()]
        
        max_listings = prefs_manager.get('max_listings', 500)
        num_workers = prefs_manager.get('num_workers', 1)
        
        print_success(f"Configuration complete! Target: {len(locations)} location(s), ~{max_listings} listings each.")
        
        # Step 2: Scrape Facebook Marketplace
        print_step(2, 5, "Scraping Facebook Marketplace")
        
        all_listings = []
        
        for i, loc in enumerate(locations):
            print(f"\n{Fore.MAGENTA}{'='*60}")
            print(f">>> GRID SEARCH [{i+1}/{len(locations)}]: {loc.upper()}")
            print(f"{'='*60}{Style.RESET_ALL}")
            
            # Prepare preferences for this location
            current_prefs = prefs_manager.preferences.copy()
            current_prefs['location'] = loc
            
            # Build URL for this specific location
            facebook_url = prefs_manager.build_facebook_url(location_override=loc)
            
            location_listings = []
            
            if num_workers > 1:
                print_info(f"Starting PARALLEL scraping in {loc} ({num_workers} workers)")
                try:
                    from scraper.parallel_manager import ParallelScraperManager
                    # Pass the location-specific prefs
                    manager = ParallelScraperManager(current_prefs, num_workers)
                    location_listings = manager.run()
                except Exception as e:
                    print_error(f"Parallel scraping failed for {loc}: {e}")
                    logger.error(f"Parallel scraping error ({loc}): {e}", exc_info=True)
            else:
                # Single Browser Mode
                print_info(f"Opening browser for {loc}...")
                print_info(f"Target URL: {facebook_url}")
                
                # Get filters
                make_filter = prefs_manager.get('make')
                model_filter = prefs_manager.get('model')
                scrape_descriptions = prefs_manager.get('scrape_descriptions', False)
                min_price = prefs_manager.get('min_price')
                max_price = prefs_manager.get('max_price')
                
                scraper = FacebookMarketplaceScraper(
                    url=facebook_url, 
                    max_listings=max_listings, 
                    make_filter=make_filter, 
                    model_filter=model_filter, 
                    scrape_descriptions=scrape_descriptions,
                    min_price=min_price,
                    max_price=max_price
                )
                
                try:
                    location_listings = scraper.scrape()
                except Exception as e:
                    print_error(f"Scraping failed for {loc}: {e}")
                    logger.error(f"Scraping error ({loc}): {e}", exc_info=True)
            
            if location_listings:
                print_success(f"Found {len(location_listings)} listings in {loc}")
                all_listings.extend(location_listings)
            else:
                print_error(f"No listings found in {loc}")
                
        # End of Grid Search Loop
        
        listings = all_listings
        
        if not listings:
            print_error("No listings found across all locations.")
            return 1
            
        print_success(f"Total aggregated listings: {len(listings)}")
        
        # Step 3: Price comparison (DISABLED - will be implemented later)
        print_step(3, 5, "Price Comparison")
        print_info("Price comparison is currently disabled (Edmunds blocking requests)")
        print_info("Skipping price lookup - proceeding with scraped data only")
        
        # Skip price comparison for now
        enriched_listings = listings
        print_success(f"Skipped price comparison for {len(enriched_listings)} listings")
        
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
                print(f"{Fore.GREEN}[+] SCRAPING COMPLETE!{Style.RESET_ALL}")
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
    # Required for PyInstaller/Auto-Py-To-Exe + Multiprocessing on Windows
    import multiprocessing
    multiprocessing.freeze_support()
    
    sys.exit(main())
