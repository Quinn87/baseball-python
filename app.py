"""
Dynasty Baseball Team Manager - Streamlit Dashboard
Tracks league scoring and advanced player performance for drafts, waiver adds, and trades.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Import custom modules
from data_manager import DataManager, calculate_fantasy_points_batter, calculate_fantasy_points_pitcher
from evaluator import PlayerEvaluator, compare_players

# Page configuration
st.set_page_config(
    page_title="Dynasty Baseball Manager",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'evaluator' not in st.session_state:
    st.session_state.evaluator = PlayerEvaluator()
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'fantrax_league' not in st.session_state:
    st.session_state.fantrax_league = None
if 'league_id' not in st.session_state:
    st.session_state.league_id = ""
if 'my_team_name' not in st.session_state:
    st.session_state.my_team_name = ""
if 'available_players' not in st.session_state:
    st.session_state.available_players = None


def load_initial_data():
    """Load ID map and initial data."""
    dm = st.session_state.data_manager
    
    with st.spinner('Loading player ID database...'):
        dm.load_id_map()
        st.session_state.data_loaded = True


def main():
    """Main application entry point."""
    
    # Sidebar navigation
    st.sidebar.title("⚾ Dynasty Manager")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🔗 Fantrax League",
            "📊 Player Lookup",
            "🎯 Projections & Stats",
            "💎 Value Analysis",
            "🔄 Player Comparison",
            "👥 My Roster",
            "🆓 Available Players",
            "🏆 League Standings",
            "📜 Transactions",
            "⚙️ Settings"
        ]
    )
    
    # Load initial data if not already loaded
    if not st.session_state.data_loaded:
        load_initial_data()
    
    st.sidebar.markdown("---")
    
    # Show league connection status
    if st.session_state.fantrax_league:
        st.sidebar.success(f"✓ Connected: {st.session_state.fantrax_league.name}")
        if st.session_state.my_team_name:
            st.sidebar.info(f"👤 Team: {st.session_state.my_team_name}")
    else:
        st.sidebar.warning("⚠ No league connected")
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**League Scoring:**\n"
        "- Batting: R, RBI, OBP, SBN2, XBS\n"
        "- Pitching: K, ERA, WHIP, RPC, SPC\n\n"
        "**Analysis:** Dual-value tracking"
    )
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔗 Fantrax League":
        show_fantrax_connection()
    elif page == "📊 Player Lookup":
        show_player_lookup()
    elif page == "🎯 Projections & Stats":
        show_projections()
    elif page == "💎 Value Analysis":
        show_value_analysis()
    elif page == "🔄 Player Comparison":
        show_player_comparison()
    elif page == "👥 My Roster":
        show_my_roster()
    elif page == "🆓 Available Players":
        show_available_players()
    elif page == "🏆 League Standings":
        show_league_standings()
    elif page == "📜 Transactions":
        show_transactions()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Main dashboard view."""
    st.title("⚾ Dynasty Baseball Team Manager")
    st.markdown("### Dashboard Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    dm = st.session_state.data_manager
    
    with col1:
        player_count = len(dm.id_map_df) if dm.id_map_df is not None else 0
        st.metric("Players in Database", f"{player_count:,}")
    
    with col2:
        active_count = len(dm.get_active_players()) if dm.id_map_df is not None else 0
        st.metric("Active Players", f"{active_count:,}")
    
    with col3:
        batters_count = len(dm.steamer_batters) if dm.steamer_batters is not None else 0
        st.metric("Batter Projections", f"{batters_count:,}")
    
    with col4:
        pitchers_count = len(dm.steamer_pitchers) if dm.steamer_pitchers is not None else 0
        st.metric("Pitcher Projections", f"{pitchers_count:,}")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Load Projections", use_container_width=True):
            with st.spinner("Fetching projections from Fangraphs API..."):
                try:
                    batters, pitchers = dm.fetch_steamer_projections()
                    if not batters.empty and not pitchers.empty:
                        st.success(f"✓ Loaded {len(batters)} batters, {len(pitchers)} pitchers")
                        st.info("📊 THE BAT X (batters) and ATC (pitchers) projections")
                    else:
                        st.warning("No data returned")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📊 Load Statcast Data", use_container_width=True):
            with st.spinner("Fetching Statcast data... (this may take a minute)"):
                try:
                    batters, pitchers = dm.fetch_statcast_data()
                    if not batters.empty or not pitchers.empty:
                        st.success(f"✓ Loaded Statcast data")
                    else:
                        st.info("No Statcast data available (may be off-season)")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            with st.spinner("Refreshing..."):
                dm.load_id_map()
                st.success("✓ Data refreshed")
                st.rerun()
    
    st.markdown("---")
    
    # Recent activity / quick stats
    st.subheader("📈 League Scoring Categories")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Batting Categories:**")
        st.markdown("- **R** - Runs")
        st.markdown("- **RBI** - Runs Batted In")
        st.markdown("- **OBP** - On-Base Percentage")
        st.markdown("- **SBN2** - Steals Net (SB - CS×2)")
        st.markdown("- **XBS** - Extra Base & Sac Hits")
    
    with col2:
        st.markdown("**Pitching Categories:**")
        st.markdown("- **K** - Strikeouts")
        st.markdown("- **ERA** - Earned Run Average")
        st.markdown("- **WHIP** - Walks + Hits per IP")
        st.markdown("- **RPC** - Relief Contribution")
        st.markdown("- **SPC** - Starting Contribution")


def show_player_lookup():
    """Player lookup and ID search page."""
    st.title("📊 Player Lookup")
    st.markdown("Search for players by name or Fantrax ID")
    
    dm = st.session_state.data_manager
    
    # Search options
    search_type = st.radio("Search by:", ["Player Name", "Fantrax ID"], horizontal=True)
    
    if search_type == "Player Name":
        search_term = st.text_input("Enter player name:", placeholder="e.g., Mike Trout")
        
        if search_term and len(search_term) >= 2:
            results = dm.search_player(search_term)
            
            if not results.empty:
                st.success(f"Found {len(results)} match(es)")
                
                # Display results
                display_cols = ['PLAYERNAME', 'TEAM', 'POS', 'FANTRAXID', 'MLBID', 'IDFANGRAPHS']
                available_cols = [col for col in display_cols if col in results.columns]
                st.dataframe(results[available_cols], use_container_width=True)
            else:
                st.warning(f"No players found matching '{search_term}'")
    
    else:  # Fantrax ID
        fantrax_id = st.text_input("Enter Fantrax ID:", placeholder="e.g., *01viz*")
        
        if fantrax_id:
            result = dm.get_ids_by_fantrax(fantrax_id)
            
            if result:
                st.success("Player found!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Player Name", result.get('PLAYERNAME', 'N/A'))
                    st.metric("Team", result.get('TEAM', 'N/A'))
                
                with col2:
                    st.metric("Position", result.get('POS', 'N/A'))
                    st.metric("MLB ID", result.get('MLBID', 'N/A'))
                
                with col3:
                    st.metric("FanGraphs ID", result.get('IDFANGRAPHS', 'N/A'))
            else:
                st.warning(f"No player found with Fantrax ID: {fantrax_id}")


def show_projections():
    """Projections and statistics page."""
    st.title("🎯 Projections & Statistics")
    st.caption("View player projections from Fangraphs and Statcast data")
    
    dm = st.session_state.data_manager
    
    tab1, tab2 = st.tabs(["Projections (Fangraphs)", "Statcast Data"])
    
    with tab1:
        st.subheader("Player Projections from Fangraphs")
        st.caption("📊 THE BAT X projections (batters) and ATC projections (pitchers)")
        
        player_type = st.radio("Player Type:", ["Batters", "Pitchers"], horizontal=True)
        
        if player_type == "Batters":
            if dm.steamer_batters is not None and not dm.steamer_batters.empty:
                st.dataframe(dm.steamer_batters, use_container_width=True, height=500)
                
                # Download button
                csv = dm.steamer_batters.to_csv(index=False)
                st.download_button(
                    "📥 Download Batter Projections",
                    csv,
                    "steamer_batters.csv",
                    "text/csv"
                )
            else:
                st.info("No batter projections loaded. Click 'Load Projections' on the Dashboard.")
        
        else:  # Pitchers
            if dm.steamer_pitchers is not None and not dm.steamer_pitchers.empty:
                st.dataframe(dm.steamer_pitchers, use_container_width=True, height=500)
                
                csv = dm.steamer_pitchers.to_csv(index=False)
                st.download_button(
                    "📥 Download Pitcher Projections",
                    csv,
                    "steamer_pitchers.csv",
                    "text/csv"
                )
            else:
                st.info("No pitcher projections loaded. Click 'Load Projections' on the Dashboard.")
    
    with tab2:
        st.subheader("Statcast Data")
        
        player_type = st.radio("Type:", ["Batters", "Pitchers"], horizontal=True, key="statcast_type")
        
        if player_type == "Batters":
            if dm.statcast_batters is not None and not dm.statcast_batters.empty:
                st.dataframe(dm.statcast_batters, use_container_width=True, height=500)
            else:
                st.info("No Statcast data loaded. Click 'Load Statcast Data' on the Dashboard.")
        else:
            if dm.statcast_pitchers is not None and not dm.statcast_pitchers.empty:
                st.dataframe(dm.statcast_pitchers, use_container_width=True, height=500)
            else:
                st.info("No Statcast data loaded. Click 'Load Statcast Data' on the Dashboard.")


def show_value_analysis():
    """Value analysis page for identifying buy-low and sell-high candidates."""
    st.title("💎 Dual-Value Analysis")
    st.markdown("Identify players whose peripherals suggest over/underperformance")
    
    dm = st.session_state.data_manager
    evaluator = st.session_state.evaluator
    
    analysis_type = st.radio("Analysis Type:", ["Buy-Low Candidates", "Sell-High Candidates", "Full Roster Evaluation"], horizontal=True)
    player_type = st.radio("Player Type:", ["Batters", "Pitchers"], horizontal=True, key="value_player_type")
    
    # Get appropriate data
    if player_type == "Batters":
        data = dm.steamer_batters
    else:
        data = dm.steamer_pitchers
    
    if data is None or data.empty:
        st.warning("No projection data loaded. Please load Steamer projections from the Dashboard first.")
        return
    
    min_confidence = st.slider("Minimum Confidence Level", 0.5, 1.0, 0.7, 0.05)
    
    if st.button("🔍 Run Analysis", type="primary"):
        with st.spinner("Analyzing players..."):
            try:
                if analysis_type == "Buy-Low Candidates":
                    results = evaluator.identify_buy_low_candidates(
                        data.head(100),  # Limit to top 100 for performance
                        player_type.lower()[:-1],  # Remove 's' from Batters/Pitchers
                        min_confidence
                    )
                    st.subheader("💎 Buy-Low Candidates (Underperforming vs Peripherals)")
                    
                elif analysis_type == "Sell-High Candidates":
                    results = evaluator.identify_sell_high_candidates(
                        data.head(100),
                        player_type.lower()[:-1],
                        min_confidence
                    )
                    st.subheader("⚠️ Sell-High Candidates (Overperforming vs Peripherals)")
                    
                else:  # Full roster evaluation
                    results = evaluator.evaluate_roster(
                        data.head(50),
                        player_type.lower()[:-1]
                    )
                    st.subheader("📊 Full Roster Evaluation")
                
                if not results.empty:
                    st.dataframe(results, use_container_width=True)
                    
                    # Download option
                    csv = results.to_csv(index=False)
                    st.download_button(
                        "📥 Download Analysis",
                        csv,
                        f"{analysis_type.lower().replace(' ', '_')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No players found matching the criteria.")
                    
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")


def show_player_comparison():
    """Player comparison tool."""
    st.title("🔄 Player Comparison")
    st.markdown("Compare two players side-by-side with dual-value analysis")
    
    dm = st.session_state.data_manager
    
    player_type = st.radio("Player Type:", ["Batters", "Pitchers"], horizontal=True, key="compare_type")
    
    # Get appropriate data
    if player_type == "Batters":
        data = dm.steamer_batters
    else:
        data = dm.steamer_pitchers
    
    if data is None or data.empty:
        st.warning("No projection data loaded. Load Steamer projections first.")
        return
    
    # Get player names
    if 'Name' in data.columns:
        player_names = sorted(data['Name'].dropna().unique().tolist())
    else:
        st.error("No 'Name' column found in data")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1 = st.selectbox("Player 1:", player_names, key="player1")
    
    with col2:
        player2 = st.selectbox("Player 2:", player_names, key="player2")
    
    if st.button("Compare Players", type="primary"):
        if player1 and player2:
            player1_stats = data[data['Name'] == player1].iloc[0]
            player2_stats = data[data['Name'] == player2].iloc[0]
            
            comparison = compare_players(player1_stats, player2_stats, player_type.lower()[:-1])
            
            st.markdown("---")
            
            # Display comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"⚾ {player1}")
                eval1 = comparison['player1']
                st.metric("Fantasy Score", f"{eval1.fantasy_score:.2f}")
                st.metric("Peripheral Score", f"{eval1.peripheral_score:.2f}")
                st.metric("Value Rating", eval1.value_rating)
                st.metric("Confidence", f"{eval1.confidence:.0%}")
                if eval1.flags:
                    st.markdown("**Flags:**")
                    for flag in eval1.flags:
                        st.markdown(f"- {flag}")
            
            with col2:
                st.subheader(f"⚾ {player2}")
                eval2 = comparison['player2']
                st.metric("Fantasy Score", f"{eval2.fantasy_score:.2f}")
                st.metric("Peripheral Score", f"{eval2.peripheral_score:.2f}")
                st.metric("Value Rating", eval2.value_rating)
                st.metric("Confidence", f"{eval2.confidence:.0%}")
                if eval2.flags:
                    st.markdown("**Flags:**")
                    for flag in eval2.flags:
                        st.markdown(f"- {flag}")
            
            st.markdown("---")
            st.subheader("📊 Recommendation")
            st.success(f"**Recommended Player:** {comparison['recommended']}")
            st.info(f"Fantasy Advantage: {comparison['fantasy_advantage']} | Peripheral Advantage: {comparison['peripheral_advantage']}")


def show_fantrax_connection():
    """Fantrax league connection page."""
    st.title("🔗 Connect to Fantrax League")
    st.markdown("Connect to your Fantrax dynasty league to access rosters, standings, and transactions.")
    
    dm = st.session_state.data_manager
    
    # Check authentication status
    from pathlib import Path
    cookie_file = Path("fantrax_login.cookie")
    
    if cookie_file.exists():
        st.success("🔐 Authenticated for private leagues")
    else:
        st.info("🔓 Public league access only. For private leagues, run: `python setup_private_league.py`")
    
    st.markdown("---")
    
    # Connection form
    st.subheader("League Connection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        league_id = st.text_input(
            "Fantrax League ID", 
            value=st.session_state.league_id,
            placeholder="e.g., 96igs4677sgjk7ol",
            help="Find this in your league URL: fantrax.com/fantasy/league/LEAGUE_ID/..."
        )
    
    with col2:
        st.markdown("####  ")  # Spacing
        if st.button("🔗 Connect", type="primary", use_container_width=True):
            if league_id:
                with st.spinner("Connecting to league..."):
                    league = dm.connect_fantrax_league(league_id)
                    if league:
                        st.session_state.fantrax_league = league
                        st.session_state.league_id = league_id
                        st.success(f"✓ Connected to {league.name}!")
                        st.rerun()
                    else:
                        st.error("Failed to connect. Check your league ID or if the league is public.")
            else:
                st.warning("Please enter a league ID")
    
    st.markdown("---")
    
    # Show league info if connected
    if st.session_state.fantrax_league:
        league = st.session_state.fantrax_league
        teams = dm.get_league_teams(league)
        
        st.subheader(f"📊 {league.name} ({league.year})")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Teams", len(teams))
        with col2:
            st.metric("Start Date", league.start_date.strftime("%m/%d/%Y") if league.start_date else "N/A")
        with col3:
            st.metric("End Date", league.end_date.strftime("%m/%d/%Y") if league.end_date else "N/A")
        
        st.markdown("---")
        
        # Team selection
        st.subheader("Select Your Team")
        team_names = [team.name for team in teams]
        my_team = st.selectbox(
            "Your Team:",
            [""] + team_names,
            index=0 if not st.session_state.my_team_name else team_names.index(st.session_state.my_team_name) + 1 if st.session_state.my_team_name in team_names else 0
        )
        
        if my_team:
            st.session_state.my_team_name = my_team
            st.success(f"✓ Set as your team: {my_team}")
        
        st.markdown("---")
        
        # Show all teams
        with st.expander("📋 View All Teams"):
            teams_data = []
            for team in teams:
                teams_data.append({
                    'Team Name': team.name,
                    'Short Name': team.short,
                    'Team ID': team.id
                })
            st.dataframe(pd.DataFrame(teams_data), use_container_width=True)
        
        # Disconnect button
        if st.button("❌ Disconnect League"):
            st.session_state.fantrax_league = None
            st.session_state.league_id = ""
            st.session_state.my_team_name = ""
            st.success("Disconnected from league")
            st.rerun()
    
    else:
        st.info("👆 Enter your Fantrax League ID above to get started")
        
        with st.expander("❓ How to find your League ID"):
            st.markdown("""
            1. Go to your Fantrax league
            2. Look at the URL in your browser
            3. The League ID is the code after `/league/`
            
            **Example:**
            ```
            https://www.fantrax.com/fantasy/league/96igs4677sgjk7ol/home
                                                    ^^^^^^^^^^^^^^^^
                                                    This is your League ID
            ```
            
            **Note:** Your league must be **public** to connect without authentication.
            For private leagues, see Settings for authentication options.
            """)


def show_my_roster():
    """Display and analyze your team's roster."""
    st.title("👥 My Roster")
    
    dm = st.session_state.data_manager
    league = st.session_state.fantrax_league
    my_team = st.session_state.my_team_name
    
    if not league:
        st.warning("⚠️ No league connected. Go to 'Fantrax League' to connect.")
        return
    
    if not my_team:
        st.warning("⚠️ No team selected. Go to 'Fantrax League' to select your team.")
        return
    
    st.markdown(f"### Team: {my_team}")
    
    if st.button("🔄 Refresh Roster"):
        with st.spinner("Loading roster..."):
            roster_df = dm.get_my_roster(league, my_team)
            st.session_state.my_roster = roster_df
            st.rerun()
    
    # Fetch roster if not in session state
    if 'my_roster' not in st.session_state or st.session_state.my_roster is None:
        with st.spinner("Loading roster..."):
            roster_df = dm.get_my_roster(league, my_team)
            st.session_state.my_roster = roster_df
    else:
        roster_df = st.session_state.my_roster
    
    if roster_df.empty:
        st.error("Failed to load roster")
        return
    
    # Display roster stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(roster_df))
    with col2:
        injured_count = roster_df['Injured'].sum() if 'Injured' in roster_df.columns else 0
        st.metric("Injured", injured_count)
    with col3:
        total_fp = roster_df['Total_FP'].sum() if 'Total_FP' in roster_df.columns else 0
        st.metric("Total Fantasy Points", f"{total_fp:.1f}")
    with col4:
        avg_fpg = roster_df['FP_Per_Game'].mean() if 'FP_Per_Game' in roster_df.columns else 0
        st.metric("Avg FP/Game", f"{avg_fpg:.2f}")
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        position_filter = st.selectbox(
            "Filter by Position:",
            ["All"] + sorted(roster_df['Position'].unique().tolist())
        )
    
    # Apply filter
    if position_filter != "All":
        display_df = roster_df[roster_df['Position'].str.contains(position_filter, na=False)]
    else:
        display_df = roster_df
    
    # Display roster
    st.dataframe(display_df, use_container_width=True, height=500)


def show_available_players():
    """Display all available free agents not on any roster."""
    st.title("🆓 Available Players")
    
    dm = st.session_state.data_manager
    league = st.session_state.fantrax_league
    
    if not league:
        st.warning("⚠️ No league connected. Go to 'Fantrax League' to connect.")
        return
    
    st.markdown("### Free Agents - Players Not on Any Roster")
    st.info("💡 These players are available for waiver claims or draft picks. Compare their stats to make informed decisions!")
    
    # Add refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Available Players"):
            if 'available_players' in st.session_state:
                del st.session_state.available_players
            st.rerun()
    
    # Fetch available players if not in session state
    if 'available_players' not in st.session_state or st.session_state.available_players is None:
        with st.spinner("Loading available players... (this may take 30-60 seconds)"):
            available_df = dm.get_available_players(league)
            st.session_state.available_players = available_df
    else:
        available_df = st.session_state.available_players
    
    if available_df.empty:
        st.error("Failed to load available players")
        return
    
    # Display summary stats
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Available Players", f"{len(available_df):,}")
    with col2:
        if 'Position' in available_df.columns:
            num_positions = available_df['Position'].nunique()
            st.metric("Positions", num_positions)
        else:
            st.metric("Positions", "N/A")
    with col3:
        if 'MLB_Team' in available_df.columns:
            num_teams = available_df['MLB_Team'].nunique()
            st.metric("MLB Teams", num_teams)
        else:
            st.metric("MLB Teams", "N/A")
    with col4:
        # Calculate percentage available
        total_in_db = len(dm.id_map_df) if dm.id_map_df is not None else 0
        pct_available = (len(available_df) / total_in_db * 100) if total_in_db > 0 else 0
        st.metric("% Available", f"{pct_available:.1f}%")
    
    st.markdown("---")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Position' in available_df.columns:
            position_filter = st.selectbox(
                "Filter by Position:",
                ["All"] + sorted([p for p in available_df['Position'].unique() if pd.notna(p)])
            )
        else:
            position_filter = "All"
    
    with col2:
        if 'MLB_Team' in available_df.columns:
            mlb_team_filter = st.selectbox(
                "Filter by MLB Team:",
                ["All"] + sorted([t for t in available_df['MLB_Team'].unique() if pd.notna(t)])
            )
        else:
            mlb_team_filter = "All"
    
    with col3:
        # Position type filter
        pos_type_options = ["All", "Batters", "Pitchers"]
        pos_type_filter = st.selectbox("Player Type:", pos_type_options)
    
    # Search box
    search_query = st.text_input("🔍 Search by player name:", "")
    
    # Apply filters
    display_df = available_df.copy()
    
    if position_filter != "All":
        display_df = display_df[display_df['Position'].str.contains(position_filter, na=False)]
    
    if mlb_team_filter != "All":
        display_df = display_df[display_df['MLB_Team'] == mlb_team_filter]
    
    # Position type filter (batters vs pitchers)
    if pos_type_filter == "Batters" and 'Position' in display_df.columns:
        batter_positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'LF', 'CF', 'RF', 'UT']
        display_df = display_df[display_df['Position'].str.contains('|'.join(batter_positions), na=False, case=False)]
    elif pos_type_filter == "Pitchers" and 'Position' in display_df.columns:
        pitcher_positions = ['SP', 'RP', 'P']
        display_df = display_df[display_df['Position'].str.contains('|'.join(pitcher_positions), na=False, case=False)]
    
    if search_query:
        display_df = display_df[display_df['Player_Name'].str.contains(search_query, case=False, na=False)]
    
    # Display results
    st.markdown(f"**Showing {len(display_df):,} of {len(available_df):,} available players**")
    
    # Add option to merge with projections
    if st.checkbox("📊 Merge with Projections (if loaded)", value=False):
        if dm.steamer_batters is not None or dm.steamer_pitchers is not None:
            st.info("Projection merge - coming soon!")
        else:
            st.warning("No projections loaded. Go to Dashboard and click 'Load Projections'")
    
    # Display dataframe
    st.dataframe(
        display_df, 
        use_container_width=True, 
        height=500,
        column_config={
            "Player_Name": st.column_config.TextColumn("Player", width="medium"),
            "Position": st.column_config.TextColumn("Pos", width="small"),
            "MLB_Team": st.column_config.TextColumn("MLB Team", width="small"),
            "Fantrax_ID": st.column_config.TextColumn("Fantrax ID", width="small"),
            "Fangraphs_ID": st.column_config.TextColumn("FG ID", width="small"),
        }
    )
    
    # Export option
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📥 Export to CSV"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"available_players_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.info("💡 **Tip**: Export to CSV to analyze with projections in a spreadsheet")

    
    # Download button
    csv = roster_df.to_csv(index=False)
    st.download_button(
        "📥 Download Roster CSV",
        csv,
        f"{my_team}_roster.csv",
        "text/csv"
    )
    
    # Roster analysis
    if st.button("🎯 Analyze Roster"):
        st.info("Roster analysis coming soon! Will include buy-low/sell-high recommendations for your players.")


def show_league_standings():
    """Display league standings."""
    st.title("🏆 League Standings")
    
    dm = st.session_state.data_manager
    league = st.session_state.fantrax_league
    
    if not league:
        st.warning("⚠️ No league connected. Go to 'Fantrax League' to connect.")
        return
    
    if st.button("🔄 Refresh Standings"):
        with st.spinner("Loading standings..."):
            standings_df = dm.get_league_standings(league)
            st.session_state.standings = standings_df
            st.rerun()
    
    # Fetch standings if not in session state
    if 'standings' not in st.session_state or st.session_state.standings is None:
        with st.spinner("Loading standings..."):
            standings_df = dm.get_league_standings(league)
            st.session_state.standings = standings_df
    else:
        standings_df = st.session_state.standings
    
    if standings_df.empty:
        st.error("Failed to load standings")
        return
    
    # Display standings
    st.dataframe(standings_df, use_container_width=True)
    
    # Download button
    csv = standings_df.to_csv(index=False)
    st.download_button(
        "📥 Download Standings CSV",
        csv,
        "league_standings.csv",
        "text/csv"
    )


def show_transactions():
    """Display recent league transactions."""
    st.title("📜 Recent Transactions")
    
    dm = st.session_state.data_manager
    league = st.session_state.fantrax_league
    
    if not league:
        st.warning("⚠️ No league connected. Go to 'Fantrax League' to connect.")
        return
    
    count = st.slider("Number of transactions to display:", 10, 200, 50, 10)
    
    if st.button("🔄 Refresh Transactions"):
        with st.spinner("Loading transactions..."):
            transactions_df = dm.get_recent_transactions(league, count)
            st.session_state.transactions = transactions_df
            st.rerun()
    
    # Fetch transactions if not in session state
    if 'transactions' not in st.session_state or st.session_state.transactions is None:
        with st.spinner("Loading transactions..."):
            transactions_df = dm.get_recent_transactions(league, count)
            st.session_state.transactions = transactions_df
    else:
        transactions_df = st.session_state.transactions
    
    if transactions_df.empty:
        st.error("Failed to load transactions")
        return
    
    # Filter options
    all_teams = ["All"] + sorted(transactions_df['Team'].unique().tolist())
    team_filter = st.selectbox("Filter by Team:", all_teams)
    
    # Apply filter
    if team_filter != "All":
        display_df = transactions_df[transactions_df['Team'] == team_filter]
    else:
        display_df = transactions_df
    
    # Display transactions
    st.dataframe(display_df, use_container_width=True, height=500)
    
    # Download button
    csv = transactions_df.to_csv(index=False)
    st.download_button(
        "📥 Download Transactions CSV",
        csv,
        "league_transactions.csv",
        "text/csv"
    )


def show_settings():
    """Settings and configuration page."""
    st.title("⚙️ Settings")
    
    st.subheader("League Scoring Configuration")
    
    st.markdown("**Current Batting Categories:**")
    st.code("R, RBI, OBP, SBN2 (SB - CS×2), XBS ((2B+3B+HR) + SH)")
    
    st.markdown("**Current Pitching Categories:**")
    st.code("K, ERA, WHIP, RPC (Relief Contribution), SPC (Starting Contribution)")
    
    st.markdown("---")
    
    st.subheader("Fantrax Connection")
    
    st.markdown("**League Status:**")
    if st.session_state.fantrax_league:
        st.success(f"✓ Connected to: {st.session_state.fantrax_league.name}")
        st.info(f"League ID: {st.session_state.league_id}")
        if st.session_state.my_team_name:
            st.info(f"Your Team: {st.session_state.my_team_name}")
    else:
        st.warning("⚠ Not connected to any league")
    
    st.markdown("---")
    
    st.subheader("Private League Authentication")
    
    with st.expander("🔒 Connect to Private League"):
        st.markdown("""
        **For private leagues**, the `fantraxapi` library requires authentication using cookies.
        
        **Setup Instructions:**
        
        1. Install additional dependencies:
        ```bash
        pip install selenium webdriver-manager
        ```
        
        2. Add authentication code to your app (see fantraxapi documentation)
        
        3. You'll need your Fantrax username and password
        
        **Reference:** [fantraxapi Authentication Guide](https://fantraxapi.kometa.wiki/en/latest/intro.html#connecting-with-a-private-league-or-accessing-specific-endpoints)
        
        **Note:** This requires setting up Selenium with Chrome WebDriver for automated login.
        """)
    
    st.markdown("---")
    
    st.subheader("Data Sources")
    st.markdown("- **Player IDs:** SFBB Player ID Map (PLAYERIDMAP.csv)")
    st.markdown("- **Projections:** Steamer (via pybaseball)")
    st.markdown("- **Advanced Stats:** Statcast (via pybaseball)")
    st.markdown("- **Fantrax Data:** fantraxapi library")
    
    st.markdown("---")
    
    st.subheader("About")
    st.markdown("""
    **Dynasty Baseball Team Manager v2.0**
    
    A comprehensive tool for managing your Fantrax dynasty league with:
    - **Fantrax Integration** - Live roster, standings, and transaction data
    - **Dual-value analysis** - Scoring vs. peripherals
    - **Buy-low and sell-high identification**
    - **Player comparison tools**
    - **Integrated projection systems**
    
    Built with Streamlit, pandas, pybaseball, and fantraxapi.
    
    ---
    
    **Updates in v2.0:**
    - ✨ Full Fantrax API integration
    - 📊 Live roster management
    - 🏆 League standings tracking
    - 📜 Transaction history
    - 🔗 Direct league connection
    """)


if __name__ == '__main__':
    main()
