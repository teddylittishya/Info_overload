import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
import re
import csv
from datetime import datetime

class ClinicalTrialsScraper:
    def __init__(self, output_dir: str = 'clinical_trials_data'):
        """
        Initialize the ClinicalTrials.gov Scraper
        
        :param output_dir: Directory to save scraped data
        """
        self.base_url = 'https://clinicaltrials.gov'
        self.search_url = f'{self.base_url}/ct2/results'
        self.output_dir = output_dir
        
        # Ensure output directory exists
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename=os.path.join(output_dir, 'clinical_trials_scraper.log')
        )
        self.logger = logging.getLogger()

    def _get_html_content(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """
        Fetch HTML content from a given URL
        
        :param url: URL to fetch
        :param params: Optional query parameters
        :return: HTML content or None if fetch fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def search_clinical_trials(self, 
                                condition: str, 
                                max_results: int = 100, 
                                recruitment_status: Optional[str] = None) -> List[Dict]:
        """
        Search and extract clinical trials based on specified criteria
        
        :param condition: Medical condition to search
        :param max_results: Maximum number of results to retrieve
        :param recruitment_status: Filter by recruitment status (e.g., 'Recruiting', 'Completed')
        :return: List of clinical trial details
        """
        # Prepare search parameters
        search_params = {
            'term': condition,
            'mode': 'Advanced'
        }
        
        # Add optional recruitment status filter
        if recruitment_status:
            search_params['rslt'] = recruitment_status

        # Fetch search results page
        html_content = self._get_html_content(self.search_url, params=search_params)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        trials = []

        # Find trial result rows
        trial_rows = soup.find_all('div', class_='tr_results')
        
        for row in trial_rows[:max_results]:
            try:
                # Extract trial details
                title_elem = row.find('a', class_='title')
                title = title_elem.text.strip() if title_elem else 'N/A'
                trial_url = urljoin(self.base_url, title_elem['href']) if title_elem else 'N/A'
                
                # Get detailed trial information
                trial_details = self._scrape_trial_details(trial_url)
                
                # Combine basic and detailed information
                trial_info = {
                    'title': title,
                    'url': trial_url,
                    **trial_details
                }
                
                trials.append(trial_info)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Error parsing trial: {e}")

        return trials

    def _scrape_trial_details(self, trial_url: str) -> Dict:
        """
        Scrape detailed information for a specific clinical trial
        
        :param trial_url: URL of the specific clinical trial
        :return: Dictionary of trial details
        """
        # If URL is invalid, return empty dict
        if trial_url == 'N/A':
            return {}

        html_content = self._get_html_content(trial_url)
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, 'html.parser')
        details = {}

        try:
            # Extract key details using various selectors
            details['nct_number'] = self._extract_text(soup, 'span#nct-id')
            details['status'] = self._extract_text(soup, 'div.recruitment-status')
            details['condition'] = self._extract_text(soup, 'span.condition-title')
            details['sponsor'] = self._extract_text(soup, 'div.sponsor-name')
            details['brief_summary'] = self._extract_text(soup, 'div.brief-summary')
            
            # Extract study design details
            details['study_type'] = self._extract_text(soup, 'div.study-type')
            details['study_phase'] = self._extract_text(soup, 'div.study-phase')
            details['primary_purpose'] = self._extract_text(soup, 'div.primary-purpose')
            
            # Dates
            details['start_date'] = self._extract_text(soup, 'div.start-date')
            details['completion_date'] = self._extract_text(soup, 'div.completion-date')
            
            # Eligibility criteria
            details['eligibility'] = self._extract_eligibility_criteria(soup)
            
        except Exception as e:
            self.logger.warning(f"Error extracting trial details: {e}")

        return details

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """
        Extract text from a specific selector
        
        :param soup: BeautifulSoup object
        :param selector: CSS selector
        :return: Extracted text or 'N/A'
        """
        elem = soup.select_one(selector)
        return elem.text.strip() if elem else 'N/A'

    def _extract_eligibility_criteria(self, soup: BeautifulSoup) -> Dict:
        """
        Extract detailed eligibility criteria
        
        :param soup: BeautifulSoup object
        :return: Dictionary of eligibility criteria
        """
        eligibility = {}
        try:
            # Criteria sections
            criteria_sections = soup.find_all('div', class_='eligibility-criteria')
            
            for section in criteria_sections:
                section_title = section.find('h3')
                section_content = section.find('div', class_='criteria-content')
                
                if section_title and section_content:
                    key = section_title.text.strip().lower().replace(' ', '_')
                    eligibility[key] = section_content.text.strip()
        
        except Exception as e:
            self.logger.warning(f"Error extracting eligibility criteria: {e}")
        
        return eligibility

    def save_to_json(self, data: List[Dict], filename: str = 'clinical_trials.json'):
        """
        Save scraped data to JSON file
        
        :param data: List of dictionaries to save
        :param filename: Output filename
        """
        try:
            filepath = f'{self.output_dir}/{filename}'
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Data saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving JSON data: {e}")

    def save_to_csv(self, data: List[Dict], filename: str = 'clinical_trials.csv'):
        """
        Save scraped data to CSV file
        
        :param data: List of dictionaries to save
        :param filename: Output filename
        """
        try:
            filepath = f'{self.output_dir}/{filename}'
            # Flatten nested dictionaries
            flattened_data = []
            for item in data:
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            flat_item[f"{key}_{sub_key}"] = sub_value
                    else:
                        flat_item[key] = value
                flattened_data.append(flat_item)
            
            # Get all possible keys to ensure all columns are included
            fieldnames = list(set().union(*(d.keys() for d in flattened_data)))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
            
            self.logger.info(f"Data saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving CSV data: {e}")

    def run_comprehensive_scrape(self, 
                                  conditions: List[str], 
                                  max_results: int = 100, 
                                  recruitment_status: Optional[str] = None):
        """
        Run comprehensive scraping for multiple conditions
        
        :param conditions: List of medical conditions to search
        :param max_results: Maximum results per condition
        :param recruitment_status: Optional recruitment status filter
        """
        all_trials = []
        
        for condition in conditions:
            self.logger.info(f"Scraping clinical trials for condition: {condition}")
            
            # Search and extract trials for this condition
            condition_trials = self.search_clinical_trials(
                condition, 
                max_results=max_results, 
                recruitment_status=recruitment_status
            )
            
            all_trials.extend(condition_trials)
        
        # Save results in multiple formats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_to_json(all_trials, f'clinical_trials_{timestamp}.json')
        self.save_to_csv(all_trials, f'clinical_trials_{timestamp}.csv')
        
        self.logger.info(f"Total trials scraped: {len(all_trials)}")
        return all_trials

def main():
    # Example usage
    scraper = ClinicalTrialsScraper()
    
    # Search multiple conditions
    conditions = [
        "breast cancer", 
        "diabetes", 
        "alzheimer's disease"
    ]
    
    # Run comprehensive scrape
    scraper.run_comprehensive_scrape(
        conditions, 
        max_results=50, 
        recruitment_status='Recruiting'
    )

if __name__ == "__main__":
    main()

# Dependencies:
# requests
# beautifulsoup4
# pandas

# Ethical Scraping Guidelines:
# 1. Respect ClinicalTrials.gov terms of service
# 2. Use official API when possible
# 3. Implement responsible scraping practices
# 4. Do not overload servers
# 5. Verify legal and ethical implications
