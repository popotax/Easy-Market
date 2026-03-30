"""
Base class for all marketplace scrapers.
Provides common functionality like HTTP requests, error handling, and data validation.
"""

from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers.
    
    Subclasses should implement:
    - parse_listing(): Extract individual account data
    - extract_listings(): Find all account listings on page
    """
    
    def __init__(
        self,
        name: str,
        base_url: str,
        request_timeout: int = 10,
        request_delay: float = 2,
        max_retries: int = 3,
        user_agent: str = None
    ):
        """
        Initialize scraper.
        
        Args:
            name: Marketplace name
            base_url: Base URL to scrape
            request_timeout: Timeout for HTTP requests (seconds)
            request_delay: Delay between requests (seconds)
            max_retries: Maximum retry attempts
            user_agent: Custom user agent string
        """
        self.name = name
        self.base_url = base_url
        self.request_timeout = request_timeout
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_page_with_browser(self, url: str, wait_seconds: int = 8) -> Optional[str]:
        """Fetch page HTML using a headless browser as a fallback for JS-heavy pages."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.support.ui import WebDriverWait
        except Exception as exc:
            logger.warning(f"Selenium fallback unavailable: {exc}")
            return None

        driver = None
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={self.user_agent}")

            driver = webdriver.Chrome(options=options, service=Service())
            driver.get(url)
            WebDriverWait(driver, wait_seconds).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(min(wait_seconds, 5))
            html = driver.page_source
            logger.info(f"✓ Browser fetched {url}")
            return html
        except Exception as exc:
            logger.warning(f"Browser fetch failed for {url}: {exc}")
            return None
        finally:
            if driver is not None:
                driver.quit()
        
    def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch a web page with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            HTML content of the page, or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.request_timeout,
                    **kwargs
                )
                response.raise_for_status()
                logger.info(f"✓ Fetched {url} (attempt {attempt + 1})")
                time.sleep(self.request_delay)
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"✗ Attempt {attempt + 1} failed for {url}: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"✗ Failed to fetch {url} after {self.max_retries} attempts")
                    return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    @abstractmethod
    def extract_listings(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract all account listings from a BeautifulSoup object.
        
        Must be implemented by subclasses.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of raw listing dictionaries
        """
        pass
    
    @abstractmethod
    def parse_listing(self, listing: Dict) -> Optional[Dict]:
        """
        Parse a single listing into normalized format.
        
        Must be implemented by subclasses.
        
        Args:
            listing: Raw listing data
            
        Returns:
            Normalized account data dict, or None if parse failed
        """
        pass
    
    def validate_data(self, data: Dict) -> bool:
        """
        Validate extracted account data.
        
        Args:
            data: Account data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = [
            'price_original_currency',
            'currency',
            'num_brawlers',
            'total_trophies'
        ]
        
        # Check all required fields exist
        if not all(field in data for field in required_fields):
            return False
        
        # Validate data types and ranges
        try:
            price = float(str(data['price_original_currency']).replace(',', '.'))
            if price <= 0 or price > 10000:
                return False
                
            num_brawlers = int(data['num_brawlers'])
            if num_brawlers < 1 or num_brawlers > 120:
                return False
                
            total_trophies = int(data['total_trophies'])
            if total_trophies < 100 or total_trophies > 1000000:
                return False
                
        except (ValueError, TypeError):
            return False
        
        return True
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method.
        
        Returns:
            List of validated account data dictionaries
        """
        logger.info(f"Starting scrape of {self.name}...")
        
        # Fetch main page
        html = self.fetch_page(self.base_url)
        if not html:
            logger.error(f"Failed to fetch base URL: {self.base_url}")
            return []
        
        # Parse HTML
        soup = self.parse_html(html)
        
        # Extract all listings
        raw_listings = self.extract_listings(soup)
        logger.info(f"Found {len(raw_listings)} listings on {self.name}")
        
        # Parse individual listings
        parsed_accounts = []
        for i, listing in enumerate(raw_listings, 1):
            try:
                account_data = self.parse_listing(listing)
                
                if account_data and self.validate_data(account_data):
                    # Add metadata
                    account_data['site_source'] = self.name
                    account_data['date_scraped'] = datetime.now().isoformat()
                    parsed_accounts.append(account_data)
                else:
                    logger.debug(f"Skipped invalid listing {i} from {self.name}")
                    
            except Exception as e:
                logger.debug(f"Error parsing listing {i} from {self.name}: {e}")
                continue
        
        logger.info(f"✓ Successfully parsed {len(parsed_accounts)} accounts from {self.name}")
        return parsed_accounts
