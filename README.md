# Dynasty Baseball Team Manager

A comprehensive Streamlit web application for managing your Fantrax Dynasty Baseball Team with advanced dual-value analysis.

## Overview

This application helps you make better dynasty baseball decisions by tracking both:

1. **League Scoring Value** (The "Results") - How players perform in your specific fantasy scoring system
2. **Performance Peripherals** (The "Process") - Advanced metrics that predict future performance

## League Scoring Categories

### Batting

- **R** - Runs
- **RBI** - Runs Batted In
- **OBP** - On-Base Percentage
- **SBN2** - Steals Net (SB - CS×2)
- **XBS** - Extra Base & Sac Hits ((2B+3B+HR) + SH)

### Pitching

- **K** - Strikeouts
- **ERA** - Earned Run Average
- **WHIP** - Walks + Hits per Innings Pitched
- **RPC** - Relief Contribution
- **SPC** - Starting Contribution

## Performance Peripherals Tracked

### Batting

PA, Games, OPS, SLG, SB, CS, K%, BB%, Hard Hit%, Barrel%

### Pitching

IP, Wins, Losses, Saves, Holds, K%, BB%, K/BB%, SwStr%, xFIP

## Project Structure

```
baseball-python/
├── app.py                 # Main Streamlit dashboard application
├── data_manager.py        # Data fetching and ID mapping
├── evaluator.py          # Dual-value analysis engine
├── requirements.txt       # Python dependencies
└── data/
    └── PLAYERIDMAP.csv   # SFBB Player ID mapping
```

## Features

### 🏠 Dashboard

- Quick overview of loaded data
- One-click data loading for Steamer projections and Statcast
- Visual metrics for database status

### 📊 Player Lookup

- Search players by name or Fantrax ID
- View all ID mappings (MLB, FanGraphs, etc.)
- Quick player information display

### 🎯 Projections & Stats

- View and download Steamer projections
- Access Statcast advanced metrics
- Separate views for batters and pitchers

### 💎 Value Analysis

- **Buy-Low Candidates** - Players whose peripherals suggest they'll improve
- **Sell-High Candidates** - Players overperforming their peripherals
- Full roster evaluation with confidence ratings
- Customizable confidence thresholds

### 🔄 Player Comparison

- Side-by-side comparison of any two players
- Fantasy value vs peripheral scores
- Automated recommendations with reasoning
- Detailed flags for each player

### 📁 Roster Manager

- Upload your Fantrax roster CSV
- Analyze your entire team
- Identify trade targets (coming soon)

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Ensure you have the PLAYERIDMAP.csv in the data/ folder**

## Usage

### Start the application:

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

### First Steps:

1. **Load Data** - Click "Load Steamer Projections" on the Dashboard
2. **Search Players** - Use Player Lookup to find specific players
3. **Analysis** - Navigate to Value Analysis to find buy-low/sell-high candidates
4. **Compare** - Use Player Comparison to evaluate trade offers

## Data Sources

- **Player ID Mapping**: SFBB Player ID Map (PLAYERIDMAP.csv)
- **Projections**: Steamer projections via pybaseball
- **Advanced Stats**: Statcast data via pybaseball
- **Roster Data**: Manual Fantrax CSV export (Fantrax API not available)

## Dual-Value Analysis Logic

The evaluator analyzes players on two dimensions:

1. **Fantasy Score**: Calculated from league scoring categories
2. **Peripheral Score**: Calculated from process metrics

Players are flagged as:

- **💎 Underperforming**: Strong peripherals, weak fantasy output (BUY)
- **⚠️ Overperforming**: Strong fantasy output, weak peripherals (SELL)
- **Aligned**: Fantasy output matches peripheral quality
- **Confidence Rating**: 0-1 scale based on sample size and metric alignment

## Key Functions

### data_manager.py

- `DataManager.load_id_map()` - Load player ID database
- `DataManager.fetch_steamer_projections()` - Get Steamer projections
- `DataManager.fetch_statcast_data()` - Get Statcast metrics
- `DataManager.get_ids_by_fantrax()` - Map Fantrax ID to other IDs

### evaluator.py

- `PlayerEvaluator.evaluate_batter()` - Evaluate a batter's dual value
- `PlayerEvaluator.evaluate_pitcher()` - Evaluate a pitcher's dual value
- `PlayerEvaluator.identify_buy_low_candidates()` - Find undervalued players
- `PlayerEvaluator.identify_sell_high_candidates()` - Find overvalued players
- `compare_players()` - Compare two players side-by-side

## Customization

You can customize the scoring weights in [evaluator.py](evaluator.py):

```python
self.batter_scoring_weights = {
    'R': 1.0,
    'RBI': 1.0,
    'OBP': 100.0,
    'SBN2': 2.0,
    'XBS': 1.5
}
```

Adjust these values to match your league's specific point values.

## Fantrax Integration

**Note**: Fantrax does not provide a public API. To analyze your roster:

1. Go to your Fantrax league
2. Export your roster as CSV
3. Upload the CSV in the "Roster Manager" tab

## Future Enhancements

- [ ] Historical trend analysis
- [ ] Trade calculator with multiple players
- [ ] Draft assistant mode
- [ ] Injury tracking integration
- [ ] Custom scoring system builder
- [ ] Web scraping for Fantrax (use responsibly)

## Technical Requirements

- Python 3.8+
- Streamlit 1.28+
- pandas 2.0+
- pybaseball 2.2.7+
- Internet connection for data fetching

## Notes

- **Steamer projections**: Available year-round for next season
- **Statcast data**: Only available during/after the season starts
- **Data caching**: pybaseball automatically caches data locally
- **Performance**: Limited to 100 players for analysis operations to maintain speed

## Troubleshooting

### "pybaseball not available" error

```bash
pip install pybaseball
```

### "PLAYERIDMAP.csv not found"

- Ensure the CSV is in the `data/` folder
- Check the file path in data_manager.py

### Statcast data returns empty

- This is normal during off-season
- Statcast data starts accumulating once the season begins

## Support

For questions about:

- **Fantrax**: Visit fantrax.com
- **pybaseball**: Check github.com/jldbc/pybaseball
- **Steamer projections**: Visit fangraphs.com

## License

This project is for personal use. Please respect data source terms of service.

---

**Built with**: Streamlit, pandas, pybaseball, numpy

**Version**: 1.0.0 - Phase 1 Complete
