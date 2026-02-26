"""
Fantrax Authentication Helper
Handles login for private Fantrax leagues using Selenium.
Based on official fantraxapi documentation:
https://fantraxapi.kometa.wiki/en/latest/intro.html#connecting-with-a-private-league-or-accessing-specific-endpoints
"""

import os
import pickle
import time

from requests import Session
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from fantraxapi import League, NotLoggedIn, api
from fantraxapi.api import Method

# Apply patch for date parsing bug in fantraxapi 1.0.x
try:
    from fantraxapi_patch import patch_fantraxapi
    patch_fantraxapi()
except:
    pass  # Patch not available or failed, continue anyway

# Configuration
COOKIE_FILEPATH = "fantrax_login.cookie"  # Name of the saved Cookie file

# Save the original request function
old_request = api.request


def new_request(league: "League", methods: list[Method] | Method) -> dict:
    """
    Intercepts fantraxapi requests to inject authentication.
    This replaces the original api.request function.
    """
    try:
        if not league.logged_in:
            add_cookie_to_session(league.session)  # Tries the login function when not logged in
        return old_request(league, methods)  # Run old function
    except NotLoggedIn:
        add_cookie_to_session(league.session, ignore_cookie=True)  # Adds/refreshes the cookie when NotLoggedIn is raised
        return new_request(league, methods)  # Rerun the request


def add_cookie_to_session(session: Session, ignore_cookie: bool = False) -> None:
    """
    Add Fantrax authentication cookies to a requests session.
    
    Args:
        session: The requests session to add cookies to
        ignore_cookie: If True, force re-login even if cookies exist
    """
    if not ignore_cookie and os.path.exists(COOKIE_FILEPATH):
        # Load existing cookies
        with open(COOKIE_FILEPATH, "rb") as f:
            for cookie in pickle.load(f):
                session.cookies.set(cookie["name"], cookie["value"])
        print(f"✅ Loaded cookies from {COOKIE_FILEPATH}")
    else:
        # Need to perform login with Selenium
        print("🔐 Logging in to Fantrax with Selenium...")
        
        # Load credentials
        username, password = load_credentials()
        
        service = Service(ChromeDriverManager().install())

        options = Options()
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
            with open(COOKIE_FILEPATH, "wb") as cookie_file:
                pickle.dump(cookies, cookie_file)
            
            print(f"✅ Login successful! Cookies saved to {COOKIE_FILEPATH}")

            # Add cookies to session
            for cookie in cookies:
                session.cookies.set(cookie["name"], cookie["value"])


def load_credentials():
    """
    Load Fantrax credentials from .env file or prompt user.
    
    Returns:
        tuple: (username, password)
    """
    # Try to load from environment or .env file
    username = os.getenv("FANTRAX_USERNAME")
    password = os.getenv("FANTRAX_PASSWORD")
    
    # Try to load from credentials file
    if not username or not password:
        creds_file = "fantrax_credentials.txt"
        if os.path.exists(creds_file):
            try:
                with open(creds_file, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        username = lines[0].strip()
                        password = lines[1].strip()
                        print(f"✅ Loaded credentials from {creds_file}")
            except Exception as e:
                print(f"⚠️  Could not load {creds_file}: {e}")
    
    # If still no credentials, raise error
    if not username or not password:
        raise ValueError(
            "Fantrax credentials not found!\n"
            "Please run setup_private_league.py first or set FANTRAX_USERNAME and FANTRAX_PASSWORD environment variables."
        )
    
    return username, password


def setup_fantrax_auth():
    """
    Setup automatic authentication for private Fantrax leagues.
    Call this once at the start of your app to enable authentication.
    """
    global api
    api.request = new_request  # Replace the old function with the new function
    print("✅ Fantrax authentication enabled")



# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("Fantrax Private League Authentication Test")
    print("="*60)
    print()
    
    # Setup authentication
    setup_fantrax_auth()
    
    # Test with a league
    league_id = input("Enter your private league ID to test: ").strip()
    
    if league_id:
        try:
            print(f"\n🔌 Connecting to league {league_id}...")
            my_league = League(league_id)
            
            print(f"✅ Successfully connected to: {my_league.name}")
            print(f"   League ID: {league_id}")
            print(f"   Season: {getattr(my_league, 'season', 'Unknown')}")
            
            # Try to access a private endpoint
            print("\n📋 Testing private endpoint (trade block)...")
            trade_block = my_league.trade_block()
            print(f"✅ Trade block accessed successfully!")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\nMake sure you've run setup_private_league.py first!")
    else:
        print("No league ID provided. Exiting.")
        print("\nTo use this authentication:")
        print("1. Run: python setup_private_league.py")
        print("2. Then use League(league_id) normally - authentication is automatic!")
