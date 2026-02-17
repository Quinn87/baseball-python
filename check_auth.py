#!/usr/bin/env python3
"""
Quick status check for Fantrax private league authentication.
Run this to see if you're ready to connect to your league.
"""

import sys
from pathlib import Path


def check_auth_status():
    """Check authentication and dependencies status."""
    print("🔍 Checking Fantrax Authentication Status...\n")
    
    all_good = True
    
    # Check for cookie file
    cookie_file = Path("fantrax_login.cookie")
    if cookie_file.exists():
        print("✅ Authentication cookie found")
        print(f"   📁 {cookie_file.absolute()}")
        
        # Check cookie file size
        size = cookie_file.stat().st_size
        if size > 100:
            print(f"   📊 Cookie size: {size} bytes (looks good)")
        else:
            print(f"   ⚠️  Cookie size: {size} bytes (seems small, may be invalid)")
            all_good = False
    else:
        print("❌ No authentication cookie found")
        print("   Run: python setup_private_league.py")
        all_good = False
    
    print()
    
    # Check dependencies
    print("📦 Checking Dependencies...")
    
    deps = {
        'fantraxapi': 'Fantrax API client',
        'selenium': 'Browser automation (for auth)',
        'webdriver_manager': 'Chrome driver manager',
        'streamlit': 'Web interface',
        'pandas': 'Data handling',
        'pybaseball': 'Baseball data'
    }
    
    for package, description in deps.items():
        try:
            __import__(package)
            print(f"   ✅ {package:20s} - {description}")
        except ImportError:
            print(f"   ❌ {package:20s} - {description} (NOT INSTALLED)")
            if package in ['fantraxapi', 'selenium', 'webdriver_manager']:
                all_good = False
    
    print()
    
    # Final status
    if all_good:
        print("=" * 60)
        print("🎉 ALL SYSTEMS GO!")
        print("=" * 60)
        print("\nYou're ready to connect to your private league:")
        print("  1. streamlit run app.py")
        print("  2. Navigate to '🔗 Fantrax League'")
        print("  3. Enter your league ID: l5b4evbymg6tge5z")
        print("  4. Click 'Connect'")
    else:
        print("=" * 60)
        print("⚠️  SETUP INCOMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        
        if not cookie_file.exists():
            print("  1. Install auth dependencies:")
            print("     pip install selenium webdriver-manager")
            print("  2. Run authentication setup:")
            print("     python setup_private_league.py")
        else:
            print("  1. Install missing dependencies:")
            print("     pip install -r requirements.txt")
    
    print()


if __name__ == "__main__":
    check_auth_status()
