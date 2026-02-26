# Fantrax Private League Authentication Guide

## Overview

Your Fantrax league **l5b4evbymg6tge5z** is a **private league**, which requires authentication before the app can access rosters, standings, and transactions.

## Quick Setup (3 Steps)

### 1. Install Authentication Dependencies

```bash
pip install selenium webdriver-manager
```

This installs the Chrome WebDriver automation tools needed to log into Fantrax.

### 2. Run the Setup Script

```bash
python setup_private_league.py
```

This script will:

- Check that all dependencies are installed
- Prompt for your Fantrax username and password
- Save credentials to `fantrax_credentials.txt` (for automatic login)
- Open a Chrome browser window and log you in
- Save authentication cookies to `fantrax_login.cookie`
- Setup automatic authentication for the app

**Note:** Credentials are stored locally in `fantrax_credentials.txt` for automatic re-authentication when cookies expire.

### 3. Launch the App

```bash
streamlit run app.py
```

The app will automatically detect the saved authentication and connect to your private league!

## Testing Your Connection

After setup, you can test the connection at any time:

```bash
python test_fantrax_private.py l5b4evbymg6tge5z
```

This will verify that:

- ✓ Authentication cookies are loaded
- ✓ League connection successful
- ✓ Rosters can be retrieved
- ✓ Standings can be retrieved

## Troubleshooting

### "NotLoggedIn" Error

If you see authentication errors:

1. Delete `fantrax_login.cookie`
2. Run `python setup_private_league.py` again
3. Make sure you're entering the correct credentials

### Chrome Browser Issues

The setup script uses Chrome WebDriver. If you don't have Chrome installed:

- **Linux:** `sudo apt install chromium-browser` or `google-chrome-stable`
- **Mac:** Download from [google.com/chrome](https://www.google.com/chrome/)
- **Windows:** Download from [google.com/chrome](https://www.google.com/chrome/)

### Cookie Expired

Authentication cookies typically last several weeks. If they expire:

- Run `python setup_private_league.py` again to refresh

## How It Works

1. **Credential Storage:** Username/password saved to `fantrax_credentials.txt` for automatic re-authentication
2. **Selenium Login:** The script uses Chrome WebDriver to automate the Fantrax login process
3. **Cookie Extraction:** After successful login, it extracts authentication cookies
4. **Cookie Storage:** Cookies are saved to `fantrax_login.cookie` (pickle format)
5. **Auto-Injection:** When connecting to the league, cookies are automatically loaded and added to API requests
6. **Auto-Refresh:** If cookies expire, the system automatically re-authenticates using saved credentials

## Security Notes

- Credentials are stored locally in `fantrax_credentials.txt` (plain text)
- The `fantrax_login.cookie` file contains session tokens
- Keep both files private (they're in `.gitignore`)
- If compromised, delete both files and re-authenticate
- Consider using environment variables (`FANTRAX_USERNAME`, `FANTRAX_PASSWORD`) instead of the credentials file for better security

## Next Steps

Once authenticated, you'll have access to all Fantrax features in the app:

- **🔗 Fantrax League:** Connect to your league
- **👥 My Roster:** View your current players with dual-value analysis
- **🏆 League Standings:** See team rankings and stats
- **📜 Transactions:** Track recent adds, drops, and trades
- **📊 All Rosters:** Compare rosters across all teams

Happy managing! ⚾
