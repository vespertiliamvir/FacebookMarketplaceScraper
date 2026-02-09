"""
Preferences management module.

Handles loading, saving, and updating user preferences for the scraper.
Provides user-friendly terminal interface for configuration.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

from scraper.config import DEFAULT_SEARCH_PARAMS, PREFERENCES_FILE

# Initialize colorama for cross-platform colored output
init(autoreset=True)

logger = logging.getLogger(__name__)


class PreferencesManager:
    """Manages user preferences with terminal UI."""
    
    def __init__(self, preferences_file: str = PREFERENCES_FILE):
        """
        Initialize preferences manager.
        
        Args:
            preferences_file: Path to JSON file storing preferences
        """
        self.preferences_file = preferences_file
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Load preferences from file, or return defaults if file doesn't exist.
        
        Returns:
            Dictionary of preferences
        """
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                logger.info(f"Loaded preferences from {self.preferences_file}")
                return prefs
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load preferences: {e}. Using defaults.")
                return DEFAULT_SEARCH_PARAMS.copy()
        else:
            logger.info("No preferences file found. Using defaults.")
            return DEFAULT_SEARCH_PARAMS.copy()
    
    def save_preferences(self) -> bool:
        """
        Save current preferences to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            logger.info(f"Saved preferences to {self.preferences_file}")
            return True
        except IOError as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get preference value."""
        return self.preferences.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set preference value."""
        self.preferences[key] = value
    
    def display_current_preferences(self) -> None:
        """Display current preferences in a user-friendly format."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}CURRENT SEARCH PREFERENCES")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"{Fore.GREEN}Location Settings:{Style.RESET_ALL}")
        print(f"  Location: {self.preferences.get('location', 'N/A')}")
        print(f"  Search Radius: {self.preferences.get('radius_miles', 'N/A')} miles")
        
        print(f"\n{Fore.GREEN}Price Range:{Style.RESET_ALL}")
        print(f"  Minimum: ${self.preferences.get('min_price', 0):,}")
        print(f"  Maximum: ${self.preferences.get('max_price', 0):,}")
        
        print(f"\n{Fore.GREEN}Mileage Range:{Style.RESET_ALL}")
        print(f"  Minimum: {self.preferences.get('min_mileage', 0):,} miles")
        print(f"  Maximum: {self.preferences.get('max_mileage', 0):,} miles")
        
        print(f"\n{Fore.GREEN}Year Range:{Style.RESET_ALL}")
        print(f"  Minimum: {self.preferences.get('min_year', 'N/A')}")
        print(f"  Maximum: {self.preferences.get('max_year', 'N/A')}")
        
        print(f"\n{Fore.GREEN}Vehicle Filters:{Style.RESET_ALL}")
        make = self.preferences.get('make', '') or 'Any'
        model = self.preferences.get('model', '') or 'Any'
        print(f"  Make: {make}")
        print(f"  Model: {model}")
        
        print(f"\n{Fore.GREEN}Scraping Settings:{Style.RESET_ALL}")
        print(f"  Max Listings: {self.preferences.get('max_listings', 'N/A')}")
        
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    def interactive_setup(self) -> bool:
        """
        Interactive terminal UI for setting up preferences.
        User-friendly for non-technical users.
        
        Returns:
            True if user wants to proceed with scraping, False to exit
        """
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"{Fore.YELLOW}FACEBOOK MARKETPLACE CAR SCRAPER - SETUP")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
        
        # Check if preferences exist
        if os.path.exists(self.preferences_file):
            print(f"{Fore.GREEN}[+] Found saved preferences!{Style.RESET_ALL}\n")
            self.display_current_preferences()
            
            # Auto-run countdown
            print(f"{Fore.CYAN}Press ANY KEY to modify settings, or wait 3 seconds to auto-run...{Style.RESET_ALL}")
            
            import msvcrt
            import time
            
            start_time = time.time()
            key_pressed = False
            
            while time.time() - start_time < 3:
                if msvcrt.kbhit():
                    msvcrt.getch()  # Consume the key press
                    key_pressed = True
                    break
                time.sleep(0.1)
            
            if not key_pressed:
                print(f"\n{Fore.GREEN}[+] Auto-running with saved settings{Style.RESET_ALL}")
                return True
            
            # User pressed a key, show options
            print()
            choice = self._get_input(
                "Do you want to:\n"
                "  1. Use these settings\n"
                "  2. Modify settings\n"
                "  3. Reset to defaults\n"
                "  4. Exit\n"
                "  5. Run Login Setup (Fix Login Issues)\n"
                "Enter choice (1-5): ",
                valid_options=['1', '2', '3', '4', '5']
            )
            
            if choice == '1':
                return True
            elif choice == '3':
                self.preferences = DEFAULT_SEARCH_PARAMS.copy()
                self.save_preferences()
                print(f"\n{Fore.GREEN}[+] Reset to default settings{Style.RESET_ALL}")
                return self.interactive_setup()
            elif choice == '4':
                return False
            elif choice == '5':
                self.preferences['run_login_setup'] = True
                return True
            # If choice == '2', continue to modification
        else:
            print(f"{Fore.YELLOW}No saved preferences found. Let's set up your search!{Style.RESET_ALL}\n")
            print(f"{Fore.CYAN}TIP: You can press Enter to keep the default value shown in [brackets]{Style.RESET_ALL}\n")
        
        # Modify preferences
        self._modify_preferences_interactive()
        
        # Save and confirm
        self.save_preferences()
        print(f"\n{Fore.GREEN}[+] Preferences saved!{Style.RESET_ALL}")
        
        self.display_current_preferences()
        
        proceed = self._get_yes_no("Start scraping with these settings? (y/n): ")
        return proceed
    
    def _modify_preferences_interactive(self) -> None:
        """Interactive modification of preferences."""
        
        # Location
        print(f"\n{Fore.CYAN}--- LOCATION SETTINGS ---{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  * Tip: Enter multiple locations separated by commas (e.g. 'atlanta, marietta, roswell'){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  * The scraper will visit each location in sequence (Grid Search).{Style.RESET_ALL}")
        location = self._get_input(
            f"Enter location(s) [{self.preferences.get('location')}]: ",
            allow_empty=True
        )
        if location:
            self.preferences['location'] = location
        
        radius = self._get_number(
            f"Search radius in miles [{self.preferences.get('radius_miles')}]: ",
            allow_empty=True,
            min_val=1,
            max_val=500
        )
        if radius is not None:
            self.preferences['radius_miles'] = radius
        
        # Price range
        print(f"\n{Fore.CYAN}--- PRICE RANGE ---{Style.RESET_ALL}")
        min_price = self._get_number(
            f"Minimum price [${ self.preferences.get('min_price')}]: ",
            allow_empty=True,
            min_val=0
        )
        if min_price is not None:
            self.preferences['min_price'] = min_price
        
        max_price = self._get_number(
            f"Maximum price [${self.preferences.get('max_price')}]: ",
            allow_empty=True,
            min_val=self.preferences.get('min_price', 0)
        )
        if max_price is not None:
            self.preferences['max_price'] = max_price
        
        # Mileage range
        print(f"\n{Fore.CYAN}--- MILEAGE RANGE ---{Style.RESET_ALL}")
        min_mileage = self._get_number(
            f"Minimum mileage [{self.preferences.get('min_mileage')}]: ",
            allow_empty=True,
            min_val=0
        )
        if min_mileage is not None:
            self.preferences['min_mileage'] = min_mileage
        
        max_mileage = self._get_number(
            f"Maximum mileage [{self.preferences.get('max_mileage')}]: ",
            allow_empty=True,
            min_val=self.preferences.get('min_mileage', 0)
        )
        if max_mileage is not None:
            self.preferences['max_mileage'] = max_mileage
        
        # Year range
        print(f"\n{Fore.CYAN}--- YEAR RANGE ---{Style.RESET_ALL}")
        min_year = self._get_number(
            f"Minimum year [{self.preferences.get('min_year')}]: ",
            allow_empty=True,
            min_val=1900,
            max_val=2030
        )
        if min_year is not None:
            self.preferences['min_year'] = min_year
        
        max_year = self._get_number(
            f"Maximum year [{self.preferences.get('max_year')}]: ",
            allow_empty=True,
            min_val=self.preferences.get('min_year', 1900),
            max_val=2030
        )
        if max_year is not None:
            self.preferences['max_year'] = max_year
        
        # Make and model
        print(f"\n{Fore.CYAN}--- VEHICLE FILTERS (Optional) ---{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Leave blank to search all makes/models{Style.RESET_ALL}")
        
        make = self._get_input(
            f"Make (e.g., Honda, Toyota) [{self.preferences.get('make') or 'Any'}]: ",
            allow_empty=True
        )
        if make:
            self.preferences['make'] = make
        elif make == '':
            self.preferences['make'] = ''
        
        model = self._get_input(
            f"Model (e.g., Civic, Camry) [{self.preferences.get('model') or 'Any'}]: ",
            allow_empty=True
        )
        if model:
            self.preferences['model'] = model
        elif model == '':
            self.preferences['model'] = ''
        
        # Max listings
        print(f"\n{Fore.CYAN}--- SCRAPING SETTINGS ---{Style.RESET_ALL}")
        max_listings = self._get_number(
            f"Maximum listings to scrape [{self.preferences.get('max_listings')}]: ",
            allow_empty=True,
            min_val=1,
            max_val=5000
        )
        if max_listings is not None:
            self.preferences['max_listings'] = max_listings
        
        # Description scraping (with warning)
        print(f"\n{Fore.YELLOW}--- DETAILED DESCRIPTIONS (OPTIONAL) ---{Style.RESET_ALL}")
        print(f"{Fore.RED}[!] WARNING: Enabling this will significantly slow down scraping!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  * Adds 5-10 minutes for 500 listings")
        print(f"{Fore.YELLOW}  * Scraper must click into each listing to get full description")
        print(f"{Fore.YELLOW}  * Default preview text is usually sufficient for AI analysis{Style.RESET_ALL}\n")
        
        current_setting = self.preferences.get('scrape_descriptions', False)
        scrape_desc = self._get_yes_no(
            f"Scrape full descriptions? (y/n) [{'Yes' if current_setting else 'No'}]: ",
            default='n' if not current_setting else 'y'
        )
        self.preferences['scrape_descriptions'] = scrape_desc

        # Parallel Scraping
        print(f"\n{Fore.CYAN}--- PARALLEL SCRAPING ---{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  * Speed up scraping by running multiple browsers at once.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  * Each browser handles a portion of the price range.{Style.RESET_ALL}")
        
        num_workers = self._get_number(
            f"Number of parallel browsers (1-4) [{self.preferences.get('num_workers', 1)}]: ",
            allow_empty=True,
            min_val=1,
            max_val=4
        )
        if num_workers is not None:
            self.preferences['num_workers'] = num_workers
    
    def _get_input(self, prompt: str, valid_options: Optional[list] = None, allow_empty: bool = False) -> str:
        """
        Get user input with validation.
        
        Args:
            prompt: Prompt to display
            valid_options: List of valid options (case-insensitive), or None for any
            allow_empty: Whether empty input is allowed
        
        Returns:
            User input string
        """
        while True:
            user_input = input(prompt).strip()
            
            if not user_input and allow_empty:
                return user_input
            
            if not user_input and not allow_empty:
                print(f"{Fore.RED}Please enter a value.{Style.RESET_ALL}")
                continue
            
            if valid_options:
                if user_input.lower() in [opt.lower() for opt in valid_options]:
                    return user_input
                else:
                    print(f"{Fore.RED}Invalid option. Please choose from: {', '.join(valid_options)}{Style.RESET_ALL}")
                    continue
            
            return user_input
    
    def _get_number(self, prompt: str, allow_empty: bool = False, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[int]:
        """
        Get numeric input with validation.
        
        Args:
            prompt: Prompt to display
            allow_empty: Whether empty input is allowed
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        
        Returns:
            Integer value or None if empty and allowed
        """
        while True:
            user_input = input(prompt).strip()
            
            if not user_input and allow_empty:
                return None
            
            try:
                value = int(user_input.replace(',', ''))
                
                if min_val is not None and value < min_val:
                    print(f"{Fore.RED}Value must be at least {min_val}{Style.RESET_ALL}")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"{Fore.RED}Value must be at most {max_val}{Style.RESET_ALL}")
                    continue
                
                return value
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
    
    def _get_yes_no(self, prompt: str, default: str = None) -> bool:
        """
        Get yes/no input.
        
        Args:
            prompt: Prompt to display
            default: Default value ('y' or 'n') if user presses Enter
        
        Returns:
            True for yes, False for no
        """
        while True:
            response = input(prompt).strip().lower()
            
            # Handle empty input with default
            if not response and default:
                return default.lower() in ['y', 'yes']
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print(f"{Fore.RED}Please enter 'y' or 'n'{Style.RESET_ALL}")
    
    def build_facebook_url(self, location_override: str = None) -> str:
        """
        Build Facebook Marketplace URL from preferences.
        
        Uses Facebook's current search endpoint format with category_id.
        Note: Make/model filtering doesn't work via URL params anymore,
        so we'll filter results after scraping.
        
        Args:
            location_override: Optional location to use instead of preference default
        
        Returns:
            Complete Facebook Marketplace search URL
        """
        import urllib.parse
        
        base_url = "https://www.facebook.com/marketplace"
        location = location_override if location_override else self.preferences.get('location', '30068')
        
        # Clean up location string
        location = location.strip()
        
        # URL encode the location to handle spaces (e.g. "New York" -> "New%20York")
        # Facebook generally accepts city names with spaces if encoded, or zip codes.
        encoded_location = urllib.parse.quote(location)
        
        # Use search endpoint with vehicles category
        # Category ID 546583916084032 = Vehicles
        url = f"{base_url}/{encoded_location}/search/?"
        
        params = []
        
        # Price range
        if self.preferences.get('min_price'):
            params.append(f"minPrice={self.preferences['min_price']}")
        if self.preferences.get('max_price'):
            params.append(f"maxPrice={self.preferences['max_price']}")
        
        # Mileage range
        if self.preferences.get('min_mileage'):
            params.append(f"minMileage={self.preferences['min_mileage']}")
        if self.preferences.get('max_mileage'):
            params.append(f"maxMileage={self.preferences['max_mileage']}")
        
        # Year range
        if self.preferences.get('min_year'):
            params.append(f"minYear={self.preferences['min_year']}")
        if self.preferences.get('max_year'):
            params.append(f"maxYear={self.preferences['max_year']}")
        
        # Radius
        if self.preferences.get('radius_miles'):
            params.append(f"radius={self.preferences['radius_miles']}")
        
        # Vehicles category and query
        params.append("query=Vehicles")
        params.append("category_id=546583916084032")
        params.append("exact=false")
        
        # Note: Make/model filtering will be done post-scrape
        # Facebook's URL params for make/model don't work reliably anymore
        
        return url + "&".join(params)
