"""
Patch for fantraxapi 1.0.x date parsing bug.
Fixes KeyError: 'Mar 25' issue when initializing League objects.
"""

def patch_fantraxapi():
    """
    Apply monkey-patch to fix fantraxapi League initialization bug.
    """
    try:
        from fantraxapi.objs.league import League
        
        # Save original __init__
        original_init = League.__init__
        
        def patched_init(self, league_id, session=None):
            """Patched init that handles date parsing errors."""
            from requests import Session
            from fantraxapi import api
            
            self.league_id = league_id  # fantraxapi uses league_id not id
            self.id = league_id  # Also set id for compatibility
            self.session = session or Session()
            self.logged_in = False
            self.name = None
            self.year = None
            self.start = None
            self.end = None
            self.scoring_dates = {}
            self._teams = []
            self._team_lookup = None
            
            # Try to call original reset_info, but catch KeyError
            try:
                self.reset_info()
            except KeyError as e:
                # Date parsing bug - manually initialize basic info
                try:
                    response = api.request(self, [api.Method.LEAGUE_INFO])
                    league_info = response.get("getLeagueInfo", {})
                    
                    self.name = league_info.get("leagueName", "Unknown")
                    self.year = league_info.get("season", "Unknown")
                    self.start = league_info.get("leagueStartDate")
                    self.end = league_info.get("leagueEndDate")
                    
                    # Initialize teams
                    from fantraxapi.objs.league import Team
                    teams_misc = league_info.get('teamsMisc', {})
                    for team_id, team_data in teams_misc.items():
                        team_obj = Team(self, team_id)
                        team_obj.name = team_data.get('name', '')
                        team_obj.short = team_data.get('abbrev', '')
                        self._teams.append(team_obj)
                except:
                    pass  # If this fails too, just have a partially initialized object
        
        # Replace __init__
        League.__init__ = patched_init
        
        # Add teams property with getter and setter if it doesn't exist properly
        def get_teams(self):
            return self._teams
        
        def set_teams(self, value):
            self._teams = value
        
        League.teams = property(get_teams, set_teams)
        
        return True
        
    except Exception:
        return False
