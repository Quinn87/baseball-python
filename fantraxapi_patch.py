"""
Patch for fantraxapi 1.0.x date parsing bug.
Fixes KeyError issues when initializing League and Roster objects.
"""

def patch_fantraxapi():
    """
    Apply monkey-patch to fix fantraxapi League and Roster initialization bugs.
    """
    try:
        from fantraxapi.objs.league import League
        from fantraxapi.objs.roster import Roster
        
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
        
        # Patch Roster class to handle missing scoring_dates
        original_roster_init = Roster.__init__
        
        def patched_roster_init(self, league, team_id, data):
            """Patched Roster init that handles missing scoring_dates."""
            from datetime import date
            from fantraxapi.objs.base import FantraxBaseObject
            
            # Initialize base object
            FantraxBaseObject.__init__(self, league, data[0])
            
            # Set team - try to use league.team() first, fallback to creating a minimal object
            try:
                self.team = league.team(team_id)
            except:
                # Create a minimal team-like object for compatibility
                class MinimalTeam:
                    def __init__(self, league_obj, tid):
                        self.league = league_obj
                        self.id = tid
                        self.name = tid  # Fallback to ID if name not available
                    
                    def __str__(self):
                        return self.name
                
                self.team = MinimalTeam(league, team_id)
            
            # Get period number
            self.period_number = int(self._data["displayedSelections"]["displayedPeriod"])
            
            # Handle missing scoring_dates gracefully
            if hasattr(league, 'scoring_dates') and self.period_number in league.scoring_dates:
                self.period_date = league.scoring_dates[self.period_number]
            else:
                # If scoring_dates is missing or doesn't have this period, use None
                self.period_date = None
            
            # Parse status totals
            lookup = {d["name"]: d for d in self._data["miscData"]["statusTotals"]}
            self.active = int(lookup["Active"]["total"]) if "Active" in lookup else 0
            self.active_max = int(lookup["Active"]["max"]) if "Active" in lookup else 0
            self.reserve = int(lookup["Reserve"]["total"]) if "Reserve" in lookup else 0
            self.reserve_max = int(lookup["Reserve"]["max"]) if "Reserve" in lookup else 0
            self.injured = int(lookup["Inj Res"]["total"]) if "Inj Res" in lookup else 0
            self.injured_max = int(lookup["Inj Res"]["max"]) if "Inj Res" in lookup else 0
            
            # Parse roster rows (rest of initialization)
            self.rows = []
            for stats_group, schedule_group in zip(self._data["tables"], data[1]["tables"]):
                stats_header = stats_group["header"]["cells"]
                schedule_header = schedule_group["header"]["cells"]
                for stats_row, schedule_row in zip(stats_group["rows"], schedule_group["rows"]):
                    if "posId" not in stats_row:
                        continue
                    
                    from fantraxapi.objs.roster import RosterRow
                    
                    # Build data dict for RosterRow
                    row_data = {
                        "posId": stats_row["posId"],
                        "future_games": {},
                        "total_fantasy_points": None,
                        "fantasy_points_per_game": None
                    }
                    
                    if "scorer" in stats_row or stats_row["statusId"] == "1":
                        if "scorer" in stats_row:
                            row_data["scorer"] = stats_row["scorer"]
                            
                            # Process future games
                            for header, cell in zip(schedule_header, schedule_row["cells"]):
                                if cell["content"] and "eventStr" in header and header["eventStr"]:
                                    key = header["shortName"]
                                    row_data["future_games"][key] = cell
                            
                            # Process stats
                            for header, cell in zip(stats_header, stats_row["cells"]):
                                if "Total" in header["shortName"]:
                                    row_data["total_fantasy_points"] = float(cell["content"]) if cell["content"] else None
                                elif "Avg" in header["shortName"]:
                                    row_data["fantasy_points_per_game"] = float(cell["content"]) if cell["content"] else None
                        
                        # Create RosterRow with correct signature (roster, data)
                        row = RosterRow(self, row_data)
                        self.rows.append(row)
        
        # Replace Roster.__init__
        Roster.__init__ = patched_roster_init
        
        return True
        
    except Exception as e:
        print(f"Patch error: {e}")
        return False
