"""
Test Fantrax API Connection
Quick script to test if you can connect to your Fantrax league.
"""

from fantraxapi import League

def test_connection(league_id):
    """
    Test connection to a Fantrax league.
    
    Args:
        league_id: Your Fantrax league ID
    """
    print("="*60)
    print("FANTRAX API CONNECTION TEST")
    print("="*60)
    print()
    
    print(f"Attempting to connect to league: {league_id}")
    print()
    
    try:
        # Connect to league
        league = League(league_id)
        
        print("✅ CONNECTION SUCCESSFUL!")
        print()
        print(f"League Name: {league.name}")
        print(f"Season Year: {league.year}")
        print(f"Start Date: {league.start_date}")
        print(f"End Date: {league.end_date}")
        print()
        
        # Show teams
        print(f"Teams ({len(league.teams)}):")
        for i, team in enumerate(league.teams, 1):
            print(f"  {i}. {team.name} ({team.short})")
        print()
        
        # Show scoring periods
        scoring_periods = league.scoring_periods()
        print(f"Scoring Periods: {len(scoring_periods)}")
        print()
        
        # Test getting a roster
        if league.teams:
            print("Testing roster fetch for first team...")
            first_team = league.teams[0]
            roster = first_team.roster()
            
            player_count = sum(1 for row in roster.rows if row.player)
            print(f"✅ Successfully fetched roster: {player_count} players")
            print()
            
            # Show first 3 players
            if player_count > 0:
                print("Sample players:")
                count = 0
                for row in roster.rows:
                    if row.player and count < 3:
                        print(f"  - {row.player.name} ({row.player.pos_short_name})")
                        count += 1
            print()
        
        # Test standings
        print("Testing standings fetch...")
        standings = league.standings()
        print(f"✅ Successfully fetched standings for {len(standings.ranks)} teams")
        print()
        
        print("="*60)
        print("ALL TESTS PASSED! ✅")
        print("="*60)
        print()
        print("You can now use this League ID in the Dynasty Manager app!")
        print(f"League ID: {league_id}")
        print()
        
        return True
        
    except ImportError:
        print("❌ ERROR: fantraxapi not installed")
        print()
        print("Install it with:")
        print("  pip install fantraxapi")
        print()
        return False
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {str(e)}")
        print()
        print("Possible issues:")
        print("  • League ID is incorrect")
        print("  • League is private (requires authentication)")
        print("  • Network connection problem")
        print()
        print("If your league is private, see FANTRAX_GUIDE.md")
        print("for authentication setup instructions.")
        print()
        return False


if __name__ == "__main__":
    print()
    print("Fantrax API Connection Tester")
    print("="*60)
    print()
    
    # Get league ID from user
    league_id = input("Enter your Fantrax League ID: ").strip()
    
    if not league_id:
        print("❌ No League ID provided")
        exit(1)
    
    print()
    
    # Test connection
    success = test_connection(league_id)
    
    if success:
        exit(0)
    else:
        exit(1)
