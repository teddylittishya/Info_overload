import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class CDCScraper:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        
        # Configure Chrome options for headless browsing
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in background
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.base_url = "https://www.cdc.gov"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_disease_data(self):
        """
        Scrape disease prevalence data from CDC using multiple methods
        """
        # Try Selenium scraping first
        selenium_data = self.selenium_advanced_scrape()
        
        if selenium_data is not None and not selenium_data.empty:
            logging.info("Successfully scraped data using Selenium")
            return selenium_data
        
        # Fallback to requests-based scraping
        try:
            url = f"{self.base_url}/diseases/index.html"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find disease tables or sections
            disease_sections = soup.find_all('div', class_='disease-item')
            
            diseases = []
            for section in disease_sections:
                try:
                    disease_name = section.find('h3')
                    disease_description = section.find('p')
                    
                    if disease_name and disease_description:
                        diseases.append({
                            'name': disease_name.text.strip(),
                            'description': disease_description.text.strip()
                        })
                except Exception as e:
                    logging.warning(f"Error parsing individual disease: {e}")
            
            # Convert to DataFrame
            df = pd.DataFrame(diseases)
            
            # Export to CSV
            self.export_to_csv(df)
            
            return df
        
        except Exception as e:
            logging.error(f"Error scraping CDC: {e}")
            return pd.DataFrame()

    def selenium_advanced_scrape(self):
        """
        Advanced scraping using Selenium for dynamic content
        """
        try:
            # Setup WebDriver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.chrome_options
            )
            
            # Navigate to page
            driver.get(f"{self.base_url}/diseases/index.html")
            time.sleep(5)  # Wait for dynamic content
            
            # Find disease elements
            disease_elements = driver.find_elements(By.CLASS_NAME, 'disease-item')
            
            diseases = []
            for element in disease_elements:
                try:
                    name = element.find_element(By.TAG_NAME, 'h3').text
                    details = element.find_element(By.TAG_NAME, 'p').text
                    
                    diseases.append({
                        'name': name,
                        'description': details
                    })
                except Exception as e:
                    logging.warning(f"Error extracting disease details: {e}")
            
            # Convert to DataFrame
            df = pd.DataFrame(diseases)
            
            # Export to CSV
            self.export_to_csv(df)
            
            return df
        
        except Exception as e:
            logging.error(f"Selenium scraping error: {e}")
            return pd.DataFrame()
        
        finally:
            # Ensure driver is closed
            if 'driver' in locals():
                driver.quit()

    def export_to_csv(self, df, filename='cdc_disease_data.csv'):
        """
        Export DataFrame to CSV
        """
        try:
            df.to_csv(filename, index=False)
            logging.info(f"Data exported successfully to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")

def main():
    # Create scraper instance
    cdc_scraper = CDCScraper()
    
    # Scrape data
    disease_data = cdc_scraper.scrape_disease_data()
    
    # Display results
    print("Scraped Disease Data:")
    print(disease_data)
    
    # Automatically exported to CSV via the scraper method

if __name__ == "__main__":
    main()