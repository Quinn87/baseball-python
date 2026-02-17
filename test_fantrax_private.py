"""
Test Fantrax API Connection for PRIVATE Leagues
This script tests if your authenticated session works.
"""

import sys
from pathlib import Path

def test_private_league(league_id):
    """
    Test connection to a private Fantrax league.
    
    Args:
        league_id: Your Fantrax league ID
    """
    print("="*60)
    print("PRIVATE FANTRAX LEAGUE CONNECTION TEST")
    print("="*60)
    print()
    
    # Check if cookie file exists
    cookie_file = Path("fantrax_login.cookie")
    if not cookie_file.exists():
        print("❌ No authentication found!")
        print()
        print("You need to authenticate first. Run:")
        print("   python setup_private_league.py")
        print()
        return False
    
    print("✅ Found saved authentication")
    print()
    
    try:
        from fantrax_auth import FantraxAuth
        from fantraxapi import League
        
        # Apply patch for fantraxapi bug
        try:
            from fantraxapi_patch import patch_fantraxapi
            patch_fantraxapi()
        except:
            pass
            
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print()
        print("Install with:")
        print("   pip install fantraxapi selenium webdriver-manager")
        print()
        return False
    
    # Setup authentication
    print("🔐 Setting up authenticated session...")
    auth = FantraxAuth()
    auth.load_cookies()
    auth.setup_auto_auth()
    print()
    
    # Try to connect
    print(f"Connecting to league: {league_id}")
    print()
    
    try:
        league = League(league_id)
        
        print("✅ CONNECTION SUCCESSFUL!")
        print()
        print(f"League Name: {league.name}")
        print(f"Season Year: {league.year}")
        print(f"Start Date: {league.start_date}")
        print(f"End Date: {league.end_date}")
        print()
        
        # Show teams (v1.0.x uses team_lookup instead of teams)
        teams = list(league.team_lookup.values())
        print(f"Teams ({len(teams)}):")
        for i, team in enumerate(teams, 1):
            print(f"  {i}. {team.name}")
        print()
        
        # Test getting a roster (private league specific)
        if teams:
            print("Testing roster fetch...")
            first_team_id = list(league.team_lookup.keys())[0]
            roster = league.team_roster(first_team_id)
            
            playercount = len([p for p in roster if p.get('player')])
            print(f"✅ Successfully fetched roster: {player_count} players")
            print()
            
            # Show first 3 players
            if player_count > 0:
                print("Sample players:")
                count = 0
                for player_data in roster:
                    if player_data.get('player') and count < 3:
                        player = player_data['player']
                        print(f"  - {player.get('name', 'Unknown')}")
                        count += 1
            print()
        
        # Test standings
        print("Testing standings fetch...")
        standings_data = league.standings()
        print(f"✅ Successfully fetched standings")
        print()
        
        # Show teams from standings
        if standings_data:
            print("Current Standings:")
            # standings_data structure may vary in v1.0.x
            if isinstance(standings_data, dict):
                for idx, (team_id, team_data) in enumerate(list(standings_data.items())[:3], 1):
                    team_name = league.team_lookup.get(team_id, {}).get('name', team_id)
                    print(f"  {idx}. {team_name}")
            else:
                print(" (Standings format varies in v1.0.x)")
        print()
        
        print("="*60)
        print("ALL TESTS PASSED! ✅")
        print("="*60)
        print()
        print("Your private league is now accessible!")
        print(f"League ID: {league_id}")
        print()
        print("You can now use this in the Dynasty Manager app:")
        print("   streamlit run app.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Print full traceback for debugging
        import traceback
        print("\n📋 Full error details:")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        
        print("\nPossible issues:")
        print("  • Your login session expired - run setup_private_league.py again")
        print("  • League ID is incorrect")
        print("  • Network connection problem")
        print("  • fantraxapi library version issue (try: pip install --upgrade fantraxapi)")
        print()
        return False


if __name__ == "__main__":
    print()
    
    if len(sys.argv) > 1:
        league_id = sys.argv[1]
    else:
        print("Private Fantrax League Connection Tester")
        print("="*60)
        print()
        league_id = input("Enter your Fantrax League ID: ").strip()
    
    if not league_id:
        print("❌ No League ID provided")
        sys.exit(1)
    
    print()
    
    # Test connection
    success = test_private_league(league_id)
    
    sys.exit(0 if success else 1)
