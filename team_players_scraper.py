#!/usr/bin/env python3
"""
Indonesia Super League Team Players Scraper
Scrapes player information from each team's squad page
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from pathlib import Path


class TeamPlayersScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.teams_data = self.load_teams_data()
        
    def load_teams_data(self):
        """Load teams data from 25_26_teams.json"""
        try:
            script_dir = Path(__file__).parent
            json_file = script_dir / '25_26_teams.json'
            
            with open(json_file, 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
            
            print(f"Loaded {len(teams_data)} teams from {json_file}")
            return teams_data
            
        except FileNotFoundError:
            print(f"Error: Could not find 25_26_teams.json file")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Error parsing 25_26_teams.json: {e}")
            return []
        except Exception as e:
            print(f"Error: Unexpected error loading teams: {e}")
            return []
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = cleaned.replace('&nbsp;', ' ').replace('&amp;', '&')
        return cleaned
    
    def extract_number(self, text):
        """Extract numerical value from text"""
        if not text:
            return None
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else None
    
    def scrape_player_details(self, player_url):
        """Scrape additional player details from individual player page"""
        try:
            print(f"    Fetching player details from: {player_url}")
            
            response = self.session.get(player_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            player_details = {
                'fullName': '',
                'posisi': ''
            }
            
            # Find the player detail section
            player_section = soup.find('div', class_='item-player single-player')
            if not player_section:
                print(f"    No player detail section found")
                return player_details
            
            # Find the info table
            info_player = player_section.find('div', class_='info-player')
            if not info_player:
                print(f"    No info-player section found")
                return player_details
            
            table = info_player.find('table')
            if not table:
                print(f"    No table found in info-player section")
                return player_details
            
            # Extract full name - look for td with specific styling, but exclude ones with images/links
            full_name_cells = table.find_all('td', style=re.compile(r'font-weight:\s*bold.*text-align:\s*center.*font-size:\s*18px'))
            for cell in full_name_cells:
                # Skip cells that contain images or links (club logo section)
                if cell.find('img') or cell.find('a'):
                    continue
                
                full_name = self.clean_text(cell.get_text())
                if full_name and len(full_name) > 3:  # Ensure it's actual name text
                    player_details['fullName'] = full_name
                    print(f"    Found full name: {full_name}")
                    break
            
            # Extract position - look for "Posisi" label
            all_cells = table.find_all('td')
            for i, cell in enumerate(all_cells):
                cell_text = self.clean_text(cell.get_text())
                if cell_text == 'Posisi' and i + 1 < len(all_cells):
                    position_cell = all_cells[i + 1]
                    position = self.clean_text(position_cell.get_text())
                    if position:
                        player_details['posisi'] = position
                        print(f"    Found position: {position}")
                    break
            
            return player_details
            
        except requests.RequestException as e:
            print(f"    Error fetching player details: {e}")
            return {'fullName': '', 'posisi': ''}
        except Exception as e:
            print(f"    Error processing player details: {e}")
            return {'fullName': '', 'posisi': ''}
    
    def scrape_team_players(self, team):
        """Scrape players from a team's detail page"""
        try:
            print(f"Scraping players for {team['name']}...")
            
            response = self.session.get(team['details_url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the squad section
            squad_section = soup.find('div', id='squad')
            if not squad_section:
                print(f"  No squad section found for {team['name']}")
                return []
            
            players = []
            
            # Find all player containers
            player_containers = squad_section.find_all('div', class_='col-player-club')
            
            print(f"  Found {len(player_containers)} player containers")
            
            for container in player_containers:
                player_item = container.find('div', class_='item-player')
                if not player_item:
                    continue
                
                player_data = self.extract_player_data(player_item)
                if player_data:
                    players.append(player_data)
                    print(f"    Extracted: {player_data['name']}")
            
            print(f"  Successfully extracted {len(players)} players")
            return players
            
        except requests.RequestException as e:
            print(f"  Error fetching data for {team['name']}: {e}")
            return []
        except Exception as e:
            print(f"  Error processing data for {team['name']}: {e}")
            return []
    
    def extract_player_data(self, player_item):
        """Extract player data from item-player div"""
        try:
            player_data = {
                'name': '',
                'negara': '',
                'penampilan': 0,
                'usia': 0,
                'detailsPlayerUrl': '',
                'pictureUrl': '',
                'fullName': '',
                'posisi': ''
            }
            
            # Find player detail URL from "Detail Pemain" link
            detail_links = player_item.find_all('a', string=re.compile(r'Detail Pemain\s*'))
            if not detail_links:
                # Alternative: look for links with "Detail Pemain" in text content
                detail_links = [link for link in player_item.find_all('a') 
                               if 'Detail Pemain' in link.get_text()]
            
            if detail_links:
                href = detail_links[0].get('href')
                if href:
                    if href.startswith('/'):
                        player_data['detailsPlayerUrl'] = f"https://ileague.id{href}"
                    else:
                        player_data['detailsPlayerUrl'] = href
            
            # Find player image
            player_img = player_item.find('img')
            if player_img and player_img.get('src'):
                player_data['pictureUrl'] = player_img.get('src')
            
            # Find all table cells with player information
            table_cells = player_item.find_all('td')
            
            for i, cell in enumerate(table_cells):
                cell_text = self.clean_text(cell.get_text())
                
                # Look for player name (usually in a cell with specific styling)
                if (cell.get('style') and 
                    'font-weight: bold' in cell.get('style', '') and 
                    'text-align: center' in cell.get('style', '') and
                    cell_text and len(cell_text) > 1):
                    player_data['name'] = cell_text
                
                # Look for country information
                if cell_text == 'Negara' and i + 1 < len(table_cells):
                    next_cell = table_cells[i + 1]
                    country = self.clean_text(next_cell.get_text())
                    if country:
                        player_data['negara'] = country
                
                # Look for appearances
                if cell_text == 'Penampilan' and i + 1 < len(table_cells):
                    next_cell = table_cells[i + 1]
                    #print({next_cell})
                    appearances = self.extract_number(next_cell.get_text())
                    if appearances is not None:
                        player_data['penampilan'] = appearances
                        print(f"    Found Penampilan: {appearances}")
                    else:
                        print(f"    NOT Found Penampilan: {appearances}")
                
                # Look for age
                if cell_text == 'Usia' and i + 1 < len(table_cells):
                    next_cell = table_cells[i + 1]
                    age = self.extract_number(next_cell.get_text())
                    if age is not None:
                        player_data['usia'] = age
            
            # Alternative parsing strategy if the above doesn't work
            if not player_data['name']:
                # Look for name in bold text
                bold_texts = player_item.find_all('td', style=re.compile(r'font-weight:\s*bold'))
                for bold_text in bold_texts:
                    text = self.clean_text(bold_text.get_text())
                    if text and len(text) > 1 and not text.isdigit():
                        player_data['name'] = text
                        break
            
            # Look for country in specific patterns
            if not player_data['negara']:
                country_patterns = [
                    r'Negara[:\s]*([A-Z]+)',
                    r'Country[:\s]*([A-Z]+)',
                ]
                text_content = player_item.get_text()
                for pattern in country_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        player_data['negara'] = match.group(1)
                        break
            
            # Only return if we have at least the player name
            if player_data['name']:
                # Fetch additional player details if URL is available
                if player_data['detailsPlayerUrl']:
                    player_details = self.scrape_player_details(player_data['detailsPlayerUrl'])
                    player_data['fullName'] = player_details['fullName']
                    player_data['posisi'] = player_details['posisi']
                    
                    # Small delay to be respectful when scraping individual player pages
                    time.sleep(0.5)
                
                return player_data
            else:
                return None
                
        except Exception as e:
            print(f"    Error extracting player data: {e}")
            return None
    
    def scrape_all_teams(self):
        """Scrape players from all teams"""
        print("Starting Indonesia Super League Team Players Scraper...")
        print(f"Found {len(self.teams_data)} teams to scrape")
        print()
        
        teams_info = {
            'teams': [],
            'retrieveDate': datetime.now().isoformat(),
            'totalClub': len(self.teams_data),
            'totalPlayers': 0
        }
        
        total_players = 0
        
        for team in self.teams_data:
            players = self.scrape_team_players(team)
            
            team_info = {
                'id': team['id'],
                'name': team['name'],
                'details_url': team['details_url'],
                'players': players
            }
            
            teams_info['teams'].append(team_info)
            total_players += len(players)
            
            print(f"  Total players so far: {total_players}")
            print()
            
            # Rate limiting - be respectful to the server
            time.sleep(1)
        
        teams_info['totalPlayers'] = total_players
        
        print(f"Completed! Successfully scraped {total_players} players from {len(self.teams_data)} teams")
        
        return teams_info
    
    def save_to_json(self, teams_info, filename='data/teams_info.json'):
        """Save teams info to JSON file"""
        try:
            # Ensure data directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(teams_info, f, ensure_ascii=False, indent=2)
            
            print(f"Data saved to {filename}")
            print(f"Total teams: {teams_info['totalClub']}")
            print(f"Total players: {teams_info['totalPlayers']}")
            return True
            
        except Exception as e:
            print(f"Error saving data to {filename}: {e}")
            return False


def main():
    scraper = TeamPlayersScraper()
    
    if not scraper.teams_data:
        print("No teams data available. Please ensure 25_26_teams.json exists.")
        return
    
    # Scrape all teams
    teams_info = scraper.scrape_all_teams()
    
    # Save to JSON file
    scraper.save_to_json(teams_info)


if __name__ == "__main__":
    main()