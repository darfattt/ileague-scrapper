#!/usr/bin/env python3
"""
Indonesia Super League Football Statistics Scraper
Scrapes football statistics from ileague.id
"""

import requests
from bs4 import BeautifulSoup
import sys
import time
import re
import csv
import argparse
from collections import defaultdict

class CSVDataManager:
    def __init__(self):
        self.team_data = defaultdict(dict)
        
    def add_statistic_data(self, stat_type, stat_name, club_statistics):
        """Add statistics data for a specific type"""
        for club_stat in club_statistics:
            team_name = club_stat['club_name']
            value = club_stat['value']
            self.team_data[team_name][stat_name] = value
    
    def export_to_csv(self, filename, statistics_types):
        """Export all collected data to CSV file"""
        if not self.team_data:
            print("No data to export")
            return False
            
        # Get all team names
        teams = sorted(self.team_data.keys())
        
        # Get all statistic names (use Indonesian names)
        stat_columns = [stat_name for stat_name in statistics_types.values()]
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = ['TEAM'] + stat_columns
            writer.writerow(header)
            
            # Write data rows
            for team in teams:
                row = [team]
                for stat_name in stat_columns:
                    value = self.team_data[team].get(stat_name, '')
                    row.append(value)
                writer.writerow(row)
        
        print(f"Data exported to {filename}")
        print(f"Teams: {len(teams)}")
        print(f"Statistics: {len(stat_columns)}")
        return True

class ILeagueScraper:
    def __init__(self):
        self.base_url = "https://ileague.id/top_actions/club/BRI_SUPER_LEAGUE_2025-26"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.statistics_types = {
            'AKURASIUMPAN': 'Akurasi Umpan',
            'AKURASITEMBAKAN': 'Akurasi Tembakan', 
            'KARTUKUNING': 'Kartu Kuning',
            'KARTUMERAH': 'Kartu Merah',
            'OFFSIDE': 'Offside',
            'UMPANGAGAL': 'Umpan Gagal',
            'UMPANSUKSES': 'Umpan Sukses',
            'PELANGGARAN': 'Pelanggaran',
            'PENGUASAANBOLAPERSEN': 'Penguasaan Bola',
            'TEKELSUKSES': 'Tekel Sukses',
            'TEMBAKANDIBLOK': 'Tembakan Diblok',
            'TEMBAKANKEGAWANG': 'Tembakan ke Gawang',
            'TENDANGANSUDUT': 'Tendangan Sudut',
            'TOTALUMPAN': 'Total Umpan',
            'TOTALTEMBAKAN': 'Total Tembakan'
        }
        
        self.csv_manager = CSVDataManager()

    def scrape_statistic(self, statistic_type):
        """Scrape a specific statistic type"""
        try:
            payload = {'statistik': statistic_type}
            response = self.session.post(self.base_url, data=payload, timeout=30)
            response.raise_for_status()
            
            return self.parse_statistics(response.text, statistic_type)
            
        except requests.RequestException as e:
            print(f"Error fetching data for {statistic_type}: {e}")
            return None
        except Exception as e:
            print(f"Error processing data for {statistic_type}: {e}")
            return None

    def parse_statistics(self, html_content, stat_type):
        """Parse HTML content to extract club statistics"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        club_stats = []
        
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
                club_stats = self.extract_from_specific_table(stats_table)
                print(f"Extracted {len(club_stats)} clubs from main statistics table")
            else:
                print("Statistics table not found in the expected div")
        
        # Fallback: Look for any table with the background-color-2 class
        if not club_stats:
            tables = soup.find_all('table', class_='background-color-2')
            for table in tables:
                extracted_stats = self.extract_from_specific_table(table)
                if extracted_stats:
                    club_stats.extend(extracted_stats)
                    print(f"Found {len(extracted_stats)} clubs in fallback table")
        
        # Additional fallback: Look for any table with statistics data
        if not club_stats:
            all_tables = soup.find_all('table')
            for table in all_tables:
                extracted_stats = self.extract_from_table(table)
                if extracted_stats and len(extracted_stats) >= 10:  # Likely to be club stats
                    club_stats.extend(extracted_stats)
                    print(f"Found {len(extracted_stats)} clubs in general table")
        
        return {
            'statistic_type': stat_type,
            'statistic_name': self.statistics_types.get(stat_type, stat_type),
            'club_statistics': club_stats,
            'total_clubs': len(club_stats),
            'html_length': len(html_content),
            'title': soup.title.string if soup.title else 'No title found'
        }

    def extract_from_specific_table(self, table):
        """Extract club statistics from the specific ileague table structure"""
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
                # Typically: [rank/position, club_name, value, additional_info...]
                # Or: [club_name, value]
                
                # Try to identify club name and value
                potential_club = None
                potential_value = None
                
                for cell in cells:
                    cell_text = self.clean_text(cell.get_text())
                    
                    # Check if this looks like a club name (contains letters, reasonable length)
                    if (len(cell_text) > 3 and 
                        any(c.isalpha() for c in cell_text) and
                        not cell_text.isdigit() and
                        not self.is_percentage(cell_text)):
                        potential_club = cell_text
                    
                    # Check if this looks like a statistical value
                    elif self.extract_number(cell_text):
                        potential_value = self.extract_number(cell_text)
                
                # If we found both club and value, add to results
                if potential_club and potential_value:
                    # Clean up club name
                    club_name = potential_club.strip()
                    # Filter out obvious non-club entries
                    if not any(word in club_name.lower() for word in 
                             ['total', 'average', 'rank', 'position', 'header', 'jumlah']):
                        stats.append({
                            'club_name': club_name,
                            'value': potential_value,
                            'raw_text': self.clean_text(row.get_text()),
                            'row_index': i
                        })
                        print(f"Row {i}: {club_name} = {potential_value}")
        
        return stats

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
        """Extract club statistics from HTML table"""
        stats = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                club_name = self.clean_text(cells[0].get_text())
                stat_value = self.extract_number(cells[-1].get_text())
                
                if club_name and stat_value and len(club_name) > 2:
                    # Filter out obvious non-club entries
                    if not any(word in club_name.lower() for word in ['total', 'average', 'rank', 'position']):
                        stats.append({
                            'club_name': club_name,
                            'value': stat_value,
                            'raw_text': self.clean_text(row.get_text())
                        })
        
        return stats

    def extract_from_container(self, container):
        """Extract club statistics from div containers"""
        stats = []
        
        # Look for patterns like club name followed by number
        text_content = container.get_text()
        
        # Try to find patterns like "Club Name: 85" or "Club Name 85"
        patterns = [
            r'([A-Z\s]+(?:FC|UNITED|CLUB)?)\s*[:\-]?\s*(\d+(?:\.\d+)?)',
            r'(\w+(?:\s+\w+)*)\s+(\d+(?:\.\d+)?)\s*$'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                club_name = self.clean_text(match.group(1))
                value = match.group(2)
                
                if len(club_name) > 3 and club_name.replace(' ', '').isalpha():
                    stats.append({
                        'club_name': club_name,
                        'value': value,
                        'raw_text': match.group(0)
                    })
        
        return stats

    def extract_from_list(self, list_element):
        """Extract club statistics from list elements"""
        stats = []
        items = list_element.find_all(['li', 'dt', 'dd'])
        
        for item in items:
            text = self.clean_text(item.get_text())
            
            # Look for club name and number in list item
            match = re.search(r'([A-Za-z\s]+(?:FC|UNITED|CLUB)?)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
            if match:
                club_name = self.clean_text(match.group(1))
                value = match.group(2)
                
                if len(club_name) > 3:
                    stats.append({
                        'club_name': club_name,
                        'value': value,
                        'raw_text': text
                    })
        
        return stats

    def extract_from_general_content(self, soup):
        """Extract club statistics from general page content"""
        stats = []
        
        # Find all text nodes that might contain club statistics
        all_text = soup.get_text()
        
        # Look for Indonesian football club patterns
        club_patterns = [
            r'([A-Z][A-Za-z\s]+(?:FC|UNITED|BANTEN|JAKARTA|SURABAYA|BANDUNG))\s*[:\-=]?\s*(\d+(?:\.\d+)?)',
            r'(DEWA\s+UNITED[^0-9]*?)(\d+)',
            r'([A-Z]{2,}(?:\s+[A-Z]+)*\s+FC)\s*[:\-=]?\s*(\d+)'
        ]
        
        for pattern in club_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                club_name = self.clean_text(match.group(1))
                value = match.group(2)
                
                if len(club_name) > 5 and value:
                    stats.append({
                        'club_name': club_name,
                        'value': value,
                        'raw_text': match.group(0)
                    })
        
        return stats

    def display_results(self, results):
        """Display results in a readable format"""
        if not results:
            print("No results to display")
            return
            
        print("="*60)
        print(f"STATISTIC: {results['statistic_name']} ({results['statistic_type']})")
        print("="*60)
        
        if results.get('club_statistics'):
            print(f"Found {results['total_clubs']} club(s) with statistics:")
            print("-" * 60)
            
            # Display in the requested format: "CLUB NAME = VALUE"
            for club_stat in results['club_statistics']:
                club_name = club_stat['club_name'].upper()
                value = club_stat['value']
                print(f"{club_name} = {value}")
            
            print("-" * 60)
            print(f"Total clubs found: {results['total_clubs']}")
            
        else:
            print("No club statistics found in the response")
            print(f"Page Title: {results['title']}")
            print(f"HTML Content Length: {results['html_length']} characters")
            print("\nThis might mean:")
            print("1. The page requires authentication")
            print("2. The data is loaded via JavaScript after page load")
            print("3. The HTML structure is different than expected")
            print("4. The statistic type is not available")
        
        print()

    def scrape_all_statistics(self, csv_export=False, csv_filename="football_stats.csv", silent=False):
        """Scrape all available statistics"""
        if not silent:
            print("Starting Indonesia Super League Statistics Scraper...")
            print(f"Target URL: {self.base_url}")
            print(f"Available statistics: {len(self.statistics_types)}")
            if csv_export:
                print(f"CSV export enabled: {csv_filename}")
            print()
        
        success_count = 0
        for stat_code, stat_name in self.statistics_types.items():
            if not silent:
                print(f"Fetching: {stat_name}...")
            
            results = self.scrape_statistic(stat_code)
            
            if results and results.get('club_statistics'):
                if csv_export:
                    # Add data to CSV manager
                    self.csv_manager.add_statistic_data(stat_code, stat_name, results['club_statistics'])
                
                if not silent:
                    self.display_results(results)
                success_count += 1
            else:
                if not silent:
                    print(f"Failed to fetch data for {stat_name}")
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
            print(f"\nCompleted! Successfully scraped {success_count}/{len(self.statistics_types)} statistics")

    def scrape_single_statistic(self, stat_code, csv_export=False, csv_filename="football_stats.csv"):
        """Scrape a single statistic"""
        if stat_code not in self.statistics_types:
            print(f"Invalid statistic code: {stat_code}")
            print(f"Available codes: {list(self.statistics_types.keys())}")
            return
            
        stat_name = self.statistics_types[stat_code]
        print(f"Fetching: {stat_name}...")
        results = self.scrape_statistic(stat_code)
        
        if results and results.get('club_statistics'):
            if csv_export:
                # Add data to CSV manager
                self.csv_manager.add_statistic_data(stat_code, stat_name, results['club_statistics'])
                self.csv_manager.export_to_csv(csv_filename, {stat_code: stat_name})
            
            self.display_results(results)
        else:
            print(f"Failed to fetch data for {stat_name}")

def main():
    parser = argparse.ArgumentParser(description='Indonesia Super League Football Statistics Scraper')
    parser.add_argument('statistic', nargs='?', help='Specific statistic code to scrape (e.g., AKURASIUMPAN)')
    parser.add_argument('--csv', action='store_true', help='Export results to CSV file')
    parser.add_argument('--csv-only', action='store_true', help='Only export to CSV, suppress terminal output')
    parser.add_argument('--output', '-o', default='football_stats.csv', help='CSV output filename (default: football_stats.csv)')
    parser.add_argument('--all', action='store_true', help='Scrape all statistics')
    
    args = parser.parse_args()
    
    scraper = ILeagueScraper()
    
    # Handle CSV-only mode
    csv_export = args.csv or args.csv_only
    silent_mode = args.csv_only
    
    if args.statistic:
        # Scrape specific statistic
        stat_code = args.statistic.upper()
        scraper.scrape_single_statistic(stat_code, csv_export=csv_export, csv_filename=args.output)
    elif args.all:
        # Scrape all statistics
        scraper.scrape_all_statistics(csv_export=csv_export, csv_filename=args.output, silent=silent_mode)
    else:
        # Interactive mode - show menu
        if not silent_mode:
            print("Indonesia Super League Football Statistics Scraper")
            print("="*40)
            print("Available statistics:")
            for i, (code, name) in enumerate(scraper.statistics_types.items(), 1):
                print(f"{i:2d}. {name} ({code})")
            print()
            print("Usage:")
            print("  python scraper.py [STATISTIC_CODE] [--csv] [--output filename.csv]")
            print("  python scraper.py AKURASIUMPAN --csv")
            print("  python scraper.py --all --csv-only")
            print()
            print("Or run without arguments and enter a number:")
        
        try:
            choice = input("Enter statistic number (1-15), 'all' for all statistics, or 'csv' for CSV export: ").strip()
            
            if choice.lower() == 'all':
                scraper.scrape_all_statistics(csv_export=csv_export, csv_filename=args.output)
            elif choice.lower() == 'csv':
                scraper.scrape_all_statistics(csv_export=True, csv_filename=args.output, silent=silent_mode)
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(scraper.statistics_types):
                    stat_code = list(scraper.statistics_types.keys())[choice_num - 1]
                    scraper.scrape_single_statistic(stat_code, csv_export=csv_export, csv_filename=args.output)
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