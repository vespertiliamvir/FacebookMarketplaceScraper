
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from colorama import Fore, Style

from scraper.config import MASTER_PROFILE_DIR, USER_AGENTS

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Manages Facebook authentication, session validation, and interactive login flows.
    """
    
    @staticmethod
    def master_profile_exists() -> bool:
        """Check if the Master Profile directory exists and is populated."""
        if not os.path.exists(MASTER_PROFILE_DIR):
            return False
        # Check if directory has content (not just an empty folder)
        try:
            return len(os.listdir(MASTER_PROFILE_DIR)) > 0
        except:
            return False

    @staticmethod
    def validate_session(headless: bool = False) -> bool:
        """
        Launch a browser with the Master Profile to check if we are logged in.
        Returns True if logged in, False otherwise.
        """
        print(f"{Fore.CYAN}[*] Verifying session status...{Style.RESET_ALL}")
        
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={MASTER_PROFILE_DIR}")
        
        if headless:
            options.add_argument("--headless=new")
        
        # Standard anti-detection options
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-notifications")
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Go to Facebook
            driver.get("https://www.facebook.com")
            
            # Wait a bit for redirects
            time.sleep(3)
            
            # Check title or specific elements
            # Logged out usually has "Log In" or "Sign Up" in title or body
            # Logged in usually implies feed
            
            title = driver.title.lower()
            current_url = driver.current_url.lower()
            
            # Heuristics
            if "log in" in title or "login" in current_url:
                print(f"{Fore.RED}[!] Detected Login Page{Style.RESET_ALL}")
                return False
                
            # Check for specific logged-out elements
            try:
                driver.find_element(By.ID, "email")
                driver.find_element(By.ID, "pass")
                # If we found login fields, we are definitely not logged in
                print(f"{Fore.RED}[!] Detected Login Fields{Style.RESET_ALL}")
                return False
            except:
                pass
                
            print(f"{Fore.GREEN}[+] Session appears valid!{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            print(f"{Fore.RED}[!] Error validating session: {e}{Style.RESET_ALL}")
            return False
        finally:
            if driver:
                driver.quit()

    @staticmethod
    def interactive_login_flow():
        """
        Launches the browser for the user to log in manually.
        Blocks until the user signals completion or closes the browser.
        """
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"  FACEBOOK LOGIN REQUIRED")
        print(f"{'='*70}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}The scraper needs you to log in to Facebook to continue.")
        print(f"A browser window will open. Please log in and wait for the homepage.{Style.RESET_ALL}")
        
        os.makedirs(MASTER_PROFILE_DIR, exist_ok=True)
        
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={MASTER_PROFILE_DIR}")
        
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        print("Launching Login Browser...")
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get("https://www.facebook.com")
            
            print(f"\n{Fore.GREEN}[+] Browser Launched!{Style.RESET_ALL}")
            print("1. Log in to Facebook")
            print("2. Resolve any 2FA/Captchas")
            print("3. Wait for the news feed to load")
            print("4. Close the browser window when done OR press ENTER here")
            
            # Wait for user input or browser close
            try:
                input(f"\n{Fore.CYAN}Press ENTER after you have logged in successfully...{Style.RESET_ALL}")
            except:
                pass
                
            print(f"\n{Fore.GREEN}[+] Login flow completed.{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error launching browser: {e}{Style.RESET_ALL}")
        finally:
            try:
                driver.quit()
            except:
                pass
