#!/usr/bin/env python3
"""
Indonesia Super League Player Data Combiner
Combines player information from teams_info.json with statistics from player_stats.csv
"""

import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
import re

class PlayerDataCombiner:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.teams_info_file = self.script_dir / 'data' / 'teams_info.json'
        self.player_stats_file = self.script_dir / 'player_stats.csv'
        self.output_file = self.script_dir / 'data' / 'players_statistics.csv'
        
        # Data containers
        self.teams_data = None
        self.player_stats = {}
        self.all_players = []
        
        # Statistics columns from CSV (excluding Player Name and Team)
        self.stat_columns = [
            'Assist', 'Ball Recovery', 'Block', 'Block Cross', 'Clearance', 
            'Create Chance', 'Cross', 'Dribble Success', 'Foul', 'Fouled', 
            'Free Kick', 'Goal', 'Header Won', 'Intercept', 'Own Goal', 
            'Passing', 'Penalty Goal', 'Saves', 'Shoot Off Target', 
            'Shoot On Target', 'Tackle', 'Yellow Card'
        ]
        
        # Final CSV header as requested
        self.output_header = [
            'Name', 'Player Name', 'Team', 'Country', 'Age', 'Position', 
            'Picture Url', 'Appearances'
        ] + self.stat_columns
        
    def load_teams_info(self):
        """Load player information from teams_info.json"""
        try:
            with open(self.teams_info_file, 'r', encoding='utf-8') as f:
                self.teams_data = json.load(f)
            
            # Extract all players with team information
            self.all_players = []
            for team in self.teams_data['teams']:
                for player in team['players']:
                    player_with_team = player.copy()
                    player_with_team['team_id'] = team['id']
                    player_with_team['team_name'] = team['name']
                    self.all_players.append(player_with_team)
            
            print(f"Loaded {len(self.all_players)} players from {self.teams_info_file}")
            return True
            
        except FileNotFoundError:
            print(f"Error: Could not find {self.teams_info_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.teams_info_file}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error loading teams info: {e}")
            return False
    
    def load_player_stats(self):
        """Load player statistics from player_stats.csv"""
        try:
            self.player_stats = {}
            
            with open(self.player_stats_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_name = row['Player Name']
                    if player_name:  # Skip empty rows
                        self.player_stats[player_name] = row
            
            print(f"Loaded statistics for {len(self.player_stats)} players from {self.player_stats_file}")
            return True
            
        except FileNotFoundError:
            print(f"Error: Could not find {self.player_stats_file}")
            return False
        except Exception as e:
            print(f"Unexpected error loading player stats: {e}")
            return False
    
    def clean_name(self, name):
        """Clean and normalize player name for matching"""
        if not name:
            return ""
        # Remove extra whitespace and convert to uppercase
        cleaned = re.sub(r'\s+', ' ', name.strip().upper())
        return cleaned
    
    def find_player_stats(self, player):
        """Find statistics for a player using various matching strategies with team validation"""
        name = player.get('name', '')
        full_name = player.get('fullName', '')
        team_name = player.get('team_name', '')
        
        # Strategy 1: Exact match with fullName + team validation
        if full_name in self.player_stats:
            stats = self.player_stats[full_name]
            if stats.get('Team', '') == team_name:
                return stats, 'exact_fullname_team'
        
        # Strategy 2: Exact match with name + team validation
        if name in self.player_stats:
            stats = self.player_stats[name]
            if stats.get('Team', '') == team_name:
                return stats, 'exact_name_team'
        
        # Strategy 3: Clean name matching + team validation
        clean_full_name = self.clean_name(full_name)
        clean_name = self.clean_name(name)
        
        for stats_player_name, stats in self.player_stats.items():
            if stats.get('Team', '') == team_name:  # Team must match first
                clean_stats_name = self.clean_name(stats_player_name)
                
                # Try exact match with cleaned names
                if clean_stats_name == clean_full_name:
                    return stats, 'clean_fullname_team'
                elif clean_stats_name == clean_name:
                    return stats, 'clean_name_team'
        
        # Strategy 4: Partial matching + team validation
        # for stats_player_name, stats in self.player_stats.items():
        #     if stats.get('Team', '') == team_name:  # Team must match first
        #         clean_stats_name = self.clean_name(stats_player_name)
                
        #         # Check if cleaned names contain each other
        #         if clean_full_name and clean_stats_name:
        #             if (clean_full_name in clean_stats_name or 
        #                 clean_stats_name in clean_full_name):
        #                 return stats, 'partial_fullname_team'
                
        #         if clean_name and clean_stats_name:
        #             if (clean_name in clean_stats_name or 
        #                 clean_stats_name in clean_name):
        #                 return stats, 'partial_name_team'
        
        # Strategy 5: Fallback - name match without team validation (lower confidence)
        # Only use this if team-validated matching fails
        # clean_full_name = self.clean_name(full_name)
        # clean_name = self.clean_name(name)
        
        # for stats_player_name, stats in self.player_stats.items():
        #     clean_stats_name = self.clean_name(stats_player_name)
            
        #     # Try exact match with cleaned names (no team validation)
        #     if clean_stats_name == clean_full_name:
        #         return stats, 'clean_fullname_no_team'
        #     elif clean_stats_name == clean_name:
        #         return stats, 'clean_name_no_team'
        
        # No match found
        return None, 'no_match'
    
    def create_empty_stats(self):
        """Create empty statistics dictionary with 0 values"""
        empty_stats = {}
        for col in self.stat_columns:
            empty_stats[col] = 0
        return empty_stats
    
    def combine_data(self):
        """Combine player information with statistics"""
        if not self.all_players or not self.player_stats:
            print("Error: Data not loaded properly")
            return False
        
        print("\nCombining player data with statistics...")
        
        combined_data = []
        matched_count = 0
        team_validated_matches = 0
        non_team_matches = 0
        unmatched_players = []
        
        for player in self.all_players:
            # Get basic player info
            name = player.get('name', '')
            full_name = player.get('fullName', '')
            team_name = player.get('team_name', '')
            country = player.get('negara', '')
            age = player.get('usia', '')
            position = player.get('posisi', '')
            picture_url = player.get('pictureUrl', '')
            appearances = player.get('penampilan', '')
            
            # Find matching statistics with team validation
            result = self.find_player_stats(player)
            stats, match_type = result if result else (None, 'no_match')
            
            if stats and match_type != 'no_match':
                matched_count += 1
                if "team" in match_type:
                    team_validated_matches += 1
                    print(f"✓ Matched: {name} ({team_name}) → {stats['Player Name']} ({stats.get('Team', '')}) [{match_type}]")
                else:
                    non_team_matches += 1
                    print(f"⚠ Matched: {name} ({team_name}) → {stats['Player Name']} ({stats.get('Team', '')}) [{match_type}] - DIFFERENT TEAMS")
            else:
                unmatched_players.append(f"{name} ({full_name}) from {team_name}")
                stats = self.create_empty_stats()
                print(f"✗ No stats found for: {name} ({full_name}) from {team_name}")
            
            # Create combined row
            row = {
                'Name': name,
                'Player Name': full_name,
                'Team': team_name,
                'Country': country,
                'Age': age,
                'Position': position,
                'Picture Url': picture_url,
                'Appearances': appearances
            }
            
            # Add statistics (default to 0 if missing)
            for col in self.stat_columns:
                value = stats.get(col, '') if stats else ''
                # Convert empty strings to 0 for numeric columns
                if value == '' or value is None:
                    value = 0
                row[col] = value
            
            combined_data.append(row)
        
        print(f"\nMatching Summary:")
        print(f"Total players: {len(self.all_players)}")
        print(f"Players with stats: {matched_count}")
        print(f"  - Team-validated matches: {team_validated_matches}")
        print(f"  - Non-team validated matches: {non_team_matches}")
        print(f"Players without stats: {len(unmatched_players)}")
        
        if non_team_matches > 0:
            print(f"\n⚠ Warning: {non_team_matches} players matched without team validation!")
            print("These matches may be inaccurate due to team mismatches.")
        
        if unmatched_players:
            print(f"\nUnmatched players ({len(unmatched_players)}):")
            for player in unmatched_players[:10]:  # Show first 10
                print(f"  - {player}")
            if len(unmatched_players) > 10:
                print(f"  ... and {len(unmatched_players) - 10} more")
        
        return combined_data
    
    def export_to_csv(self, combined_data):
        """Export combined data to CSV file"""
        try:
            # Ensure output directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.output_header)
                writer.writeheader()
                writer.writerows(combined_data)
            
            print(f"\nData exported to: {self.output_file}")
            print(f"Total records: {len(combined_data)}")
            print(f"Columns: {len(self.output_header)}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        print("Indonesia Super League Player Data Combiner")
        print("=" * 50)
        
        # Load data
        if not self.load_teams_info():
            return False
        
        if not self.load_player_stats():
            return False
        
        # Combine data
        combined_data = self.combine_data()
        if not combined_data:
            return False
        
        # Export to CSV
        return self.export_to_csv(combined_data)

def main():
    combiner = PlayerDataCombiner()
    
    try:
        success = combiner.run()
        if success:
            print("\n✅ Data combination completed successfully!")
        else:
            print("\n❌ Data combination failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()