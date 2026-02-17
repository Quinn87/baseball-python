# Fantrax API Integration Guide

## Overview

Your Dynasty Baseball Manager now has **full Fantrax integration** using the `fantraxapi` library! You can now pull live data directly from your league.

## What You Can Access

✅ **Your Team's Roster** - All your players with stats and injury info  
✅ **All League Rosters** - Every team's roster in your league  
✅ **League Standings** - Current standings with W-L-T records  
✅ **Recent Transactions** - Waiver moves, adds, drops, trades  
✅ **League Information** - Teams, scoring periods, dates

## Quick Start

### 1. Install the Library

```bash
pip install fantraxapi
```

Or update all dependencies:

```bash
pip install -r requirements.txt
```

**For Private Leagues:** Also install authentication dependencies:

```bash
pip install selenium webdriver-manager
```

### 2. Authenticate (Private Leagues Only)

If your league is **private**, you need to authenticate first:

```bash
python setup_private_league.py
```

This will prompt for your Fantrax credentials and save authentication cookies.

**See [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) for detailed instructions.**

### 3. Find Your League ID

1. Go to your Fantrax league in a browser
2. Look at the URL:
   ```
   https://www.fantrax.com/fantasy/league/96igs4677sgjk7ol/home
                                          ^^^^^^^^^^^^^^^^
                                          This is your League ID
   ```
3. Copy the League ID (the alphanumeric code after `/league/`)

### 4. Connect in the App

1. Run the app: `streamlit run app.py`
2. Navigate to **"🔗 Fantrax League"** in the sidebar
3. Enter your League ID
4. Click **"Connect"**
5. Select your team from the dropdown

### 5. Explore Your Data

Once connected, you can:

- **👥 My Roster** - View and analyze your team
- **🏆 League Standings** - Check current standings
- **📜 Transactions** - See recent league activity

## Public vs Private Leagues

### Public Leagues (Easy Setup)

If your league is **public**, you can connect immediately with just the League ID. No authentication needed!

### Private Leagues (Requires Authentication)

If your league is **private**, you'll need to set up authentication:

1. Install additional dependencies:

   ```bash
   pip install selenium webdriver-manager
   ```

2. Add authentication code (see `data/API Documentation.txt` or [fantraxapi docs](https://fantraxapi.kometa.wiki/en/latest/intro.html#connecting-with-a-private-league))

3. You'll need your Fantrax username and password

## Available Data

### Roster Data Structure

When you load your roster, you get:

- **Player_Name** - Full name
- **Fantrax_ID** - Fantrax player identifier
- **Position** - Player positions (e.g., "SS,2B")
- **Team** - MLB team abbreviation
- **Roster_Position** - Fantasy roster slot (e.g., "SS", "UTIL", "BN")
- **Total_FP** - Total fantasy points this season
- **FP_Per_Game** - Fantasy points per game
- **Injured** - Boolean injury flag
- **Status** - "Active", "DTD", "Out", or "IR"

### Standings Data Structure

- **Rank** - Current standing
- **Team** - Team name
- **Wins/Losses/Ties** - Record
- **Win_Pct** - Win percentage
- **Points** - Total points
- **Points_For/Against** - Fantasy points scored/allowed
- **Streak** - Current streak (e.g., "W3", "L1")

### Transaction Data Structure

- **Date** - Transaction timestamp
- **Team** - Team that made the move
- **Player** - Player involved
- **Position** - Player position
- **Type** - Transaction type (add, drop, trade, etc.)
- **Status** - Player health status

## Features in the App

### 🔗 Fantrax League Page

- Enter League ID to connect
- View league information
- Select your team
- See all league teams
- Disconnect from league

### 👥 My Roster Page

- View complete roster with stats
- Filter by position
- See injury statuses
- Track fantasy points
- Download roster as CSV
- Refresh for latest data

### 🏆 League Standings Page

- Current standings table
- Win/loss records
- Points for/against
- Download standings as CSV
- Refresh for latest data

### 📜 Transactions Page

- Recent league activity
- Filter by team
- Configurable number of transactions (10-200)
- Download transaction history
- Refresh for latest data

## Integration with Other Features

### Combining Fantrax Data with Analysis

1. **Load your roster** from Fantrax
2. **Merge with projections** - Your roster players are automatically matched with:
   - Steamer projections
   - Statcast data
   - Player ID mappings (MLB ID, FanGraphs ID)
3. **Run dual-value analysis** on your players to find buy-low/sell-high candidates

### Workflow Example

```
1. Connect to Fantrax → Get your roster
2. Load Steamer Projections → Get rest-of-season outlook
3. Value Analysis → Identify your underperforming assets
4. Player Comparison → Evaluate trade targets
5. Check Transactions → See what other teams are doing
```

## Data Manager Functions

The `DataManager` class now includes:

```python
# Connect to league
league = dm.connect_fantrax_league("YOUR_LEAGUE_ID")

# Get your roster
my_roster_df = dm.get_my_roster(league, "Your Team Name")

# Get all rosters
all_rosters = dm.get_all_rosters(league)  # Returns dict of team -> DataFrame

# Get standings
standings_df = dm.get_league_standings(league)

# Get recent transactions
transactions_df = dm.get_recent_transactions(league, count=50)
```

## Troubleshooting

### "Failed to connect" Error

- ✅ Check your League ID is correct
- ✅ Ensure your league is **public** (or set up authentication for private)
- ✅ Verify you have `fantraxapi` installed: `pip show fantraxapi`

### "No team selected" Warning

- ✅ Go to **Fantrax League** page
- ✅ Select your team from the dropdown after connecting

### Empty Roster/Standings

- ✅ Click the **🔄 Refresh** button
- ✅ Check your internet connection
- ✅ Verify the league is active (not off-season)

### Private League Access

If you get authentication errors:

- Your league is likely private
- See the **Settings** page → **Private League Authentication**
- Follow the fantraxapi documentation for cookie-based auth

## API Rate Limits

The Fantrax API doesn't have published rate limits, but best practices:

- Don't spam the refresh button
- Cache data in session state (app does this automatically)
- Use the built-in refresh buttons rather than rerunning constantly

## Free Agents (Coming Soon)

The `fantraxapi` library doesn't directly expose available/free agent lists. Options:

1. **Web scraping** - Can be added if your league is public
2. **Manual export** - Export available players CSV from Fantrax
3. **Roster comparison** - Compare ID map with rostered players

## Resources

- **fantraxapi Documentation**: https://fantraxapi.kometa.wiki/
- **GitHub Repository**: https://github.com/meisnate12/FantraxAPI
- **Fantrax API Docs**: See `data/API Documentation.txt`

## Next Steps

Now that you have Fantrax integration:

1. ✅ Connect your league
2. ✅ Load your roster
3. ✅ Get Steamer projections
4. 🎯 Run value analysis on YOUR players
5. 💎 Find buy-low candidates among available players
6. 🔄 Compare trade targets with your roster
7. 📈 Track your standings progress

Enjoy your enhanced Dynasty Baseball Manager! ⚾

---

**Version**: 2.0 with Fantrax Integration  
**Last Updated**: February 2026
