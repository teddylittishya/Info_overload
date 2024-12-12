import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class NIHScraper:
    def __init__(self):
        self.base_url = "https://www.nih.gov"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

    def scrape_disease_research(self):
        """
        Scrape disease research and prevalence data
        """
        url = f"{self.base_url}/health-information/scientific-research"
        
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            research_sections = soup.find_all('div', class_='research-panel')
            
            disease_research = []
            for section in research_sections:
                disease_name = section.find('h3').text
                research_details = section.find('div', class_='research-details')
                
                disease_research.append({
                    'disease': disease_name,
                    'research_summary': research_details.text if research_details else 'N/A'
                })
            
            # Save the data as CSV
            df = pd.DataFrame(disease_research)
            df.to_csv('nih_disease_research.csv', index=False)
            print("Data saved as 'nih_disease_research.csv'")
            
            return df
        
        except Exception as e:
            print(f"NIH scraping error: {e}")
            return None

    def selenium_advanced_scrape(self):
        """
        Advanced Selenium-based scraping for dynamic content
        """
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        
        try:
            driver.get(f"{self.base_url}/research/clinical-trials")
            time.sleep(5)  # Wait for dynamic content
            
            trial_elements = driver.find_elements(By.CLASS_NAME, 'clinical-trial')
            
            clinical_trials = []
            for element in trial_elements:
                disease_name = element.find_element(By.CLASS_NAME, 'trial-disease').text
                trial_status = element.find_element(By.CLASS_NAME, 'trial-status').text
                
                clinical_trials.append({
                    'disease': disease_name,
                    'trial_status': trial_status
                })
            
            # Save the clinical trials data as CSV
            df = pd.DataFrame(clinical_trials)
            df.to_csv('nih_clinical_trials.csv', index=False)
            print("Clinical trials data saved as 'nih_clinical_trials.csv'")
            
            return df
        
        except Exception as e:
            print(f"Selenium NIH scraping error: {e}")
            return None
        finally:
            driver.quit()

# Usage
nih_scraper = NIHScraper()
nih_data = nih_scraper.scrape_disease_research()
print(nih_data)
