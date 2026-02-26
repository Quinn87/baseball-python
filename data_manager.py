"""
Data Manager Module
Handles all data fetching, ID mapping, and API connections for the Dynasty Baseball app.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import requests
from datetime import datetime

# pybaseball imports
try:
    from pybaseball import (
        statcast_batter,
        statcast_pitcher,
        playerid_lookup,
        playerid_reverse_lookup,
        fg_batting_data,
        fg_pitching_data
    )
    PYBASEBALL_AVAILABLE = True
except ImportError as e:
    PYBASEBALL_AVAILABLE = False
    print(f"Warning: pybaseball not available ({e}). Install with: pip install pybaseball")


class DataManager:
    """Central data management class for all baseball data operations."""
    
    def __init__(self, id_map_path: str = None):
        """
        Initialize the DataManager.
        
        Args:
            id_map_path: Path to the PLAYERIDMAP.csv file
        """
        if id_map_path is None:
            id_map_path = Path(__file__).parent / 'data' / 'PLAYERIDMAP.csv'
        
        self.id_map_path = Path(id_map_path)
        self.id_map_df = None
        self.steamer_batters = None
        self.steamer_pitchers = None
        self.statcast_batters = None
        self.statcast_pitchers = None
        
    # ==================== ID MAPPING FUNCTIONS ====================
    
    def load_id_map(self) -> pd.DataFrame:
        """
        Load the SFBB Player ID Map CSV.
        
        Returns:
            DataFrame with player ID mappings
        """
        try:
            self.id_map_df = pd.read_csv(self.id_map_path)
            print(f"✓ Loaded {len(self.id_map_df)} players from ID map")
            return self.id_map_df
        except FileNotFoundError:
            print(f"✗ Error: ID map file not found at {self.id_map_path}")
            return pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading ID map: {str(e)}")
            return pd.DataFrame()
    
    def get_ids_by_fantrax(self, fantrax_id: str) -> Optional[Dict]:
        """
        Get MLBID and IDFANGRAPHS for a given FANTRAXID.
        
        Args:
            fantrax_id: The Fantrax ID to search for
            
        Returns:
            Dictionary with MLBID and IDFANGRAPHS, or None if not found
        """
        if self.id_map_df is None:
            self.load_id_map()
        
        if self.id_map_df.empty or not fantrax_id or pd.isna(fantrax_id):
            return None
        
        player = self.id_map_df[self.id_map_df['FANTRAXID'] == fantrax_id]
        
        if player.empty:
            return None
        
        player_row = player.iloc[0]
        
        # Extract and clean IDs
        mlbid = self._clean_id(player_row.get('MLBID'))
        idfangraphs = self._clean_id(player_row.get('IDFANGRAPHS'))
        
        return {
            'MLBID': mlbid,
            'IDFANGRAPHS': idfangraphs,
            'PLAYERNAME': player_row.get('PLAYERNAME'),
            'TEAM': player_row.get('TEAM'),
            'POS': player_row.get('POS')
        }
    
    def get_fantrax_id_by_name(self, player_name: str) -> Optional[str]:
        """
        Look up Fantrax ID by player name.
        
        Args:
            player_name: Name to search for
            
        Returns:
            Fantrax ID or None
        """
        if self.id_map_df is None:
            self.load_id_map()
        
        if self.id_map_df.empty:
            return None
        
        match = self.id_map_df[self.id_map_df['PLAYERNAME'].str.contains(player_name, case=False, na=False)]
        
        if not match.empty:
            return match.iloc[0]['FANTRAXID']
        return None
    
    @staticmethod
    def _clean_id(value) -> Optional[str]:
        """Convert ID to string, handling NaN and float values."""
        if pd.notna(value):
            if isinstance(value, float):
                return str(int(value))
            return str(value)
        return None
    
    # ==================== PYBASEBALL DATA FETCHING ====================
    
    def fetch_steamer_projections(self, year: Optional[int] = None, batter_proj: str = 'thebatx', pitcher_proj: str = 'atc') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch player projections from Fangraphs API.
        
        Args:
            year: Year for projections (defaults to current year)
            batter_proj: Projection system for batters (thebatx, steamer, atc, thebat, zips)
            pitcher_proj: Projection system for pitchers (atc, steamer, thebat, zips)
            
        Returns:
            Tuple of (batters_df, pitchers_df)
        """
        if year is None:
            year = datetime.now().year
        
        try:
            print(f"Fetching {year} projections from Fangraphs API...")
            
            # Fetch batter projections via Fangraphs API
            batter_url = f'https://www.fangraphs.com/api/projections?type={batter_proj}&stats=bat&pos=all'
            print(f"  Fetching batter projections ({batter_proj.upper()})...")
            batter_response = requests.get(batter_url, timeout=30)
            batter_response.raise_for_status()
            
            batters_data = batter_response.json()
            batters = pd.DataFrame(batters_data)
            
            if not batters.empty:
                self.steamer_batters = self._process_batter_projections(batters)
                print(f"✓ Loaded {len(self.steamer_batters)} batter projections")
            else:
                self.steamer_batters = pd.DataFrame()
                print("⚠ No batter projections returned")
            
            # Fetch pitcher projections via Fangraphs API
            pitcher_url = f'https://www.fangraphs.com/api/projections?type={pitcher_proj}&stats=pit&pos=all'
            print(f"  Fetching pitcher projections ({pitcher_proj.upper()})...")
            pitcher_response = requests.get(pitcher_url, timeout=30)
            pitcher_response.raise_for_status()
            
            pitchers_data = pitcher_response.json()
            pitchers = pd.DataFrame(pitchers_data)
            
            if not pitchers.empty:
                self.steamer_pitchers = self._process_pitcher_projections(pitchers)
                print(f"✓ Loaded {len(self.steamer_pitchers)} pitcher projections")
            else:
                self.steamer_pitchers = pd.DataFrame()
                print("⚠ No pitcher projections returned")
            
            return self.steamer_batters, self.steamer_pitchers
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching projections from Fangraphs API: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            print(f"✗ Error processing projections: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(), pd.DataFrame()
    
    def _process_batter_projections(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process batter projections and calculate custom metrics.
        
        League Scoring: R, RBI, OBP, SBN2 (SB - CS*2), XBS ((2B+3B+HR) + SH)
        Performance Peripherals: PA, Games, OPS, SLG, SB, CS
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Calculate custom scoring categories
        if '2B' in df.columns and '3B' in df.columns and 'HR' in df.columns:
            # XBS = (2B + 3B + HR) + SH
            df['XBS'] = df['2B'] + df['3B'] + df['HR']
            if 'SH' in df.columns:
                df['XBS'] += df['SH']
        
        if 'SB' in df.columns and 'CS' in df.columns:
            # SBN2 = SB - (CS * 2)
            df['SBN2'] = df['SB'] - (df['CS'] * 2)
        
        # Calculate performance peripherals
        if 'OBP' in df.columns and 'SLG' in df.columns:
            df['OPS'] = df['OBP'] + df['SLG']
        elif 'OPS' not in df.columns:
            # Calculate OPS from basic stats if not present
            if all(col in df.columns for col in ['H', 'BB', 'HBP', 'AB', 'SF']):
                df['OBP'] = (df['H'] + df['BB'] + df['HBP']) / (df['AB'] + df['BB'] + df['HBP'] + df['SF'])
            if all(col in df.columns for col in ['1B', '2B', '3B', 'HR', 'AB']):
                df['SLG'] = (df['1B'] + 2*df['2B'] + 3*df['3B'] + 4*df['HR']) / df['AB']
                df['OPS'] = df.get('OBP', 0) + df['SLG']
        
        return df
    
    def _process_pitcher_projections(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process pitcher projections and calculate custom metrics.
        
        League Scoring: K, ERA, WHIP, RPC (Relief Contribution), SPC (Starting Contribution)
        Performance Peripherals: IP, Wins, Losses, Saves, Holds, K%, BB%, K/BB%
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Calculate advanced metrics
        if 'SO' in df.columns and 'BF' in df.columns:
            # K% = K / Batters Faced
            df['K%'] = (df['SO'] / df['BF'] * 100).round(1)
        
        if 'BB' in df.columns and 'BF' in df.columns:
            # BB% = BB / Batters Faced
            df['BB%'] = (df['BB'] / df['BF'] * 100).round(1)
        
        if 'SO' in df.columns and 'BB' in df.columns:
            # K/BB ratio
            df['K/BB'] = (df['SO'] / df['BB'].replace(0, np.nan)).round(2)
        
        # Relief Contribution (RPC) - placeholder formula
        # Can be customized based on your league's specific calculation
        if 'SV' in df.columns and 'HLD' in df.columns and 'G' in df.columns and 'GS' in df.columns:
            relief_games = df['G'] - df['GS']
            df['RPC'] = df['SV'] + df['HLD'] + (relief_games * 0.1)  # Basic formula
        
        # Starting Contribution (SPC) - placeholder formula
        if 'GS' in df.columns and 'W' in df.columns and 'IP' in df.columns:
            df['SPC'] = df['GS'] * 0.5 + df['W'] * 1.5 + df['IP'] * 0.1  # Basic formula
        
        return df
    
    def fetch_statcast_data(self, year: Optional[int] = None, min_pa: int = 50, min_ip: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch Statcast leaderboards for in-season advanced metrics.
        
        Args:
            year: Season year (defaults to current)
            min_pa: Minimum plate appearances for batters
            min_ip: Minimum innings pitched for pitchers
            
        Returns:
            Tuple of (batters_df, pitchers_df)
        """
        if not PYBASEBALL_AVAILABLE:
            print("✗ pybaseball not available")
            return pd.DataFrame(), pd.DataFrame()
        
        if year is None:
            year = datetime.now().year
        
        try:
            print(f"Fetching Statcast data for {year}...")
            
            # Note: statcast_batter and statcast_pitcher require date ranges
            # This is a simplified version - you may need to adjust based on season dates
            start_date = f"{year}-03-20"
            end_date = f"{year}-10-01"
            
            # Fetch batter data
            print("  Fetching batter Statcast data...")
            batters = statcast_batter(start_date, end_date, min_pa=min_pa)
            self.statcast_batters = batters
            print(f"✓ Loaded {len(batters) if not batters.empty else 0} batters with Statcast data")
            
            # Fetch pitcher data
            print("  Fetching pitcher Statcast data...")
            pitchers = statcast_pitcher(start_date, end_date, min_ip=min_ip)
            self.statcast_pitchers = pitchers
            print(f"✓ Loaded {len(pitchers) if not pitchers.empty else 0} pitchers with Statcast data")
            
            return self.statcast_batters, self.statcast_pitchers
            
        except Exception as e:
            print(f"✗ Error fetching Statcast data: {str(e)}")
            print("  Note: Statcast data may not be available for future seasons or early in the season")
            return pd.DataFrame(), pd.DataFrame()
    
    # ==================== FANTRAX API INTEGRATION ====================
    
    def connect_fantrax_league(self, league_id: str, use_auth: bool = True) -> Optional['League']:
        """
        Connect to a Fantrax league using the fantraxapi library.
        
        Args:
            league_id: Your Fantrax league ID (found in league URL)
            use_auth: Whether to attempt authentication for private leagues
            
        Returns:
            League object if successful, None otherwise
        """
        try:
            from fantraxapi import League
            
            # Check for authentication (for private leagues)
            if use_auth:
                try:
                    from fantrax_auth import setup_fantrax_auth
                    from pathlib import Path
                    
                    cookie_file = Path("fantrax_login.cookie")
                    if cookie_file.exists():
                        print("🔐 Using saved authentication for private league...")
                        setup_fantrax_auth()
                        print("✓ Authentication enabled")
                except ImportError:
                    pass  # Auth module not available, continue without it
            
            print(f"Connecting to Fantrax league: {league_id}")
            league = League(league_id)
            print(f"✓ Connected to league: {league.name} ({league.year})")
            print(f"  Teams: {len(league.teams)}")
            # Note: scoring_periods() doesn't exist in fantraxapi 1.0.0
            
            return league
            
        except ImportError:
            print("✗ fantraxapi not installed. Run: pip install fantraxapi")
            return None
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Error connecting to Fantrax league: {error_msg}")
            
            # Check if it's a private league issue
            if "not logged in" in error_msg.lower() or "private" in error_msg.lower():
                print("  ⚠️  This appears to be a PRIVATE league")
                print("  Run the setup script: python setup_private_league.py")
            else:
                print("  Note: If league is private, run setup_private_league.py")
            
            return None
    
    def get_league_teams(self, league: 'League') -> list:
        """
        Get list of teams from a Fantrax league.
        
        In fantraxapi 1.0.0, league.teams is often empty, but we can get teams
        from the standings instead.
        
        Args:
            league: League object from connect_fantrax_league()
            
        Returns:
            List of Team objects
        """
        # Try league.teams first (might be empty in 1.0.0)
        if league.teams:
            return league.teams
        
        # Fall back to getting teams from standings
        try:
            standings = league.standings()
            teams = []
            for rank, record in standings.ranks.items():
                if hasattr(record, 'team'):
                    teams.append(record.team)
            return teams
        except Exception as e:
            print(f"Warning: Could not fetch teams from standings: {e}")
            return []
    
    def get_my_roster(self, league: 'League', team_name: str) -> pd.DataFrame:
        """
        Get your team's roster from Fantrax.
        
        Args:
            league: League object from connect_fantrax_league()
            team_name: Your team name (partial match works)
            
        Returns:
            DataFrame with your roster
        """
        try:
            # Get team from standings (league.team() doesn't work in 1.0.0)
            teams = self.get_league_teams(league)
            team = None
            for t in teams:
                if team_name.lower() in t.name.lower():
                    team = t
                    break
            
            if not team:
                print(f"✗ Team '{team_name}' not found in league")
                return pd.DataFrame()
            
            print(f"Fetching roster for {team.name}...")
            roster = team.roster()
            
            roster_data = []
            for row in roster.rows:
                if row.player:  # Skip empty roster spots
                    player_data = {
                        'Player_Name': row.player.name,
                        'Fantrax_ID': row.player.id,
                        'Position': row.player.pos_short_name,
                        'Team': row.player.team_short_name,
                        'Roster_Position': row.position.short_name if row.position else 'Unknown',
                        'Total_FP': row.total_fantasy_points,
                        'FP_Per_Game': row.fantasy_points_per_game,
                        'Injured': row.player.injured,
                        'Status': 'IR' if row.player.injured_reserve else ('Out' if row.player.out else ('DTD' if row.player.day_to_day else 'Active'))
                    }
                    roster_data.append(player_data)
            
            df = pd.DataFrame(roster_data)
            print(f"✓ Loaded {len(df)} players from {team.name}'s roster")
            
            # Merge with ID map if available
            if self.id_map_df is not None and not df.empty:
                df = self._enrich_fantrax_data(df)
            
            return df
            
        except Exception as e:
            print(f"✗ Error fetching roster: {str(e)}")
            return pd.DataFrame()
    
    def get_all_rosters(self, league: 'League') -> Dict[str, pd.DataFrame]:
        """
        Get all team rosters in the league.
        
        Args:
            league: League object from connect_fantrax_league()
            
        Returns:
            Dictionary of team_name -> roster DataFrame
        """
        all_rosters = {}
        
        try:
            teams = self.get_league_teams(league)
            for team in teams:
                print(f"  Fetching roster for {team.name}...")
                roster = team.roster()
                
                roster_data = []
                for row in roster.rows:
                    if row.player:
                        player_data = {
                            'Player_Name': row.player.name,
                            'Fantrax_ID': row.player.id,
                            'Position': row.player.pos_short_name,
                            'Team': row.player.team_short_name,
                            'Roster_Position': row.position.short_name if row.position else 'Unknown',
                            'Total_FP': row.total_fantasy_points,
                            'FP_Per_Game': row.fantasy_points_per_game,
                            'Injured': row.player.injured,
                            'Status': 'IR' if row.player.injured_reserve else ('Out' if row.player.out else ('DTD' if row.player.day_to_day else 'Active'))
                        }
                        roster_data.append(player_data)
                
                df = pd.DataFrame(roster_data)
                all_rosters[team.name] = df
            
            print(f"✓ Loaded rosters for {len(all_rosters)} teams")
            return all_rosters
            
        except Exception as e:
            print(f"✗ Error fetching all rosters: {str(e)}")
            return {}
    
    def get_all_claimed_players(self, league: 'League') -> pd.DataFrame:
        """
        Get a combined DataFrame of all claimed players across all teams.
        
        Args:
            league: League object from connect_fantrax_league()
            
        Returns:
            DataFrame with all claimed players and their fantasy team owners
        """
        try:
            print("Fetching all team rosters...")
            all_rosters = self.get_all_rosters(league)
            
            if not all_rosters:
                return pd.DataFrame()
            
            # Combine all rosters into one DataFrame with Fantasy_Team column
            combined_data = []
            for team_name, roster_df in all_rosters.items():
                if not roster_df.empty:
                    roster_df = roster_df.copy()
                    roster_df['Fantasy_Team'] = team_name
                    combined_data.append(roster_df)
            
            if not combined_data:
                return pd.DataFrame()
            
            claimed_df = pd.concat(combined_data, ignore_index=True)
            
            # Reorder columns to put Fantasy_Team first
            cols = ['Fantasy_Team'] + [col for col in claimed_df.columns if col != 'Fantasy_Team']
            claimed_df = claimed_df[cols]
            
            print(f"✓ Total claimed players: {len(claimed_df)} across {len(all_rosters)} teams")
            
            # Merge with ID map if available
            if self.id_map_df is not None and not claimed_df.empty:
                claimed_df = self._enrich_fantrax_data(claimed_df)
            
            return claimed_df
            
        except Exception as e:
            print(f"✗ Error fetching claimed players: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_available_players(self, league: 'League', position: Optional[str] = None) -> pd.DataFrame:
        """
        Get available free agents by comparing ID map with claimed players.
        
        Args:
            league: League object from connect_fantrax_league()
            position: Optional position filter (e.g., 'SP', 'OF', 'SS')
            
        Returns:
            DataFrame with available players (not on any roster)
        """
        try:
            # Load ID map if not already loaded
            if self.id_map_df is None:
                print("Loading ID map...")
                self.load_id_map()
            
            if self.id_map_df is None or self.id_map_df.empty:
                print("✗ ID map not available")
                return pd.DataFrame()
            
            # Get all claimed players
            print("Fetching claimed players...")
            claimed_df = self.get_all_claimed_players(league)
            
            if claimed_df.empty:
                print("⚠ No claimed players found, returning all players")
                available_df = self.id_map_df.copy()
            else:
                # Get list of claimed Fantrax IDs
                claimed_ids = set(claimed_df['Fantrax_ID'].dropna().unique())
                print(f"✓ Found {len(claimed_ids)} unique claimed players")
                
                # The ID map has Fantrax IDs with asterisks (*05u2v*) while
                # the roster data has them without (05u2v). We need to normalize.
                # Create a set with both formats for matching
                claimed_ids_normalized = set()
                for fid in claimed_ids:
                    claimed_ids_normalized.add(fid)
                    claimed_ids_normalized.add(f"*{fid}*")  # Add with asterisks
                
                # Filter ID map to exclude claimed players
                # Match on FANTRAXID column from ID map
                available_df = self.id_map_df[
                    ~self.id_map_df['FANTRAXID'].isin(claimed_ids_normalized)
                ].copy()
                
                print(f"✓ Found {len(available_df)} available players")
            
            # Filter by position if specified
            if position and 'POS' in available_df.columns:
                available_df = available_df[
                    available_df['POS'].str.contains(position, na=False, case=False)
                ]
                print(f"✓ Filtered to {len(available_df)} {position} players")
            
            # Select and rename relevant columns for display
            display_columns = []
            column_mapping = {}
            
            if 'PLAYERNAME' in available_df.columns:
                display_columns.append('PLAYERNAME')
                column_mapping['PLAYERNAME'] = 'Player_Name'
            if 'FANTRAXID' in available_df.columns:
                display_columns.append('FANTRAXID')
                column_mapping['FANTRAXID'] = 'Fantrax_ID'
            if 'POS' in available_df.columns:
                display_columns.append('POS')
                column_mapping['POS'] = 'Position'
            if 'TEAM' in available_df.columns:
                display_columns.append('TEAM')
                column_mapping['TEAM'] = 'MLB_Team'
            if 'MLBID' in available_df.columns:
                display_columns.append('MLBID')
                column_mapping['MLBID'] = 'MLB_ID'
            if 'IDFANGRAPHS' in available_df.columns:
                display_columns.append('IDFANGRAPHS')
                column_mapping['IDFANGRAPHS'] = 'Fangraphs_ID'
            
            # Keep only relevant columns
            if display_columns:
                available_df = available_df[display_columns].copy()
                available_df = available_df.rename(columns=column_mapping)
            
            # Sort by player name
            if 'Player_Name' in available_df.columns:
                available_df = available_df.sort_values('Player_Name')
            
            # Reset index
            available_df = available_df.reset_index(drop=True)
            
            return available_df
            
        except Exception as e:
            print(f"✗ Error fetching available players: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_free_agents(self, league: 'League', position: Optional[str] = None) -> pd.DataFrame:
        """
        Alias for get_available_players() for backward compatibility.
        
        Args:
            league: League object from connect_fantrax_league()
            position: Optional position filter (e.g., 'SP', 'OF', 'SS')
            
        Returns:
            DataFrame with free agent information
        """
        return self.get_available_players(league, position)
    
    # ==================== FANGRAPHS PROJECTIONS ====================
    
    def get_league_standings(self, league: 'League') -> pd.DataFrame:
        """
        Get current league standings.
        
        Args:
            league: League object from connect_fantrax_league()
            
        Returns:
            DataFrame with standings
        """
        try:
            standings = league.standings()
            
            standings_data = []
            for rank, record in standings.ranks.items():
                standings_data.append({
                    'Rank': rank,
                    'Team': record.team.name,
                    'Wins': record.win,
                    'Losses': record.loss,
                    'Ties': record.tie,
                    'Win_Pct': record.win_percentage,
                    'Points': record.points,
                    'Points_For': record.points_for,
                    'Points_Against': record.points_against,
                    'Streak': record.streak
                })
            
            df = pd.DataFrame(standings_data)
            print(f"✓ Loaded standings for {len(df)} teams")
            return df
            
        except Exception as e:
            print(f"✗ Error fetching standings: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_transactions(self, league: 'League', count: int = 50) -> pd.DataFrame:
        """
        Get recent league transactions.
        
        Args:
            league: League object from connect_fantrax_league()
            count: Number of transactions to retrieve
            
        Returns:
            DataFrame with transaction history
        """
        try:
            transactions = league.transactions(count=count)
            
            trans_data = []
            for trans in transactions:
                for player in trans.players:
                    trans_data.append({
                        'Date': trans.date,
                        'Team': trans.team.name,
                        'Player': player.name,
                        'Position': player.pos_short_name,
                        'Type': player.type,
                        'Status': 'Injured' if player.injured else 'Active'
                    })
            
            df = pd.DataFrame(trans_data)
            print(f"✓ Loaded {len(df)} transactions")
            return df
            
        except Exception as e:
            print(f"✗ Error fetching transactions: {str(e)}")
            return pd.DataFrame()
    
    def _enrich_fantrax_data(self, fantrax_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich Fantrax roster data with IDs from the ID map.
        
        Args:
            fantrax_df: DataFrame with Fantrax roster data
            
        Returns:
            Enhanced DataFrame with MLBID and IDFANGRAPHS
        """
        if self.id_map_df is None or fantrax_df.empty:
            return fantrax_df
        
        # Merge on Fantrax ID if available
        if 'Fantrax_ID' in fantrax_df.columns:
            enriched = fantrax_df.merge(
                self.id_map_df[['FANTRAXID', 'MLBID', 'IDFANGRAPHS', 'PLAYERNAME']],
                left_on='Fantrax_ID',
                right_on='FANTRAXID',
                how='left'
            )
            return enriched
        
        return fantrax_df
    
    def load_fantrax_roster_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load roster data from a Fantrax CSV export (fallback option).
        
        Args:
            csv_path: Path to exported CSV from Fantrax
            
        Returns:
            DataFrame with roster data
        """
        try:
            roster = pd.read_csv(csv_path)
            print(f"✓ Loaded roster with {len(roster)} players from CSV")
            
            # Try to match with ID map
            if self.id_map_df is not None and 'Player' in roster.columns:
                roster = self._match_roster_to_id_map(roster)
            
            return roster
        except Exception as e:
            print(f"✗ Error loading Fantrax roster CSV: {str(e)}")
            return pd.DataFrame()
    
    def _match_roster_to_id_map(self, roster_df: pd.DataFrame) -> pd.DataFrame:
        """
        Match roster players to ID map for enriched data.
        
        Args:
            roster_df: DataFrame from Fantrax export
            
        Returns:
            Enhanced DataFrame with IDs
        """
        # This would need to be customized based on Fantrax export format
        # Placeholder implementation
        return roster_df
    
    # ==================== DATA MERGING AND ENRICHMENT ====================
    
    def merge_projection_with_ids(self, projection_df: pd.DataFrame, player_type: str = 'batter') -> pd.DataFrame:
        """
        Merge projection data with ID map for complete player information.
        
        Args:
            projection_df: Steamer or other projection DataFrame
            player_type: 'batter' or 'pitcher'
            
        Returns:
            Merged DataFrame
        """
        if self.id_map_df is None:
            self.load_id_map()
        
        if projection_df.empty or self.id_map_df.empty:
            return projection_df
        
        # Try to merge on common fields (Name, IDFANGRAPHS, etc.)
        # This will depend on the structure of your projection data
        try:
            if 'IDfg' in projection_df.columns:
                # Merge on FanGraphs ID
                merged = projection_df.merge(
                    self.id_map_df[['IDFANGRAPHS', 'FANTRAXID', 'MLBID', 'PLAYERNAME', 'TEAM', 'POS']],
                    left_on='IDfg',
                    right_on='IDFANGRAPHS',
                    how='left'
                )
                return merged
            elif 'Name' in projection_df.columns:
                # Merge on player name (less reliable)
                merged = projection_df.merge(
                    self.id_map_df,
                    left_on='Name',
                    right_on='PLAYERNAME',
                    how='left'
                )
                return merged
        except Exception as e:
            print(f"Warning: Could not merge projections with ID map: {str(e)}")
        
        return projection_df
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def get_active_players(self) -> pd.DataFrame:
        """Get only active players from ID map."""
        if self.id_map_df is None:
            self.load_id_map()
        
        if 'ACTIVE' in self.id_map_df.columns:
            return self.id_map_df[self.id_map_df['ACTIVE'] == 'Y']
        return self.id_map_df
    
    def search_player(self, search_term: str) -> pd.DataFrame:
        """
        Search for players by name.
        
        Args:
            search_term: Name or partial name to search
            
        Returns:
            DataFrame of matching players
        """
        if self.id_map_df is None:
            self.load_id_map()
        
        if self.id_map_df.empty:
            return pd.DataFrame()
        
        mask = self.id_map_df['PLAYERNAME'].str.contains(search_term, case=False, na=False)
        return self.id_map_df[mask]


# ==================== STANDALONE HELPER FUNCTIONS ====================

def calculate_fantasy_points_batter(player_stats: pd.Series) -> float:
    """
    Calculate fantasy points for a batter based on league scoring.
    R, RBI, OBP, SBN2 (SB - CS*2), XBS ((2B+3B+HR) + SH)
    
    Args:
        player_stats: Series with player statistics
        
    Returns:
        Total fantasy points
    """
    points = 0.0
    
    # Add runs and RBI (assuming 1 point each, adjust as needed)
    points += player_stats.get('R', 0)
    points += player_stats.get('RBI', 0)
    
    # OBP contribution (scaled, adjust multiplier as needed)
    points += player_stats.get('OBP', 0) * 100  # Scale up OBP
    
    # SBN2 = SB - (CS * 2)
    points += player_stats.get('SBN2', 0)
    
    # XBS points
    points += player_stats.get('XBS', 0)
    
    return points


def calculate_fantasy_points_pitcher(player_stats: pd.Series) -> float:
    """
    Calculate fantasy points for a pitcher based on league scoring.
    K, ERA, WHIP, RPC (Relief Contribution), SPC (Starting Contribution)
    
    Args:
        player_stats: Series with player statistics
        
    Returns:
        Total fantasy points
    """
    points = 0.0
    
    # Strikeouts (positive)
    points += player_stats.get('SO', 0) * 1  # Adjust multiplier as needed
    
    # ERA (negative impact, lower is better)
    era = player_stats.get('ERA', 4.5)
    points -= (era - 3.0) * 5  # Penalty for ERA above 3.00
    
    # WHIP (negative impact, lower is better)
    whip = player_stats.get('WHIP', 1.3)
    points -= (whip - 1.0) * 10  # Penalty for WHIP above 1.00
    
    # Relief and Starting Contribution
    points += player_stats.get('RPC', 0)
    points += player_stats.get('SPC', 0)
    
    return points
