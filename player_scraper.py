#!/usr/bin/env python3
"""
Indonesia Super League Player Statistics Scraper
Scrapes player statistics from ileague.id
"""

import requests
from bs4 import BeautifulSoup
import sys
import time
import re
import csv
import argparse
import json
from pathlib import Path
from collections import defaultdict

class PlayerCSVDataManager:
    def __init__(self):
        self.player_data = defaultdict(dict)
        
    def add_statistic_data(self, stat_type, stat_name, club_name, player_statistics):
        """Add statistics data for a specific type and club"""
        for player_stat in player_statistics:
            player_name = player_stat['player_name']
            value = player_stat['value']
            
            # Store player's team information
            self.player_data[player_name]['Team'] = club_name
            self.player_data[player_name][stat_name] = value
    
    def export_to_csv(self, filename, statistics_types):
        """Export all collected data to CSV file"""
        if not self.player_data:
            print("No data to export")
            return False
            
        # Get all player names
        players = sorted(self.player_data.keys())
        
        # Get all statistic names
        stat_columns = [stat_name for stat_name in statistics_types.values()]
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = ['Player Name', 'Team'] + stat_columns
            writer.writerow(header)
            
            # Write data rows
            for player in players:
                row = [player]
                row.append(self.player_data[player].get('Team', ''))
                for stat_name in stat_columns:
                    value = self.player_data[player].get(stat_name, '')
                    row.append(value)
                writer.writerow(row)
        
        print(f"Data exported to {filename}")
        print(f"Players: {len(players)}")
        print(f"Statistics: {len(stat_columns)}")
        return True


class EnhancedPlayerCSVDataManager:
    def __init__(self, all_players):
        self.all_players = all_players
        self.player_stats = {}
        
    def add_player_statistic(self, full_name, stat_name, value):
        """Add a statistic for a specific player by full name"""
        if full_name not in self.player_stats:
            self.player_stats[full_name] = {}
        self.player_stats[full_name][stat_name] = value
    
    def export_comprehensive_csv(self, filename, statistics_types):
        """Export player info + statistics to CSV"""
        if not self.all_players:
            print("No player data to export")
            return False
            
        # Define comprehensive header
        header = [
            'Name', 'Full Name', 'Team', 'Position', 'Age', 
            'Country', 'Appearances', 'Picture URL'
        ] + list(statistics_types.values())
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            
            for player in self.all_players:
                full_name = player.get('fullName', '')
                row = [
                    player.get('name', ''),
                    full_name,
                    player.get('team_name', ''),
                    player.get('posisi', ''),
                    player.get('usia', ''),
                    player.get('negara', ''),
                    player.get('penampilan', ''),
                    player.get('pictureUrl', '')
                ]
                
                # Add statistics columns
                for stat_name in statistics_types.values():
                    value = self.player_stats.get(full_name, {}).get(stat_name, '')
                    row.append(value)
                
                writer.writerow(row)
        
        print(f"Enhanced data exported to {filename}")
        print(f"Players: {len(self.all_players)}")
        print(f"Statistics: {len(statistics_types)}")
        return True


class ClubStatsCSVDataManager:
    def __init__(self, clubs):
        self.clubs = clubs  # Dictionary of club_id: club_name
        self.club_stats = defaultdict(lambda: defaultdict(int))
        
    def add_club_statistic(self, club_id, stat_name, value):
        """Add a statistic value for a specific club (aggregates values)"""
        try:
            numeric_value = float(value) if value else 0
            self.club_stats[club_id][stat_name] += numeric_value
        except (ValueError, TypeError):
            # If value is not numeric, just keep the latest value
            self.club_stats[club_id][stat_name] = value or 0
    
    def export_club_stats_csv(self, filename, statistics_types):
        """Export aggregated club statistics to CSV"""
        if not self.club_stats:
            print("No club statistics to export")
            return False
            
        # Define header
        header = ['Club'] + list(statistics_types.values())
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            
            # Sort clubs by name for consistent output
            sorted_club_ids = sorted(self.club_stats.keys(), key=lambda x: self.clubs.get(x, f'Club {x}'))
            
            for club_id in sorted_club_ids:
                club_name = self.clubs.get(club_id, f'Club {club_id}')
                row = [club_name]
                
                # Add statistics columns, defaulting to 0 if no data
                for stat_name in statistics_types.values():
                    value = self.club_stats[club_id].get(stat_name, 0)
                    row.append(value)
                
                writer.writerow(row)
        
        print(f"Club statistics exported to {filename}")
        print(f"Clubs: {len(self.club_stats)}")
        print(f"Statistics: {len(statistics_types)}")
        return True

class ILeaguePlayerScraper:
    def __init__(self):
        self.base_url = "https://ileague.id/top_actions/player/BRI_SUPER_LEAGUE_2025-26"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.statistics_types = {
            'ASSIST': 'Assist',
            'BALL_RECOVERY': 'Ball Recovery',
            'BLOCK': 'Block',
            'BLOCK_CROSS': 'Block Cross',
            'CLEARANCE': 'Clearance',
            'CREATE_CHANCE': 'Create Chance',
            'CROS': 'Cross',
            'DRIBBLE_SUCCESS': 'Dribble Success',
            'FOUL': 'Foul',
            'FOULED': 'Fouled',
            'FREE_KICK': 'Free Kick',
            'GOAL': 'Goal',
            'HEADER_WON': 'Header Won',
            'INTERCEPT': 'Intercept',
            'OWN_GOAL': 'Own Goal',
            'PASSING': 'Passing',
            'PENALTY_GOAL': 'Penalty Goal',
            'SAVES': 'Saves',
            'SHOOT_OFF_TARGET': 'Shoot Off Target',
            'SHOOT_ON_TARGET': 'Shoot On Target',
            'TACKLE': 'Tackle',
            'YELLOW_CARD': 'Yellow Card'
        }
        
        self.clubs = self.load_clubs_from_json()
        self.csv_manager = PlayerCSVDataManager()
        self.all_players = self.load_all_players_from_teams_info()

    def load_clubs_from_json(self):
        """Load club information from the 25_26_teams.json file"""
        try:
            # Get the script directory and construct path to JSON file
            script_dir = Path(__file__).parent
            json_file = script_dir / '25_26_teams.json'
            
            with open(json_file, 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
            
            # Convert to dictionary mapping id to name
            clubs_dict = {}
            for team in teams_data:
                clubs_dict[team['id']] = team['name']
            
            print(f"Loaded {len(clubs_dict)} clubs from {json_file}")
            return clubs_dict
            
        except FileNotFoundError:
            print(f"Warning: Could not find 25_26_teams.json, using fallback club data")
            return self.get_fallback_clubs()
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing 25_26_teams.json: {e}")
            print("Using fallback club data")
            return self.get_fallback_clubs()
        except Exception as e:
            print(f"Warning: Unexpected error loading clubs: {e}")
            print("Using fallback club data")
            return self.get_fallback_clubs()

    def get_fallback_clubs(self):
        """Fallback club data in case JSON file is not available"""
        return {
            32: 'AREMA FC',
            71: 'BALI UNITED FC',
            30: 'BHAYANGKARA PRESISI LAMPUNG FC',
            192: 'BORNEO FC SAMARINDA',
            209: 'DEWA UNITED BANTEN FC',
            40: 'MADURA UNITED FC',
            1819851379: 'MALUT UNITED FC',
            280: 'PERSEBAYA SURABAYA',
            11: 'PERSIB BANDUNG',
            12: 'PERSIJA JAKARTA',
            21: 'PERSIJAP JEPARA',
            37: 'PERSIK KEDIRI',
            67: 'PERSIS SOLO',
            15: 'PERSITA',
            181: 'PSBS BIAK',
            27: 'PSIM YOGYAKARTA',
            50: 'PSM MAKASSAR',
            5: 'SEMEN PADANG FC'
        }

    def load_all_players_from_teams_info(self):
        """Load all players from data/teams_info.json"""
        try:
            script_dir = Path(__file__).parent
            teams_info_file = script_dir / 'data' / 'teams_info.json'
            
            with open(teams_info_file, 'r', encoding='utf-8') as f:
                teams_info = json.load(f)
            
            all_players = []
            for team in teams_info['teams']:
                for player in team['players']:
                    # Add team info to player data
                    player_with_team = player.copy()
                    player_with_team['team_id'] = team['id']
                    player_with_team['team_name'] = team['name']
                    all_players.append(player_with_team)
            
            print(f"Loaded {len(all_players)} players from teams_info.json")
            return all_players
            
        except FileNotFoundError:
            print("Warning: Could not find data/teams_info.json")
            return []
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing data/teams_info.json: {e}")
            return []
        except Exception as e:
            print(f"Warning: Unexpected error loading teams_info.json: {e}")
            return []

    def scrape_statistic(self, statistic_type, club_id):
        """Scrape a specific statistic type for a specific club"""
        try:
            payload = {
                'statistik': statistic_type,
                'klub': str(club_id)
            }
            response = self.session.post(self.base_url, data=payload, timeout=30)
            response.raise_for_status()
            
            return self.parse_statistics(response.text, statistic_type, club_id)
            
        except requests.RequestException as e:
            print(f"Error fetching data for {statistic_type} (Club {club_id}): {e}")
            return None
        except Exception as e:
            print(f"Error processing data for {statistic_type} (Club {club_id}): {e}")
            return None

    def parse_statistics(self, html_content, stat_type, club_id):
        """Parse HTML content to extract player statistics"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        player_stats = []
        
        # Primary strategy: Look for the specific div structure
        stats_div = soup.find('div', class_='info-ranking top-player background-color-2')
        
        if stats_div:
            # Verify this is the correct statistic by checking the h4 title
            h4_title = stats_div.find('h4')
            if h4_title:
                title_text = self.clean_text(h4_title.get_text())
                print(f"Found statistics section: {title_text}")
            
            # Find the table with statistics
            stats_table = stats_div.find('table', class_='background-color-2')
            
            if stats_table:
                player_stats = self.extract_from_specific_table(stats_table)
                print(f"Extracted {len(player_stats)} players from main statistics table")
            else:
                print("Statistics table not found in the expected div")
        
        # Fallback: Look for any table with the background-color-2 class
        if not player_stats:
            tables = soup.find_all('table', class_='background-color-2')
            for table in tables:
                extracted_stats = self.extract_from_specific_table(table)
                if extracted_stats:
                    player_stats.extend(extracted_stats)
                    print(f"Found {len(extracted_stats)} players in fallback table")
        
        # Additional fallback: Look for any table with statistics data
        if not player_stats:
            all_tables = soup.find_all('table')
            for table in all_tables:
                extracted_stats = self.extract_from_table(table)
                if extracted_stats and len(extracted_stats) >= 3:  # Likely to be player stats
                    player_stats.extend(extracted_stats)
                    print(f"Found {len(extracted_stats)} players in general table")
        
        return {
            'statistic_type': stat_type,
            'statistic_name': self.statistics_types.get(stat_type, stat_type),
            'club_id': club_id,
            'club_name': self.clubs.get(club_id, f'Club {club_id}'),
            'player_statistics': player_stats,
            'total_players': len(player_stats),
            'html_length': len(html_content),
            'title': soup.title.string if soup.title else 'No title found'
        }

    def extract_from_specific_table(self, table):
        """Extract player statistics from the specific ileague table structure"""
        stats = []
        
        # Find tbody or use table directly
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = table.find_all('tr')
        
        print(f"Found {len(rows)} rows in statistics table")
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # Typically: [rank/position, player_name, value, additional_info...]
                # Or: [player_name, value]
                
                # Try to identify player name and value
                potential_player = None
                potential_value = None
                
                for cell in cells:
                    cell_text = self.clean_text(cell.get_text())
                    
                    # Check if this looks like a player name (contains letters, reasonable length)
                    if (len(cell_text) > 3 and 
                        any(c.isalpha() for c in cell_text) and
                        not cell_text.isdigit() and
                        not self.is_percentage(cell_text) and
                        not self.looks_like_team_name(cell_text)):
                        potential_player = cell_text
                    
                    # Check if this looks like a statistical value
                    elif self.extract_number(cell_text):
                        potential_value = self.extract_number(cell_text)
                
                # If we found both player and value, add to results
                if potential_player and potential_value:
                    # Clean up player name
                    player_name = potential_player.strip()
                    # Filter out obvious non-player entries
                    if not any(word in player_name.lower() for word in 
                             ['total', 'average', 'rank', 'position', 'header', 'jumlah', 'klub', 'team']):
                        stats.append({
                            'player_name': player_name,
                            'value': potential_value,
                            'raw_text': self.clean_text(row.get_text()),
                            'row_index': i
                        })
                        print(f"Row {i}: {player_name} = {potential_value}")
        
        return stats

    def looks_like_team_name(self, text):
        """Check if text looks like a team name rather than player name"""
        team_indicators = ['fc', 'united', 'club', 'persib', 'persija', 'arema', 'bali', 'psm']
        return any(indicator in text.lower() for indicator in team_indicators)

    def is_percentage(self, text):
        """Check if text represents a percentage"""
        return '%' in text or (self.extract_number(text) and float(self.extract_number(text)) <= 100)

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace, newlines, and special characters
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Remove common HTML entities
        cleaned = cleaned.replace('&nbsp;', ' ').replace('&amp;', '&')
        return cleaned

    def extract_number(self, text):
        """Extract numerical value from text"""
        if not text:
            return None
        # Look for numbers (including decimals and percentages)
        numbers = re.findall(r'\d+(?:\.\d+)?', str(text))
        return numbers[0] if numbers else None

    def extract_from_table(self, table):
        """Extract player statistics from HTML table"""
        stats = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                player_name = self.clean_text(cells[0].get_text())
                stat_value = self.extract_number(cells[-1].get_text())
                
                if player_name and stat_value and len(player_name) > 2:
                    # Filter out obvious non-player entries
                    if not any(word in player_name.lower() for word in 
                             ['total', 'average', 'rank', 'position', 'klub', 'team']) and \
                       not self.looks_like_team_name(player_name):
                        stats.append({
                            'player_name': player_name,
                            'value': stat_value,
                            'raw_text': self.clean_text(row.get_text())
                        })
        
        return stats

    def match_player_by_fullname(self, scraped_name, all_players):
        """Match a scraped player name to a player from teams_info by fullName"""
        scraped_name_clean = self.clean_text(scraped_name).upper()
        
        # Try exact match with fullName first
        for player in all_players:
            if player.get('fullName', '').upper() == scraped_name_clean:
                return player
        
        # Try exact match with name
        for player in all_players:
            if player.get('name', '').upper() == scraped_name_clean:
                return player
        
        # Try partial match with fullName (contains scraped name)
        for player in all_players:
            full_name = player.get('fullName', '').upper()
            if scraped_name_clean in full_name or full_name in scraped_name_clean:
                return player
        
        # Try partial match with name
        for player in all_players:
            name = player.get('name', '').upper()
            if scraped_name_clean in name or name in scraped_name_clean:
                return player
        
        return None

    def scrape_comprehensive_player_statistics(self, csv_filename="enhanced_player_stats.csv"):
        """Scrape statistics for all players from teams_info.json using club-based scraping and fullName matching"""
        if not self.all_players:
            print("No players found in teams_info.json")
            return
        
        print(f"Starting comprehensive player statistics scraping...")
        print(f"Found {len(self.all_players)} players across all teams")
        print()
        
        # Initialize enhanced CSV manager with player data
        enhanced_csv_manager = EnhancedPlayerCSVDataManager(self.all_players)
        
        # Get unique team IDs from loaded players
        team_ids = list(set(player['team_id'] for player in self.all_players))
        
        # Group players by team for easier matching
        players_by_team = {}
        for player in self.all_players:
            team_id = player['team_id']
            if team_id not in players_by_team:
                players_by_team[team_id] = []
            players_by_team[team_id].append(player)
        
        success_count = 0
        total_operations = len(self.statistics_types) * len(team_ids)
        
        # Scrape statistics for each team and statistic type
        for stat_code, stat_name in self.statistics_types.items():
            print(f"\nScraping {stat_name}...")
            
            for team_id in team_ids:
                team_name = self.clubs.get(team_id, f'Club {team_id}')
                team_players = players_by_team.get(team_id, [])
                
                print(f"  Processing {team_name} ({len(team_players)} players)...")
                
                # Scrape this statistic for this team
                results = self.scrape_statistic(stat_code, team_id)
                
                if results and results.get('player_statistics'):
                    success_count += 1
                    
                    # Match scraped players to our loaded players by fullName
                    for player_stat in results['player_statistics']:
                        scraped_name = player_stat['player_name']
                        value = player_stat['value']
                        
                        # Try to match this scraped player to our loaded players
                        matched_player = self.match_player_by_fullname(scraped_name, team_players)
                        
                        if matched_player:
                            full_name = matched_player['fullName']
                            enhanced_csv_manager.add_player_statistic(full_name, stat_name, value)
                            print(f"    Matched {scraped_name} → {full_name}: {value}")
                        else:
                            print(f"    Could not match: {scraped_name}")
                else:
                    print(f"    Failed to fetch data for {stat_name} - {team_name}")
                
                # Rate limiting
                time.sleep(1)
        
        print(f"\nCompleted! Successfully scraped {success_count}/{total_operations} operations")
        
        # Export comprehensive CSV
        enhanced_csv_manager.export_comprehensive_csv(csv_filename, self.statistics_types)
        return enhanced_csv_manager

    def scrape_club_aggregated_statistics(self, csv_filename="club_stats.csv"):
        """Scrape and aggregate player statistics per club from teams_info.json"""
        if not self.all_players:
            print("No players found in teams_info.json")
            return
        
        print(f"Starting club-level statistics aggregation...")
        print(f"Found {len(self.all_players)} players across all teams")
        print()
        
        # Initialize club stats CSV manager
        club_csv_manager = ClubStatsCSVDataManager(self.clubs)
        
        # Get unique team IDs from loaded players
        team_ids = list(set(player['team_id'] for player in self.all_players))
        
        # Group players by team for easier matching
        players_by_team = {}
        for player in self.all_players:
            team_id = player['team_id']
            if team_id not in players_by_team:
                players_by_team[team_id] = []
            players_by_team[team_id].append(player)
        
        success_count = 0
        total_operations = len(self.statistics_types) * len(team_ids)
        
        # Scrape statistics for each team and statistic type
        for stat_code, stat_name in self.statistics_types.items():
            print(f"\nScraping {stat_name}...")
            
            for team_id in team_ids:
                team_name = self.clubs.get(team_id, f'Club {team_id}')
                team_players = players_by_team.get(team_id, [])
                
                print(f"  Processing {team_name} ({len(team_players)} players)...")
                
                # Scrape this statistic for this team
                results = self.scrape_statistic(stat_code, team_id)
                
                if results and results.get('player_statistics'):
                    success_count += 1
                    
                    # Aggregate all player stats for this club
                    club_total = 0
                    matched_players = 0
                    
                    for player_stat in results['player_statistics']:
                        scraped_name = player_stat['player_name']
                        value = player_stat['value']
                        
                        # Try to match this scraped player to our loaded players
                        matched_player = self.match_player_by_fullname(scraped_name, team_players)
                        
                        if matched_player:
                            try:
                                numeric_value = float(value) if value else 0
                                club_total += numeric_value
                                matched_players += 1
                                print(f"    Matched {scraped_name}: {value}")
                            except (ValueError, TypeError):
                                print(f"    Matched {scraped_name}: non-numeric value '{value}'")
                        else:
                            print(f"    Could not match: {scraped_name}")
                    
                    # Add the aggregated value to club stats
                    club_csv_manager.add_club_statistic(team_id, stat_name, club_total)
                    print(f"    Club total for {stat_name}: {club_total} (from {matched_players} players)")
                    
                else:
                    print(f"    Failed to fetch data for {stat_name} - {team_name}")
                    # Set club stat to 0 when no data is available
                    club_csv_manager.add_club_statistic(team_id, stat_name, 0)
                
                # Rate limiting
                time.sleep(1)
        
        print(f"\nCompleted! Successfully scraped {success_count}/{total_operations} operations")
        
        # Export club aggregated CSV
        club_csv_manager.export_club_stats_csv(csv_filename, self.statistics_types)
        return club_csv_manager

    def display_results(self, results):
        """Display results in a readable format"""
        if not results:
            print("No results to display")
            return
            
        print("="*60)
        print(f"STATISTIC: {results['statistic_name']} ({results['statistic_type']})")
        print(f"CLUB: {results['club_name']} (ID: {results['club_id']})")
        print("="*60)
        
        if results.get('player_statistics'):
            print(f"Found {results['total_players']} player(s) with statistics:")
            print("-" * 60)
            
            # Display in the requested format: "PLAYER NAME = VALUE"
            for player_stat in results['player_statistics']:
                player_name = player_stat['player_name']
                value = player_stat['value']
                print(f"{player_name} = {value}")
            
            print("-" * 60)
            print(f"Total players found: {results['total_players']}")
            
        else:
            print("No player statistics found in the response")
            print(f"Page Title: {results['title']}")
            print(f"HTML Content Length: {results['html_length']} characters")
            print("\nThis might mean:")
            print("1. The page requires authentication")
            print("2. The data is loaded via JavaScript after page load")
            print("3. The HTML structure is different than expected")
            print("4. The statistic type is not available for this club")
        
        print()

    def scrape_all_statistics(self, club_ids=None, csv_export=False, csv_filename="player_stats.csv", silent=False):
        """Scrape all available statistics for specified clubs"""
        if club_ids is None:
            club_ids = list(self.clubs.keys())
        
        if not silent:
            print("Starting Indonesia Super League Player Statistics Scraper...")
            print(f"Target URL: {self.base_url}")
            print(f"Available statistics: {len(self.statistics_types)}")
            print(f"Clubs to scrape: {len(club_ids)}")
            if csv_export:
                print(f"CSV export enabled: {csv_filename}")
            print()
        
        success_count = 0
        total_operations = len(self.statistics_types) * len(club_ids)
        
        for stat_code, stat_name in self.statistics_types.items():
            for club_id in club_ids:
                club_name = self.clubs.get(club_id, f'Club {club_id}')
                
                if not silent:
                    print(f"Fetching: {stat_name} for {club_name}...")
                
                results = self.scrape_statistic(stat_code, club_id)
                
                if results and results.get('player_statistics'):
                    if csv_export:
                        # Add data to CSV manager
                        self.csv_manager.add_statistic_data(
                            stat_code, stat_name, club_name, results['player_statistics']
                        )
                    
                    if not silent:
                        self.display_results(results)
                    success_count += 1
                else:
                    if not silent:
                        print(f"Failed to fetch data for {stat_name} - {club_name}")
                        print()
                
                # Small delay to be respectful to the server
                time.sleep(1)
        
        # Export to CSV if requested
        if csv_export:
            if success_count > 0:
                self.csv_manager.export_to_csv(csv_filename, self.statistics_types)
            else:
                print("No data collected, CSV not created")
        
        if not silent:
            print(f"\nCompleted! Successfully scraped {success_count}/{total_operations} operations")

    def scrape_single_statistic(self, stat_code, club_ids=None, csv_export=False, csv_filename="player_stats.csv"):
        """Scrape a single statistic for specified clubs"""
        if stat_code not in self.statistics_types:
            print(f"Invalid statistic code: {stat_code}")
            print(f"Available codes: {list(self.statistics_types.keys())}")
            return
        
        if club_ids is None:
            club_ids = list(self.clubs.keys())
            
        stat_name = self.statistics_types[stat_code]
        
        for club_id in club_ids:
            club_name = self.clubs.get(club_id, f'Club {club_id}')
            print(f"Fetching: {stat_name} for {club_name}...")
            results = self.scrape_statistic(stat_code, club_id)
            
            if results and results.get('player_statistics'):
                if csv_export:
                    # Add data to CSV manager
                    self.csv_manager.add_statistic_data(
                        stat_code, stat_name, club_name, results['player_statistics']
                    )
                
                self.display_results(results)
            else:
                print(f"Failed to fetch data for {stat_name} - {club_name}")
            
            time.sleep(1)
        
        if csv_export:
            self.csv_manager.export_to_csv(csv_filename, {stat_code: stat_name})

def main():
    parser = argparse.ArgumentParser(description='Indonesia Super League Player Statistics Scraper')
    parser.add_argument('statistic', nargs='?', help='Specific statistic code to scrape (e.g., GOAL)')
    parser.add_argument('--csv', action='store_true', help='Export results to CSV file')
    parser.add_argument('--csv-only', action='store_true', help='Only export to CSV, suppress terminal output')
    parser.add_argument('--output', '-o', default='player_stats.csv', help='CSV output filename (default: player_stats.csv)')
    parser.add_argument('--all', action='store_true', help='Scrape all statistics')
    parser.add_argument('--enhanced', action='store_true', help='Scrape comprehensive player data using teams_info.json')
    parser.add_argument('--club-stats', action='store_true', help='Scrape and aggregate statistics per club (outputs club-level totals)')
    parser.add_argument('--club', type=int, help='Specific club ID to scrape (for testing)')
    
    args = parser.parse_args()
    
    scraper = ILeaguePlayerScraper()
    
    # Handle CSV-only mode
    csv_export = args.csv or args.csv_only
    silent_mode = args.csv_only
    
    # Handle club selection
    club_ids = [args.club] if args.club else None
    
    if args.statistic:
        # Scrape specific statistic
        stat_code = args.statistic.upper()
        scraper.scrape_single_statistic(stat_code, club_ids=club_ids, csv_export=csv_export, csv_filename=args.output)
    elif args.all:
        # Scrape all statistics
        scraper.scrape_all_statistics(club_ids=club_ids, csv_export=csv_export, csv_filename=args.output, silent=silent_mode)
    elif args.enhanced:
        # Scrape comprehensive player statistics using teams_info.json
        scraper.scrape_comprehensive_player_statistics(csv_filename=args.output)
    elif args.club_stats:
        # Scrape and aggregate statistics per club
        scraper.scrape_club_aggregated_statistics(csv_filename=args.output)
    else:
        # Interactive mode - show menu
        if not silent_mode:
            print("Indonesia Super League Player Statistics Scraper")
            print("="*50)
            print("Available statistics:")
            for i, (code, name) in enumerate(scraper.statistics_types.items(), 1):
                print(f"{i:2d}. {name} ({code})")
            print()
            print("Available clubs:")
            for club_id, club_name in scraper.clubs.items():
                print(f"  {club_id}: {club_name}")
            print()
            print("Usage:")
            print("  python player_scraper.py [STATISTIC_CODE] [--csv] [--output filename.csv] [--club CLUB_ID]")
            print("  python player_scraper.py GOAL --csv --club 32")
            print("  python player_scraper.py --all --csv-only")
            print("  python player_scraper.py --enhanced --output enhanced_player_stats.csv")
            print("  python player_scraper.py --club-stats --output club_stats.csv")
            print()
            print("Or run without arguments and enter a choice:")
        
        try:
            choice = input("Enter statistic number (1-22), 'all' for all statistics, 'csv' for CSV export, 'enhanced' for comprehensive player data, or 'club-stats' for club aggregated stats: ").strip()
            
            if choice.lower() == 'all':
                scraper.scrape_all_statistics(club_ids=club_ids, csv_export=csv_export, csv_filename=args.output)
            elif choice.lower() == 'csv':
                scraper.scrape_all_statistics(club_ids=club_ids, csv_export=True, csv_filename=args.output, silent=silent_mode)
            elif choice.lower() == 'enhanced':
                scraper.scrape_comprehensive_player_statistics(csv_filename=args.output)
            elif choice.lower() == 'club-stats':
                scraper.scrape_club_aggregated_statistics(csv_filename=args.output)
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(scraper.statistics_types):
                    stat_code = list(scraper.statistics_types.keys())[choice_num - 1]
                    scraper.scrape_single_statistic(stat_code, club_ids=club_ids, csv_export=csv_export, csv_filename=args.output)
                else:
                    print("Invalid choice number")
            else:
                print("Invalid input")
                
        except KeyboardInterrupt:
            print("\nScraping cancelled by user")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()