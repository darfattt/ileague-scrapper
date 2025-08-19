# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Indonesia Super League Football Statistics Scraper with an integrated Streamlit dashboard for data visualization. The project consists of four main components:

1. **Club Statistics Scraper** (`scraper.py`) - Extracts club-level football statistics from ileague.id
2. **Player Statistics Scraper** (`player_scraper.py`) - Extracts individual player statistics from ileague.id
3. **Data Combiner** (`combine_player_data.py`) - Combines player info with statistics for comprehensive database
4. **Streamlit Dashboard** (`isuperleague-club-streamlit/`) - Interactive visualization of scraped data

## Key Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running the Club Statistics Scraper
```bash
# Interactive mode - shows menu of available statistics
python scraper.py

# Scrape specific statistic
python scraper.py AKURASIUMPAN

# Scrape all statistics and export to CSV
python scraper.py --all --csv

# CSV export only (suppress terminal output)
python scraper.py --all --csv-only --output football_stats.csv

# Scrape single statistic with CSV export
python scraper.py AKURASIUMPAN --csv --output specific_stat.csv
```

### Running the Player Statistics Scraper
```bash
# Interactive mode - shows menu of available player statistics
python player_scraper.py

# Scrape specific player statistic for all clubs
python player_scraper.py GOAL

# Scrape all player statistics and export to CSV
python player_scraper.py --all --csv --output player_stats.csv

# CSV export only (suppress terminal output)
python player_scraper.py --all --csv-only --output player_stats.csv

# Enhanced mode - comprehensive player data using teams_info.json
python player_scraper.py --enhanced --output enhanced_player_stats.csv

# NEW: Club-level aggregated statistics (sum of all players per club)
python player_scraper.py --club-stats --output club_aggregated_stats.csv
```

### Running the Data Combiner
```bash
# Combine player info from teams_info.json with stats from player_stats.csv
python combine_player_data.py

# Output: data/players_statistics.csv with comprehensive player database
# Format: Name,Player Name,Team,Country,Age,Position,Picture Url,Appearances,Assist,Ball Recovery,...
```

### Running the Dashboard
```bash
# Run Streamlit dashboard (requires CSV data)
streamlit run isuperleague-club-streamlit/app.py
```

## Architecture Overview

### Club Statistics Scraper (`scraper.py`)

- **ILeagueScraper class**: Main scraper that makes POST requests to `https://ileague.id/top_actions/club/BRI_SUPER_LEAGUE_2025-26`
- **CSVDataManager class**: Handles data aggregation and CSV export across multiple statistics
- **Statistic Types**: 15 predefined statistics (e.g., AKURASIUMPAN → "Akurasi Umpan", KARTUMERAH → "Kartu Merah")
- **Parsing Strategy**: Multiple fallback methods for extracting club statistics from HTML tables

### Player Statistics Scraper (`player_scraper.py`)

- **ILeaguePlayerScraper class**: Extracts player statistics from `https://ileague.id/top_actions/player/BRI_SUPER_LEAGUE_2025-26`
- **PlayerCSVDataManager class**: Basic player statistics export
- **EnhancedPlayerCSVDataManager class**: Comprehensive player data with team info
- **ClubStatsCSVDataManager class**: NEW - Aggregates player stats per club
- **Player Statistics**: 22 player-specific statistics (Assist, Ball Recovery, Block, Goals, etc.)
- **Team Integration**: Loads club data from `25_26_teams.json` and player data from `data/teams_info.json`
- **NEW Feature**: `--club-stats` flag aggregates all player statistics per club

### Data Combiner (`combine_player_data.py`)

- **PlayerDataCombiner class**: NEW - Combines player information with statistics
- **Smart Matching**: Multi-strategy player name matching with team validation
- **Team Validation**: Ensures `csv.Team == json.teams.name` for accurate matches
- **Fallback Handling**: Sets missing statistics to 0 for comprehensive database
- **Input Sources**: 
  - Player info: `data/teams_info.json`
  - Player stats: `player_stats.csv`
- **Output**: `data/players_statistics.csv` with comprehensive player database

### Streamlit Dashboard Structure

- **Main App** (`app.py`): Multi-page Streamlit application with sidebar navigation
- **Data Loader** (`utils/data_loader.py`): FootballDataLoader class with metric categorization
- **Visualizations** (`utils/visualization.py`): Plotly chart utilities
- **Metric Categories**: Attack, Defense, Progression, General

### Data Flow

**Club Statistics Flow:**
1. Club scraper extracts statistics → CSV export (`football_stats.csv`)
2. Dashboard loads CSV → processes into metric categories → interactive visualizations
3. Expected CSV format: `TEAM,Akurasi Umpan,Akurasi Tembakan,Kartu Kuning,...`

**Player Statistics Flow:**
1. Player scraper extracts individual statistics → CSV export (`player_stats.csv`)
2. Data combiner matches players with team info → comprehensive database (`data/players_statistics.csv`)
3. Optional: Club-level aggregation via `--club-stats` flag

**NEW: Comprehensive Player Database:**
1. `team_players_scraper.py` → `data/teams_info.json` (player demographics)
2. `player_scraper.py --all --csv-only` → `player_stats.csv` (player statistics)
3. `combine_player_data.py` → `data/players_statistics.csv` (combined comprehensive database)

## Important Technical Details

### Available Club Statistics (Indonesian Names)
- **Akurasi Umpan** (AKURASIUMPAN) - Pass Accuracy
- **Akurasi Tembakan** (AKURASITEMBAKAN) - Shot Accuracy  
- **Kartu Kuning/Merah** (KARTUKUNING/KARTUMERAH) - Yellow/Red Cards
- **Penguasaan Bola** (PENGUASAANBOLAPERSEN) - Ball Possession
- **Tekel Sukses** (TEKELSUKSES) - Successful Tackles
- And 10 others (see `statistics_types` dict in `scraper.py:72-88`)

### Available Player Statistics
- **Assist, Ball Recovery, Block, Block Cross, Clearance**
- **Create Chance, Cross, Dribble Success, Foul, Fouled**
- **Free Kick, Goal, Header Won, Intercept, Own Goal**
- **Passing, Penalty Goal, Saves, Shoot Off Target, Shoot On Target**
- **Tackle, Yellow Card**
- Total: 22 player-specific statistics (see `statistics_types` dict in `player_scraper.py:132-155`)

### Key Classes

**Club Statistics (`scraper.py`):**
- **`ILeagueScraper`** (`scraper.py:60`): Main scraper with session management and HTML parsing
- **`CSVDataManager`** (`scraper.py:16`): Data aggregation across multiple scraping sessions

**Player Statistics (`player_scraper.py`):**
- **`ILeaguePlayerScraper`** (`player_scraper.py:168`): Player statistics scraper with team integration
- **`PlayerCSVDataManager`** (`player_scraper.py:18`): Basic player data export
- **`EnhancedPlayerCSVDataManager`** (`player_scraper.py:67`): Enhanced export with player info
- **`ClubStatsCSVDataManager`** (`player_scraper.py:121`): NEW - Club-level aggregation

**Data Combination (`combine_player_data.py`):**
- **`PlayerDataCombiner`** (`combine_player_data.py:9`): NEW - Smart player data combination with team validation

**Dashboard:**
- **`FootballDataLoader`** (`utils/data_loader.py:6`): Dashboard data loading with metric categorization

### Scraper Parsing Logic

The scraper uses multiple fallback strategies to extract club statistics:
1. Primary: Look for `div.info-ranking.top-player.background-color-2` with nested tables
2. Fallback: Search all `table.background-color-2` elements
3. Final: Parse any table with reasonable club statistics (≥10 entries)

Each strategy extracts club name and statistical value pairs, filtering out non-club entries.

## Development Workflow

1. **Data Collection**: Run scraper to collect latest statistics
2. **Data Export**: Use `--csv` flag to generate/update `football_stats.csv`
3. **Analysis**: Use Streamlit dashboard to visualize and analyze collected data
4. **Dashboard Data Path**: Dashboard expects CSV at `isuperleague-club-streamlit/data/football_stats.csv`

The scraper includes rate limiting (1-second delays) and comprehensive error handling for robustness.

## Data Collection Workflow

### Initial Setup (One Time Only)
```bash
# Scrape all team and player information
python team_players_scraper.py

# This creates:
# - 25_26_teams.json (club information)
# - data/teams_info.json (comprehensive player demographics)
```

### Regular Data Updates (Every Gameweek End)
```bash
# 0. sequence update
python team_players_scraper.py
python player_scraper.py --all --csv-only
python combine_player_data.py

# 1. Update club statistics
python scraper.py --all --csv-only --output football_stats.csv

# 2. Update player statistics  
python player_scraper.py --all --csv-only --output player_stats.csv

# 3. Combine player info with statistics (comprehensive database)
python combine_player_data.py

# Optional: Generate club-level aggregated player stats
python player_scraper.py --club-stats --output club_aggregated_stats.csv
```

### Output Files Generated
- **`football_stats.csv`**: Club-level statistics (team aggregated)
- **`player_stats.csv`**: Individual player statistics
- **`data/players_statistics.csv`**: NEW - Comprehensive player database (demographics + statistics)
- **`club_aggregated_stats.csv`**: Optional - Club totals from player statistics

### NEW Features Added Today
1. **Enhanced Player Scraper**: Added `--club-stats` flag for club-level aggregation
2. **Data Combiner**: Smart player matching with team validation
3. **Team Validation**: Ensures accurate player-statistics matching via team names
4. **Comprehensive Database**: Complete player info + statistics in single CSV
