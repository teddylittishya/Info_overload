import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

class MedicalInfoScraper:
    def __init__(self, sources: List[str], output_file: str = 'medical_data.json'):
        """
        Initialize the Medical Information Scraper
        
        :param sources: List of URLs to scrape medical information from
        :param output_file: File to save scraped data
        """
        self.sources = sources
        self.output_file = output_file
        self.scraped_data = []
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='medical_scraper.log'
        )
        self.logger = logging.getLogger()

    def _get_html_content(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a given URL
        
        :param url: URL to fetch
        :return: HTML content or None if fetch fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def scrape_pubmed(self, search_term: str, max_results: int = 50) -> List[Dict]:
        """
        Scrape medical research articles from PubMed
        
        :param search_term: Medical research topic to search
        :param max_results: Maximum number of results to retrieve
        :return: List of scraped article details
        """
        base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        search_url = f"{base_url}?term={search_term}&size={max_results}"
        
        html_content = self._get_html_content(search_url)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        for article_elem in soup.find_all('article', class_='full-docsum'):
            try:
                title_elem = article_elem.find('a', class_='docsum-title')
                authors_elem = article_elem.find('span', class_='docsum-authors')
                journal_elem = article_elem.find('span', class_='docsum-journal-citation')

                article_data = {
                    'title': title_elem.text.strip() if title_elem else 'N/A',
                    'authors': authors_elem.text.strip() if authors_elem else 'N/A',
                    'journal': journal_elem.text.strip() if journal_elem else 'N/A',
                    'url': urljoin(base_url, title_elem['href']) if title_elem and 'href' in title_elem.attrs else 'N/A'
                }
                articles.append(article_data)
            except Exception as e:
                self.logger.warning(f"Error parsing article: {e}")

        return articles

    def scrape_clinical_trials(self, condition: str, max_results: int = 30) -> List[Dict]:
        """
        Scrape clinical trials information
        
        :param condition: Medical condition to search clinical trials for
        :param max_results: Maximum number of trials to retrieve
        :return: List of clinical trial details
        """
        base_url = "https://clinicaltrials.gov/search"
        params = {
            'term': condition,
            'lim': max_results
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            trials = []
            
            for trial_elem in soup.find_all('div', class_='trial-result'):
                trial_data = {
                    'title': trial_elem.find('h3').text.strip() if trial_elem.find('h3') else 'N/A',
                    'condition': condition,
                    'status': trial_elem.find('span', class_='trial-status').text.strip() if trial_elem.find('span', class_='trial-status') else 'N/A'
                }
                trials.append(trial_data)
            
            return trials
        
        except requests.RequestException as e:
            self.logger.error(f"Error scraping clinical trials: {e}")
            return []

    def save_to_json(self, data: List[Dict]):
        """
        Save scraped data to JSON file
        
        :param data: List of dictionaries to save
        """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Data saved to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")

    def run_scraping(self, search_term: str):
        """
        Run comprehensive medical information scraping
        
        :param search_term: Term to search across sources
        """
        self.logger.info(f"Starting scraping for term: {search_term}")
        
        # Scrape multiple sources
        pubmed_results = self.scrape_pubmed(search_term)
        clinical_trials_results = self.scrape_clinical_trials(search_term)
        
        # Combine and save results
        self.scraped_data = pubmed_results + clinical_trials_results
        self.save_to_json(self.scraped_data)
        
        self.logger.info(f"Scraping completed. Total results: {len(self.scraped_data)}")

def main():
    # Example usage
    scraper = MedicalInfoScraper(
        sources=[
            'https://pubmed.ncbi.nlm.nih.gov/',
            'https://clinicaltrials.gov/'
        ]
    )
    
    # Run scraper for a specific medical condition
    scraper.run_scraping("diabetes management")

if __name__ == "__main__":
    main()

# Requirements (install via pip):
# requests
# beautifulsoup4
# pandas

# Ethical and Legal Note:
# Always ensure you have permission to scrape websites.
# Respect robots.txt and website terms of service.
# Use rate limiting and be considerate of server load.
