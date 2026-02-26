# Fantrax Authentication - Quick Reference

## New Simplified Authentication Method

Based on the official [fantraxapi documentation](https://fantraxapi.kometa.wiki/en/latest/intro.html#connecting-with-a-private-league-or-accessing-specific-endpoints), the authentication has been simplified.

## How to Use in Your Code

### Simple Usage (Recommended)

```python
from fantrax_auth import setup_fantrax_auth
from fantraxapi import League

# One-time setup - monkey-patches the fantraxapi to inject authentication
setup_fantrax_auth()

# Now just use League normally - authentication happens automatically!
league = League("your_league_id_here")

# Access any endpoint, including private ones
print(league.name)
print(league.rosters())
print(league.trade_block())  # Private endpoint
```

### How It Works

1. **Credential Storage**: Credentials are saved to `fantrax_credentials.txt` (or can use env vars)
2. **Cookie Management**: Login cookies saved to `fantrax_login.cookie`
3. **Auto-Injection**: The `setup_fantrax_auth()` function monkey-patches `fantraxapi.api.request`
4. **Auto-Refresh**: If cookies expire (NotLoggedIn error), automatically re-authenticates

### Files Used

- **`fantrax_credentials.txt`**: Stores username and password (plain text, in .gitignore)
- **`fantrax_login.cookie`**: Stores Fantrax session cookies (pickle format, in .gitignore)

### Environment Variables (More Secure)

Instead of storing credentials in a file, you can use environment variables:

```bash
export FANTRAX_USERNAME="your_email@example.com"
export FANTRAX_PASSWORD="your_password"
```

The authentication system checks for these first before looking for `fantrax_credentials.txt`.

## Initial Setup (One-Time)

### For End Users

Run the setup script:

```bash
python setup_private_league.py
```

This will:

1. Prompt for your credentials
2. Save them to `fantrax_credentials.txt`
3. Perform Selenium login and save cookies
4. Test the connection

### Manual Setup (Alternative)

1. Set environment variables:

   ```bash
   export FANTRAX_USERNAME="your_email"
   export FANTRAX_PASSWORD="your_password"
   ```

2. In your code:
   ```python
   from fantrax_auth import setup_fantrax_auth
   setup_fantrax_auth()  # Will trigger login on first API call
   ```

## Testing Connection

### Quick Test

```bash
python test_fantrax_private.py your_league_id
```

### In Python

```python
from fantrax_auth import setup_fantrax_auth
from fantraxapi import League

setup_fantrax_auth()

try:
    league = League("your_league_id")
    print(f"✅ Connected to: {league.name}")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Troubleshooting

### "Fantrax credentials not found!"

**Solution**: Run `python setup_private_league.py` or set environment variables

### NotLoggedIn Errors

**Solution**:

1. Delete `fantrax_login.cookie`
2. Run `python setup_private_league.py` again

### Chrome/WebDriver Issues

**Solution**: Make sure Chrome is installed. The script will automatically download the correct ChromeDriver.

## Migration from Old Authentication

The old class-based `FantraxAuth` has been replaced with a simpler function-based approach.

### Old Code (No Longer Works)

```python
from fantrax_auth import FantraxAuth

auth = FantraxAuth()
auth.load_cookies()
auth.setup_auto_auth()
```

### New Code (Current)

```python
from fantrax_auth import setup_fantrax_auth

setup_fantrax_auth()
```

## Security Best Practices

1. **Never commit credentials to git**: Both files are in `.gitignore`
2. **Use environment variables in production**: More secure than storing in files
3. **Rotate credentials periodically**: Good security practice
4. **Limit credential access**: Don't share these files

## API Reference

### `setup_fantrax_auth()`

Sets up automatic authentication by monkey-patching `fantraxapi.api.request`.

**Returns**: None

**Side Effects**:

- Patches the global `api.request` function
- Credentials loaded from env vars or `fantrax_credentials.txt`
- Cookies loaded from `fantrax_login.cookie` (or created via Selenium)

### `add_cookie_to_session(session, ignore_cookie=False)`

Manually add cookies to a requests session.

**Parameters**:

- `session` (Session): Requests session object
- `ignore_cookie` (bool): If True, force a fresh Selenium login

**Use Case**: Advanced users who want manual control over authentication

### `load_credentials()`

Load credentials from environment variables or `fantrax_credentials.txt`.

**Returns**: Tuple of (username, password)

**Raises**: ValueError if credentials not found

## Example: Data Manager Usage

```python
# In data_manager.py
def connect_to_fantrax(self, league_id, use_auth=True):
    from fantraxapi import League

    if use_auth:
        from fantrax_auth import setup_fantrax_auth
        setup_fantrax_auth()

    league = League(league_id)
    return league
```

This pattern is used throughout the app to enable seamless private league access.
