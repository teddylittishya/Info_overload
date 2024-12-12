import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
import re

class NCBIScraper:
    def __init__(self, output_file: str = 'ncbi_data.json'):
        """
        Initialize the NCBI Medical Information Scraper
        
        :param output_file: File to save scraped data
        """
        self.base_url = 'https://www.ncbi.nlm.nih.gov'
        self.output_file = output_file
        self.scraped_data = []
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='ncbi_scraper.log'
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
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def scrape_pubmed(self, search_term: str, max_results: int = 50) -> List[Dict]:
        """
        Comprehensive scraping of PubMed articles
        
        :param search_term: Medical research topic to search
        :param max_results: Maximum number of results to retrieve
        :return: List of detailed article information
        """
        # URL encode the search term
        encoded_term = quote(search_term)
        search_url = f"{self.base_url}/pubmed/?term={encoded_term}&size={max_results}"
        
        html_content = self._get_html_content(search_url)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []

        for article_elem in soup.find_all('div', class_='docsum-content'):
            try:
                # Extract title
                title_elem = article_elem.find('a', class_='docsum-title')
                title = title_elem.text.strip() if title_elem else 'N/A'

                # Extract authors
                authors_elem = article_elem.find('span', class_='docsum-authors')
                authors = authors_elem.text.strip() if authors_elem else 'N/A'

                # Extract journal information
                journal_elem = article_elem.find('span', class_='docsum-journal-citation')
                journal = journal_elem.text.strip() if journal_elem else 'N/A'

                # Extract publication date
                date_elem = article_elem.find('span', class_='docsum-journal-citation full-journal-citation')
                pub_date = date_elem.text.strip() if date_elem else 'N/A'

                # Construct full article URL
                article_url = urljoin(self.base_url, title_elem['href']) if title_elem and 'href' in title_elem.attrs else 'N/A'

                # Extract abstract (requires additional request)
                abstract = self._get_article_abstract(article_url)

                article_data = {
                    'title': title,
                    'authors': authors,
                    'journal': journal,
                    'publication_date': pub_date,
                    'url': article_url,
                    'abstract': abstract
                }
                articles.append(article_data)

                # Implement rate limiting
                time.sleep(0.5)

            except Exception as e:
                self.logger.warning(f"Error parsing article: {e}")

        return articles

    def _get_article_abstract(self, article_url: str) -> str:
        """
        Retrieve article abstract from its detailed page
        
        :param article_url: URL of the specific article
        :return: Abstract text or 'N/A'
        """
        try:
            html_content = self._get_html_content(article_url)
            if not html_content:
                return 'N/A'

            soup = BeautifulSoup(html_content, 'html.parser')
            abstract_elem = soup.find('div', class_='abstract-content')
            
            if abstract_elem:
                # Clean up abstract text
                abstract = abstract_elem.get_text(strip=True)
                return abstract
            return 'N/A'
        except Exception as e:
            self.logger.warning(f"Error extracting abstract: {e}")
            return 'N/A'

    def scrape_gene_database(self, gene_name: str) -> List[Dict]:
        """
        Scrape gene information from NCBI Gene database
        
        :param gene_name: Name or symbol of the gene
        :return: List of gene-related information
        """
        search_url = f"{self.base_url}/gene/?term={quote(gene_name)}"
        
        html_content = self._get_html_content(search_url)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        gene_results = []

        for gene_elem in soup.find_all('div', class_='gene-result'):
            try:
                # Extract gene details
                name_elem = gene_elem.find('h3', class_='gene-name')
                description_elem = gene_elem.find('p', class_='gene-description')
                
                gene_data = {
                    'name': name_elem.text.strip() if name_elem else 'N/A',
                    'description': description_elem.text.strip() if description_elem else 'N/A',
                    'url': urljoin(self.base_url, name_elem.find('a')['href']) if name_elem and name_elem.find('a') else 'N/A'
                }
                gene_results.append(gene_data)
            except Exception as e:
                self.logger.warning(f"Error parsing gene information: {e}")

        return gene_results

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

    def run_comprehensive_scrape(self, search_term: str):
        """
        Run comprehensive scraping across NCBI resources
        
        :param search_term: Term to search across NCBI sources
        """
        self.logger.info(f"Starting comprehensive NCBI scraping for term: {search_term}")
        
        # Scrape multiple NCBI sources
        pubmed_results = self.scrape_pubmed(search_term)
        gene_results = self.scrape_gene_database(search_term)
        
        # Combine and save results
        self.scraped_data = {
            'pubmed_articles': pubmed_results,
            'gene_information': gene_results
        }
        self.save_to_json(self.scraped_data)
        
        self.logger.info(f"NCBI scraping completed. Total PubMed results: {len(pubmed_results)}, Total Gene results: {len(gene_results)}")

def main():
    # Example usage
    scraper = NCBIScraper()
    
    # Run scraper for a specific medical term
    scraper.run_comprehensive_scrape("breast cancer")

if __name__ == "__main__":
    main()

# Requirements (install via pip):
# requests
# beautifulsoup4
# pandas

# Ethical and Legal Note:
# 1. Respect NCBI's robots.txt and terms of service
# 2. Use official APIs when possible
# 3. Implement responsible scraping practices
# 4. Add appropriate delays between requests
# 5. Do not overload NCBI servers
