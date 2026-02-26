#!/usr/bin/env python3
"""
Setup script for private Fantrax league access.
This will log you in and save your credentials securely.
"""

import sys
import os
from pathlib import Path

# Check dependencies
try:
    from fantraxapi import League
    fantrax_ok = True
except ImportError:
    fantrax_ok = False

try:
    from selenium import webdriver
    selenium_ok = True
except ImportError:
    selenium_ok = False

def check_dependencies():
    """Check if all required packages are installed."""
    missing = []
    
    if not fantrax_ok:
        missing.append("fantraxapi")
    if not selenium_ok:
        missing.extend(["selenium", "webdriver-manager"])
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print()
        print("Install them with:")
        print("   pip install fantraxapi selenium webdriver-manager")
        print()
        return False
    
    return True


def main():
    """Main setup flow."""
    print()
    print("="*70)
    print("FANTRAX PRIVATE LEAGUE SETUP")
    print("="*70)
    print()
    print("This will authenticate you with Fantrax so you can access")
    print("your private league in the Dynasty Baseball Manager app.")
    print()
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Get credentials
    print("Enter your Fantrax credentials:")
    print("(Your credentials will be saved locally for automatic login)")
    print()
    username = input("Username/Email: ").strip()
    password = input("Password: ").strip()
    print()
    
    if not username or not password:
        print("❌ Both username and password are required")
        return False
    
    # Save credentials to file for future use
    creds_file = "fantrax_credentials.txt"
    try:
        with open(creds_file, "w") as f:
            f.write(f"{username}\n{password}\n")
        print(f"✅ Credentials saved to {creds_file}")
    except Exception as e:
        print(f"⚠️  Could not save credentials: {e}")
        print("   You'll need to re-enter them each time.")
    
    print()
    
    # Attempt login
    print("🔐 Logging in to Fantrax...")
    print("(This will open Chrome in the background)")
    print()
    
    try:
        from fantrax_auth import setup_fantrax_auth, add_cookie_to_session
        from requests import Session
        
        # Force a fresh login by creating a session and calling add_cookie_to_session
        # with ignore_cookie=True
        session = Session()
        add_cookie_to_session(session, ignore_cookie=True)
        
        # Now setup the authentication for future use
        setup_fantrax_auth()
        
        print()
        print("✅ Login successful!")
        
    except Exception as e:
        print()
        print(f"❌ Login failed: {e}")
        print("Please check your credentials and try again.")
        return False
    
    print()
    print("="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print()
    print("Your Fantrax login has been saved. You can now:")
    print()
    print("1. Test the connection:")
    print("   python test_fantrax_private.py l5b4evbymg6tge5z")
    print()
    print("2. Run the app:")
    print("   streamlit run app.py")
    print()
    print("3. Connect to your private league using the League ID:")
    print("   l5b4evbymg6tge5z")
    print()
    print("Your login session is saved in 'fantrax_login.cookie'")
    print("It will remain valid until you clear it or Fantrax expires it.")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print("⚠️  Setup cancelled")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
