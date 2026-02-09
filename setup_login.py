
import sys
import os
import logging
from colorama import init, Fore, Style

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.auth import AuthManager

# Initialize colorama
init(autoreset=True)
logging.basicConfig(level=logging.INFO)

def setup_master_profile():
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  FACEBOOK LOGIN SETUP (MASTER PROFILE)")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    # Check if already exists
    if AuthManager.master_profile_exists():
        print(f"\n{Fore.YELLOW}[!] Master Profile already exists.")
        print(f"Running this will open the browser for you to check/update your login.{Style.RESET_ALL}")
    
    # Run the interactive flow
    AuthManager.interactive_login_flow()
    
    # Validate result
    print(f"\n{Fore.CYAN}[*] Verifying login status...{Style.RESET_ALL}")
    if AuthManager.validate_session(headless=True):
        print(f"\n{Fore.GREEN}[+] SUCCESS: Master Profile is logged in and ready!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] You can now run the scraper with parallel workers.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}[!] WARNING: Session verification failed.{Style.RESET_ALL}")
        print(f"{Fore.RED}[!] You may not be fully logged in, or Facebook is blocking the automated check.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}    Try running this script again and browsing manually for a bit longer.{Style.RESET_ALL}")

if __name__ == "__main__":
    setup_master_profile()
