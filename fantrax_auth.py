"""
Fantrax Authentication Helper
Handles login for private Fantrax leagues using Selenium.
"""

import os
import pickle
import time
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from requests import Session
    from fantraxapi import League, NotLoggedIn, api
    from fantraxapi.api import Method
    FANTRAX_AVAILABLE = True
    
    # Apply patch for date parsing bug in fantraxapi 1.0.x
    try:
        from fantraxapi_patch import patch_fantraxapi
        patch_fantraxapi()
    except:
        pass  # Patch not available or failed, continue anyway
        
except ImportError:
    FANTRAX_AVAILABLE = False


class FantraxAuth:
    """Handles authentication for private Fantrax leagues."""
    
    def __init__(self, cookie_file: str = "fantrax_login.cookie"):
        """
        Initialize the authenticator.
        
        Args:
            cookie_file: Path to save/load cookies
        """
        self.cookie_file = Path(cookie_file)
        self.username = None
        self.password = None
        self.logged_in = False
    
    def login(self, username: str, password: str, headless: bool = True):
        """
        Log in to Fantrax and save cookies.
        
        Args:
            username: Your Fantrax username/email
            password: Your Fantrax password
            headless: Run browser in headless mode (no visible window)
            
        Returns:
            True if successful
        """
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not installed. Run: pip install selenium webdriver-manager")
            return False
        
        self.username = username
        self.password = password
        
        print("🔐 Logging in to Fantrax...")
        
        try:
            service = Service(ChromeDriverManager().install())
            
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--window-size=1920,1600")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36")
            
            with webdriver.Chrome(service=service, options=options) as driver:
                driver.get("https://www.fantrax.com/login")
                
                # Wait for and fill username
                username_box = WebDriverWait(driver, 10).until(
                    expected_conditions.presence_of_element_located((By.XPATH, "//input[@formcontrolname='email']"))
                )
                username_box.send_keys(username)
                
                # Fill password
                password_box = WebDriverWait(driver, 10).until(
                    expected_conditions.presence_of_element_located((By.XPATH, "//input[@formcontrolname='password']"))
                )
                password_box.send_keys(password)
                password_box.send_keys(Keys.ENTER)
                
                # Wait for login to complete
                time.sleep(5)
                
                # Save cookies
                cookies = driver.get_cookies()
                with open(self.cookie_file, "wb") as f:
                    pickle.dump(cookies, f)
                
                print(f"✅ Login successful! Cookies saved to {self.cookie_file}")
                self.logged_in = True
                return True
        
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False
    
    def load_cookies(self) -> bool:
        """
        Load saved cookies.
        
        Returns:
            True if cookies exist and were loaded
        """
        if self.cookie_file.exists():
            print(f"✅ Found saved cookies: {self.cookie_file}")
            self.logged_in = True
            return True
        else:
            print("⚠️  No saved cookies found")
            return False
    
    def add_cookies_to_session(self, session: Session, ignore_saved: bool = False):
        """
        Add cookies to a requests session.
        
        Args:
            session: Requests session object
            ignore_saved: Force re-login even if cookies exist
        """
        if not ignore_saved and self.cookie_file.exists():
            with open(self.cookie_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    # Add domain if not present
                    domain = cookie.get("domain", ".fantrax.com")
                    session.cookies.set(
                        cookie["name"], 
                        cookie["value"],
                        domain=domain,
                        path=cookie.get("path", "/")
                    )
                print(f"✅ Loaded {len(cookies)} cookies into session")
        else:
            # Need to login
            if not self.username or not self.password:
                raise ValueError("Username and password required for login")
            
            self.login(self.username, self.password)
            self.add_cookies_to_session(session, ignore_saved=False)
    
    def setup_auto_auth(self):
        """
        Setup automatic authentication that intercepts API calls.
        This patches the fantraxapi.api.request function.
        
        Returns:
            True if setup successful
        """
        if not FANTRAX_AVAILABLE:
            print("❌ fantraxapi not installed")
            return False
        
        # Save original request function
        old_request = api.request
        auth = self
        
        def new_request(league: "League", methods: list[Method] | Method) -> dict:
            try:
                # Always inject cookies before request if not logged in
                if not league.logged_in and auth.cookie_file.exists():
                    auth.add_cookies_to_session(league.session)
                    league.logged_in = True  # Mark as logged in
                return old_request(league, methods)
            except NotLoggedIn:
                print("⚠️  NotLoggedIn error - attempting re-authentication...")
                auth.add_cookies_to_session(league.session, ignore_saved=True)
                league.logged_in = True
                return new_request(league, methods)
        
        # Replace the function
        api.request = new_request
        print("✅ Auto-authentication enabled")
        return True
    
    def clear_cookies(self):
        """Delete saved cookies."""
        if self.cookie_file.exists():
            self.cookie_file.unlink()
            print(f"✅ Deleted cookies: {self.cookie_file}")
            self.logged_in = False
        else:
            print("⚠️  No cookies to delete")


def quick_login_for_private_league(username: str, password: str, cookie_file: str = "fantrax_login.cookie"):
    """
    Quick setup function for private league access.
    
    Args:
        username: Your Fantrax username/email  
        password: Your Fantrax password
        cookie_file: Where to save cookies
        
    Returns:
        FantraxAuth object
    """
    auth = FantraxAuth(cookie_file)
    
    # Try to load existing cookies first
    if not auth.load_cookies():
        # Need to login
        print("🔑 No saved login found. Logging in...")
        if not auth.login(username, password):
            print("❌ Login failed!")
            return None
    
    # Setup auto-authentication
    auth.setup_auto_auth()
    
    return auth


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Fantrax Private League Authentication")
    print("="*60)
    print()
    
    if not SELENIUM_AVAILABLE:
        print("❌ Missing dependencies. Install with:")
        print("   pip install selenium webdriver-manager")
        exit(1)
    
    if not FANTRAX_AVAILABLE:
        print("❌ Missing fantraxapi. Install with:")
        print("   pip install fantraxapi")
        exit(1)
    
    # Get credentials
    print("Enter your Fantrax credentials:")
    username = input("Username/Email: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required")
        exit(1)
    
    print()
    
    # Login
    auth = quick_login_for_private_league(username, password)
    
    if auth:
        print()
        print("="*60)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*60)
        print()
        print("You can now connect to private leagues in the app.")
        print("Your login will be remembered until you clear cookies.")
        print()
        
        # Offer to test with a league
        test = input("Test with a league ID? (y/n): ").strip().lower()
        if test == 'y':
            from fantraxapi import League
            league_id = input("Enter League ID: ").strip()
            
            if league_id:
                print(f"\nConnecting to {league_id}...")
                try:
                    league = League(league_id)
                    print(f"✅ Successfully connected to: {league.name}")
                except Exception as e:
                    print(f"❌ Connection failed: {e}")
    else:
        print("❌ Authentication failed")
        exit(1)
