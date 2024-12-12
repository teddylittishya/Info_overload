import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

class WHOScraper:
    def __init__(self):
        self.base_url = "https://www.who.int"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

    def scrape_global_health_data(self):
        """
        Scrape global health statistics and disease information
        """
        url = f"{self.base_url}/data/global-health-observatory"
        
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find disease data sections
            data_sections = soup.find_all('div', class_='data-section')
            
            global_health_data = []
            for section in data_sections:
                disease_name = section.find('h3').text
                disease_stats = section.find('div', class_='stats')
                
                global_health_data.append({
                    'disease': disease_name,
                    'global_prevalence': disease_stats.text if disease_stats else 'N/A'
                })
            
            return pd.DataFrame(global_health_data)
        
        except Exception as e:
            print(f"WHO scraping error: {e}")
            return None

    def fetch_who_api_data(self):
        """
        Attempt to fetch data from WHO's public API (hypothetical endpoint)
        """
        api_url = f"{self.base_url}/api/v1/health-data"
        
        try:
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data['diseases'])
            else:
                print("Failed to fetch WHO API data")
                return None
        
        except Exception as e:
            print(f"WHO API error: {e}")
            return None

# Usage
who_scraper = WHOScraper()
who_data = who_scraper.scrape_global_health_data()
print(who_data)
